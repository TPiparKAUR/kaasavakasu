"""Raster-teenuste töötlusliin: allalaadimine -> plokkidesse agregeerimine -> toorfaili kustutamine."""

from __future__ import annotations

import json
import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from numpy.typing import NDArray
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

from . import aggregate, baas, catalog, config, fetch, hist

log = logging.getLogger(__name__)

#: Rastrid, mille lahutusvõime on madalam kui see (m), viiakse enne aggregeerimist 10 m lahutusvõimele.
MAX_RES_M = 10
#: Vektorite rasterdamise NoData (polügoonist väljas); metoodika v2: kehtiv null.
VECTOR_NODATA = -9999.0


def _load_lut() -> tuple[NDArray[np.int16], int]:
    used = pl.read_parquet(config.DERIVED / "klassid_kasutusel.parquet")
    classes = pl.read_parquet(config.DERIVED / "klassid.parquet")
    lut, _ = baas.class_lut(classes)
    return lut, used.height


def cls_path(layer_id: str) -> Path:
    """Klassitabel (kõik baaskaardi klassid): ``{id}__cls.parquet``."""
    return config.BLOCKS / f"{layer_id}__cls.parquet"


def write_cls(layer_id: str, stats: np.ndarray, all_classes: pl.DataFrame) -> None:
    """Kirjuta klassitabel: ``kood`` + ``aggregate.CLS_STATS`` veerud (ainult klassid, millel on pikslid)."""
    df = pl.DataFrame(
        {"kood": all_classes["kood"], **{c: stats[:, i] for i, c in enumerate(aggregate.CLS_STATS)}}
    ).filter(pl.col("n_total") > 0)
    df.with_columns(pl.col(c).cast(pl.Int64) for c in aggregate.CLS_STATS[:5]).write_parquet(
        cls_path(layer_id), compression="zstd"
    )


def val_path(layer_id: str) -> Path:
    """Kadudeta sagedustabeli kaust (``aggregate.value_counts``, üks fail ploki-rea kohta): ``{id}__val``."""
    return config.BLOCKS / f"{layer_id}__val"


def blkmed_path(layer_id: str) -> Path:
    """Plokimediaanide tabel (``aggregate.segment_medians``): ``{id}__blkmed.parquet``."""
    return config.BLOCKS / f"{layer_id}__blkmed.parquet"


def groupings(classes: pl.DataFrame) -> dict[str, NDArray[np.int64]]:
    """Plokimediaanide rühmitused (``kood -> rühm``, ainult seisundiga klassid, ``uld`` 1..3).

    ``alam``: ``alam_kood * 10 + uld`` (paaritatud hinnangu stratum plokis); ``eco``: ``okosusteem_kood * 10 + uld``.
    """
    st = classes.filter(pl.col("uld").is_in([1, 2, 3]))
    out: dict[str, NDArray[np.int64]] = {}
    for name, col in (("alam", "alam_kood"), ("eco", "okosusteem_kood")):
        arr = np.full(65536, -1, dtype=np.int64)
        arr[st["kood"].to_numpy()] = st[col].to_numpy().astype(np.int64) * 10 + st["uld"].to_numpy()
        out[name] = arr
    return out


def hist_paths(layer_id: str) -> tuple[Path, Path]:
    """Jaotuse (histogrammi) failid: loendused (Parquet) ja vahemike kirjeldus (JSON)."""
    return config.BLOCKS / f"{layer_id}__hist.parquet", config.BLOCKS / f"{layer_id}__hist.json"


def write_hist(layer_id: str, spec: hist.HistSpec, counts: np.ndarray) -> None:
    """Kirjuta jaotuse loendused (``cls, bin, n``; ``bin == n_bins`` on täpsete nullide arv) ja vahemikud."""
    pq, js = hist_paths(layer_id)
    cls, b = np.nonzero(counts)
    pl.DataFrame(
        {"cls": cls.astype(np.int16), "bin": b.astype(np.int16), "n": counts[cls, b].astype(np.int64)}
    ).write_parquet(pq, compression="zstd")
    js.write_text(json.dumps(spec.to_dict()), encoding="utf-8")


def _aggregate_with_hist(
    layer_id: str,
    src: Path,
    tif_name: str,
    invalid: tuple[float, ...],
    baas_det: Path,
    lut: NDArray[np.int16],
    n_cls: int,
    zero_values: tuple[float, ...] = (),
) -> pl.DataFrame:
    spec = hist.choose_spec(src, baas_det, lut, invalid, zero_values)
    counts = np.zeros((n_cls, spec.n_bins + 1), dtype=np.int64)
    classes = pl.read_parquet(config.DERIVED / "klassid.parquet")
    lut_all, all_classes = baas.class_lut_all(classes)
    cstats = np.zeros((all_classes.height, aggregate.N_CLS_STATS), dtype=np.float64)
    config.BLOCKS.mkdir(parents=True, exist_ok=True)
    blk: list[pl.DataFrame] = []
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec(layer_id, tif_name, invalid, zero_values),
        src,
        baas_det,
        lut,
        n_cls,
        spec,
        counts,
        lut_all,
        cstats,
        val_dir=val_path(layer_id),
        groupings=groupings(classes),
        blk_med=blk,
    )
    write_hist(layer_id, spec, counts)
    write_cls(layer_id, cstats, all_classes)
    if blk:
        pl.concat(blk).write_parquet(blkmed_path(layer_id), compression="zstd")
    return df


def done(layer_id: str) -> bool:
    """Kas kihi kõik aggregeerimise väljundid on olemas (plokitabel, jaotus, klassitabel, mediaanide sisend)."""
    return (
        (config.BLOCKS / f"{layer_id}.parquet").exists()
        and hist_paths(layer_id)[0].exists()
        and cls_path(layer_id).exists()
        and val_path(layer_id).is_dir()
        and blkmed_path(layer_id).exists()
    )


def resample_to_10m(src: Path, out: Path) -> Path:
    """Vii madalama lahutusvõimega raster (nt 930 m) baaskaardi 10 m lahutusvõimele lähima naabriga.

    Sihtruudustik on sama mis vektorite rasterdamisel (``fields.X0, Y0, RES``; baaskaardi servadega joondatud).
    Väärtusi ei skaleerita: kihid on hektaripõhised (EUR/ha, kg/ha/a), seega jääb tähendus samaks.
    Seisundite erinevus tuleb ainult algsete ruutude vahelistest erinevustest.
    """
    from . import fields  # hilinenud import: shapely vajalik ainult siin

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.tif")
    with rasterio.open(src) as s:
        if s.crs is None or s.crs.to_epsg() != 3301:
            raise ValueError(f"{src.name}: CRS ei ole EPSG:3301 ({s.crs})")
        profile = {
            "driver": "GTiff",
            "height": fields.HEIGHT,
            "width": fields.WIDTH,
            "count": 1,
            "dtype": s.dtypes[0],
            "crs": "EPSG:3301",
            "transform": from_origin(fields.X0, fields.Y0, fields.RES, fields.RES),
            "nodata": s.nodata,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "compress": "deflate",
        }
        with rasterio.open(tmp, "w", **profile) as d:
            reproject(
                source=rasterio.band(s, 1),
                destination=rasterio.band(d, 1),
                resampling=Resampling.nearest,
                src_nodata=s.nodata,
                dst_nodata=s.nodata,
            )
    tmp.replace(out)
    return out


def process_layer(
    layer_id: str,
    rel: str,
    invalid: tuple[float, ...],
    zero_values: tuple[float, ...] = (),
    keep_raw: bool = False,
    resample: bool = False,
) -> dict[str, object]:
    """Töötle üks raster; tagasta manifestirida (ajad, ridade arv, suurus).

    ``resample``: madalama lahutusvõimega raster viiakse enne aggregeerimist 10 m lahutusvõimele.
    """
    out = config.BLOCKS / f"{layer_id}.parquet"
    t0 = time.time()
    lut, n_cls = _load_lut()
    dest = config.CACHE / rel
    fetch.download(rel, dest)
    t1 = time.time()
    baas_det = fetch.download(config.BAAS_DET, config.CACHE / config.BAAS_DET)
    src = resample_to_10m(dest, config.CACHE / "lahutus_10m" / f"{layer_id}.tif") if resample else dest
    df = _aggregate_with_hist(layer_id, src, rel, invalid, baas_det, lut, n_cls, zero_values)
    config.BLOCKS.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out, compression="zstd")
    if not keep_raw:
        dest.unlink(missing_ok=True)
        if resample:
            src.unlink(missing_ok=True)
    t2 = time.time()
    return {
        "id": layer_id,
        "fail": rel,
        "ridu": df.height,
        "pikslid": int(df["n"].cast(pl.Int64).sum()) if df.height else 0,
        "alla_s": round(t1 - t0, 1),
        "agg_s": round(t2 - t1, 1),
        "parquet_b": out.stat().st_size,
    }


def run(workers: int = 3, only: set[str] | None = None, force: bool = False) -> pl.DataFrame:
    """Töötle kõik analüüsitavad rastrid (eval=TRUE).

    Rastrid, mille lahutusvõime on madalam kui ``MAX_RES_M``, viiakse enne 10 m lahutusvõimele (``resample_to_10m``).
    """
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    ev = catalog.evaluated(cat).filter(pl.col("tyyp") == "raster")
    jobs = []
    for r in ev.iter_rows(named=True):
        if only and r["id"] not in only:
            continue
        if not force and done(r["id"]):
            continue
        jobs.append(
            (
                r["id"],
                r["fail"],
                catalog.EXTRA_INVALID.get(r["id"], ()),
                catalog.zero_values(r["id"], r["nodata"]),
                False,
                bool(r["spatial_resolution"] > MAX_RES_M),
            )
        )
    log.info("%d kihti töötlemisel", len(jobs))
    rows: list[dict[str, object]] = []
    # 'spawn': Polars + fork võib ummistuda
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(process_layer, *j): j[0] for j in jobs}
        for f in as_completed(futs):
            try:
                row = f.result()
            except Exception:
                log.exception("kiht %s ebaõnnestus", futs[f])
                continue
            log.info("valmis: %s", row)
            rows.append(row)
    man = pl.DataFrame(rows)
    if man.height:
        path = config.BLOCKS / "_manifest.csv"
        if path.exists():
            man = pl.concat([pl.read_csv(path), man], how="diagonal_relaxed").unique("id", keep="last")
        man.write_csv(path)
    return man


#: Rasteriseeritud põllumassiivide atribuudid: (kihi id, gpkg, väli, tulemuse fail). ``vaartusklass``
#: on ainult diagnostika (võrdlus baaskaardi põllumaa seisundiga) ja ei ole teenuse hinnang.
FIELD_LAYERS: tuple[tuple[str, str, str, str], ...] = (
    ("toiduteenus_2022", "Toit_soot_pollult/toiduteenus_2022.gpkg", "boniteet", "toiduteenus_boniteet.tif"),
    (
        "biotorje_2022",
        "Bioloogiline_torje/biotorje_2022.gpkg",
        "pestits_vahenemine",
        "biotorje_pestits_vahenemine.tif",
    ),
    (
        "toiduteenus_2022__vaartusklass",
        "Toit_soot_pollult/toiduteenus_2022.gpkg",
        "vaartusklass",
        "toiduteenus_vaartusklass.tif",
    ),
    (
        "lamm_grd1000_am_drained_2022",
        "Puhverdavad_teenused/lamm_grd1000_am_drained_2022.gpkg",
        "lammide_taastamise_kulu",
        "lamm_taastamise_kulu.tif",
    ),
)


def run_fields(force: bool = False, only: set[str] | None = None) -> pl.DataFrame:
    """Rasteriseeri ja aggregeeri vektorkihid (``fields``: põllumassiivid, 1 km lammiruudud) samale plokitabelile.

    Metoodika v2: polügoonist väljas (rasterdamise NoData) loetakse nulliks, kui all on baaskaardi kood.
    """
    from . import fields  # hilinenud import: shapely vajalik ainult siin

    lut, n_cls = _load_lut()
    baas_det = fetch.download(config.BAAS_DET, config.CACHE / config.BAAS_DET)
    rows = []
    for lid, gpkg, attr, tif in FIELD_LAYERS:
        if only and lid not in only:
            continue
        out = config.BLOCKS / f"{lid}.parquet"
        if done(lid) and not force:
            continue
        t0 = time.time()
        src = config.DERIVED / "vektor_raster" / tif
        if force or not src.exists():
            mapper = fields.value_class_to_number if attr == "vaartusklass" else None
            fields.rasterize_attribute(fields.cached_gpkg(gpkg), attr, src, mapper, nodata=VECTOR_NODATA)
        df = _aggregate_with_hist(lid, src, tif, (), baas_det, lut, n_cls, (VECTOR_NODATA,))
        config.BLOCKS.mkdir(parents=True, exist_ok=True)
        df.write_parquet(out, compression="zstd")
        rows.append(
            {
                "id": lid,
                "fail": gpkg,
                "ridu": df.height,
                "pikslid": int(df["n"].cast(pl.Int64).sum()),
                "agg_s": round(time.time() - t0, 1),
            }
        )
        log.info("valmis: %s", rows[-1])
    return pl.DataFrame(rows)
