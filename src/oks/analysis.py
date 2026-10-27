"""Statistilise analüüsi käivitaja: kõik kihid -> tulemustabelid (Parquet/CSV)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import polars as pl

from . import baas, catalog, config, fetch, mixing, pipeline, stats

log = logging.getLogger(__name__)


def load_context() -> tuple[pl.DataFrame, pl.DataFrame, stats.Units]:
    """Laadi klassitabelid ja koosta ühikud."""
    classes = pl.read_parquet(config.DERIVED / "klassid.parquet")
    used = pl.read_parquet(config.DERIVED / "klassid_kasutusel.parquet")
    return classes, used, stats.make_units(used)


def unit_table(classes: pl.DataFrame, used: pl.DataFrame, u: stats.Units) -> pl.DataFrame:
    """Ühikute tabel (nimi, ülem-ökosüsteem, pindala seisundi kaupa baaskaardi 5 m täisresolutsioonil)."""
    rows: list[dict[str, object]] = []
    area = used.group_by(["okosusteem_kood", "alam_kood", "seisund"]).agg(pl.col("pindala_km2").sum())
    for code in u.eco_codes:
        a = (
            area.filter(pl.col("okosusteem_kood") == code)
            .group_by("seisund")
            .agg(pl.col("pindala_km2").sum())
        )
        d = dict(zip(a["seisund"], a["pindala_km2"], strict=True))
        rows.append(
            {
                "unit_level": "okosusteem",
                "unit_code": int(code),
                "nimi": baas.ECOSYSTEM_NAMES[code],
                "eco_code": int(code),
                **{f"pind_{s}": float(d.get(s, 0.0)) for s in stats.STATES},
            }
        )
    names = classes.group_by("alam_kood").agg(pl.col("tuup").first(), pl.col("okosusteem_kood").first())
    nm = dict(zip(names["alam_kood"], names["tuup"], strict=True))
    for j, code in enumerate(u.alam_codes):
        a = area.filter(pl.col("alam_kood") == code)
        d = dict(zip(a["seisund"], a["pindala_km2"], strict=True))
        rows.append(
            {
                "unit_level": "alam",
                "unit_code": int(code),
                "nimi": nm[code],
                "eco_code": int(u.eco_codes[u.alam_eco[j]]),
                **{f"pind_{s}": float(d.get(s, 0.0)) for s in stats.STATES},
            }
        )
    return pl.DataFrame(rows)


def diagnostics(tbl: pl.DataFrame, u: stats.Units) -> list[dict[str, object]]:
    """η² näitajad ökosüsteemi kaupa: kui palju kihi dispersioonist on klassi tabelväärtus."""
    out: list[dict[str, object]] = []
    n_cls = u.cls_eco.size
    ident = np.arange(n_cls, dtype=np.int64)
    for ei, code in enumerate(u.eco_codes):
        in_eco = u.cls_eco == ei
        det = np.where(in_eco, ident, -1)
        alam = np.where(in_eco & (u.cls_alam >= 0), u.cls_alam.astype(np.int64), -1)
        state = np.where(in_eco & (u.cls_alam >= 0), u.cls_state.astype(np.int64), -1)
        within_alam = np.where(in_eco & (u.cls_alam >= 0), u.cls_alam.astype(np.int64), -1)
        out.append(
            {
                "eco_code": int(code),
                "eta2_det": stats.eta_squared(tbl, det),
                "eta2_alam": stats.eta_squared(tbl, alam),
                "eta2_state_in_alam": stats.eta_squared(tbl, state, within_alam),
            }
        )
    return out


def _cached_composition(
    baas_det: Path, lut: np.ndarray, u: stats.Units, x0: float, y0: float, res: int, shape: tuple[int, int]
) -> np.ndarray:
    """Baaskaardi koosseis ruudustikul (vahemälus ``data/derived``; arvutus võtab ~2,5 min)."""
    path = config.DERIVED / f"koosseis_{res}m_{shape[0]}x{shape[1]}_{round(x0)}_{round(y0)}.npy"
    if path.exists():
        return np.load(path)
    comp = mixing.composition(baas_det, lut, u.cls_eco, u.cls_state, x0, y0, float(res), shape)
    np.save(path, comp)
    return comp


def _coarse_inputs(
    layer_id: str, rel: str, classes: pl.DataFrame, u: stats.Units
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Jämeda ruudustiku sisend: ``(y, koosseis, ruutude e_km/n_km, märkus)``.

    Rastri puhul loetakse kogu kiht ja koosseis arvutatakse baaskaardilt; ``lamm_grd1000...`` puhul on
    ruudustik 1 km INSPIRE-ruudustik ja väärtus on väli ``lammide_taastamise_kulu`` (>= 0).
    """
    import pyogrio
    import pyogrio.raw
    import rasterio

    lut, _ = baas.class_lut(classes)
    baas_det = fetch.download(config.BAAS_DET, config.CACHE / config.BAAS_DET)
    if rel.endswith(".tif"):
        src = fetch.download(rel, config.CACHE / rel)
        with rasterio.open(src) as ds:
            t = ds.transform
            arr = ds.read(1).astype(np.float64)
            mask = ds.read_masks(1) > 0
            shape, x0, y0, res = arr.shape, t.c, t.f, t.a
        y = np.where(mask & np.isfinite(arr), arr, np.nan).ravel()
        comp = _cached_composition(baas_det, lut, u, x0, y0, round(res), shape).reshape(-1, mixing.N_COLS)
        cols = np.tile(np.arange(shape[1]), shape[0])
        rows = np.repeat(np.arange(shape[0]), shape[1])
        e_km = np.floor((x0 + (cols + 0.5) * res) / 1000).astype(np.int64)
        n_km = np.floor((y0 - (rows + 0.5) * res) / 1000).astype(np.int64)
        return y, comp, np.stack([e_km, n_km], 1), f"{res:.0f} m ruudustik, segumudel"
    gpkg = config.CACHE / "vektor" / rel
    if not gpkg.exists():
        fetch.download(rel, gpkg)
    meta, _f, _g, fd = pyogrio.raw.read(gpkg, read_geometry=False)
    fields = dict(zip(meta["fields"], fd, strict=True))
    gid = np.asarray(fields["grd_inspir"]).astype(str)
    n_km = np.array([int(g.split("N")[1][:4]) for g in gid])  # '1kmN6465E0369' -> 6465
    e_km = np.array([int(g.split("E")[1][:4]) for g in gid])  # -> 369
    val = np.asarray(fields["lammide_taastamise_kulu"], dtype=np.float64)
    y = np.where(np.isfinite(val) & (val >= 0), val, np.nan)
    shape = (stats.N_MAX - stats.N_MIN, stats.E_MAX - stats.E_MIN)
    comp_grid = _cached_composition(baas_det, lut, u, stats.E_MIN * 1000.0, stats.N_MAX * 1000.0, 1000, shape)
    r = np.clip(stats.N_MAX - 1 - n_km, 0, shape[0] - 1)
    c = np.clip(e_km - stats.E_MIN, 0, shape[1] - 1)
    return y, comp_grid[r, c], np.stack([e_km, n_km], 1), "1 km ruudustik, segumudel"


def run_mixing(
    params: stats.Params, W: np.ndarray, classes: pl.DataFrame, u: stats.Units, cat: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Segumudel jämedatele ruudustikele (930 m rastrid, ``lamm_grd1000...``)."""
    sel = catalog.evaluated(cat).filter(
        ((pl.col("tyyp") == "raster") & (pl.col("spatial_resolution") > 10))
        | (pl.col("id") == "lamm_grd1000_am_drained_2022")
    )
    pairs, cells, notes = [], [], []
    for r in sel.iter_rows(named=True):
        t0 = time.time()
        y, comp, ek, note = _coarse_inputs(r["id"], r["fail"], classes, u)
        cl, ncl = stats.cluster_index(ek[:, 0], ek[:, 1], params.cluster_blocks)
        res = mixing.fit_mixing(y, comp, cl, ncl, W)
        pt = mixing.pair_table(res, u.eco_codes, r["id"])
        pairs.append(pt)
        for ei, code in enumerate(u.eco_codes):
            for s in range(3):
                k = ei * 3 + s
                if np.isfinite(res["beta"][k]):
                    cells.append(
                        {
                            "layer_id": r["id"],
                            "unit_level": "okosusteem",
                            "unit_code": int(code),
                            "state": stats.STATES[s],
                            "n": int(res["cells_ok"][k]),
                            "mean": res["beta"][k],
                            "sd": None,
                            "blocks": int(res["cells_ok"][k]),
                            "q05": None,
                            "q25": None,
                            "q50": None,
                            "q75": None,
                            "q95": None,
                        }
                    )
        notes.append(
            {"id": r["id"], "meetod": "segumudel (uuriv)", "markus": note, "ruute": int(np.isfinite(y).sum())}
        )
        log.info("%s: segumudel %.1f s, %d ruutu", r["id"], time.time() - t0, int(np.isfinite(y).sum()))
    pt = pl.concat(pairs) if pairs else pl.DataFrame()
    if not pt.is_empty():
        pt = pt.with_columns(
            ((pl.col("cells_a") >= 30) & (pl.col("cells_b") >= 30)).alias("enough_m"),
            pl.lit(None, dtype=pl.Float64).alias("delta_u"),
            pl.lit(False).alias("enough_u"),
        ).with_columns(pl.when(pl.col("enough_m")).then(pl.col("p_m")).otherwise(None).alias("p_m"))
    return pt, pl.DataFrame(cells), pl.DataFrame(notes)


def distributions(
    u: stats.Units, ids: list[str], blocks_dir: Path | None = None
) -> tuple[pl.DataFrame, dict[str, dict[str, object]]]:
    """Liida klasside histogrammid ökosüsteemi/alamökosüsteemi ja seisundi tasemele.

    Parameters
    ----------
    u
        Ühikud (``stats.make_units``).
    ids
        Kihtide id-d; kasutatakse neid, millel on histogrammi failid (``pipeline.write_hist``).
    blocks_dir
        Histogrammide kaust (vaikimisi ``config.BLOCKS``).

    Returns
    -------
    tuple[pl.DataFrame, dict[str, dict[str, object]]]
        Pikk tabel ``layer_id, unit_level, unit_code, state, bin, n`` (``bin == n_bins`` on täpsete
        nullide arv) ja vahemike kirjeldused kihi kaupa.
    """
    bdir = blocks_dir or config.BLOCKS
    n_cls = u.cls_eco.size
    frames: list[pl.DataFrame] = []
    specs: dict[str, dict[str, object]] = {}
    for lid in ids:
        pq, js = bdir / f"{lid}__hist.parquet", bdir / f"{lid}__hist.json"
        if not (pq.exists() and js.exists()):
            continue
        specs[lid] = json.loads(js.read_text(encoding="utf-8"))
        h = pl.read_parquet(pq).filter(pl.col("cls") < n_cls)
        cls = h["cls"].to_numpy().astype(np.int64)
        base = pl.DataFrame(
            {
                "bin": h["bin"].cast(pl.Int64),
                "n": h["n"].cast(pl.Int64),
                "state": u.cls_state[cls].astype(np.int64),
                "eco": u.cls_eco[cls].astype(np.int64),
                "alam": u.cls_alam[cls].astype(np.int64),
            }
        ).filter(pl.col("state") >= 0)
        eco_map = dict(enumerate(u.eco_codes))
        alam_map = dict(enumerate(u.alam_codes))
        eco_part = (
            base.group_by(["eco", "state", "bin"])
            .agg(pl.col("n").sum())
            .with_columns(
                pl.lit("okosusteem").alias("unit_level"),
                pl.col("eco").replace_strict(eco_map, return_dtype=pl.Int64).alias("unit_code"),
            )
            .drop("eco")
        )
        alam_part = (
            base.filter(pl.col("alam") >= 0)
            .group_by(["alam", "state", "bin"])
            .agg(pl.col("n").sum())
            .with_columns(
                pl.lit("alam").alias("unit_level"),
                pl.col("alam").replace_strict(alam_map, return_dtype=pl.Int64).alias("unit_code"),
            )
            .drop("alam")
        )
        part = pl.concat([eco_part, alam_part], how="diagonal_relaxed").with_columns(
            pl.lit(lid).alias("layer_id"),
            pl.col("state").replace_strict(dict(enumerate(stats.STATES)), return_dtype=pl.String),
        )
        frames.append(part.select("layer_id", "unit_level", "unit_code", "state", "bin", "n"))
    return (pl.concat(frames) if frames else pl.DataFrame()), specs


def check_distributions(
    dist: pl.DataFrame, specs: dict[str, dict[str, object]], cells: pl.DataFrame
) -> pl.DataFrame:
    """Kontrolli, et jaotuse pikslite arv (ilma nullide lisaveeruta) võrdub plokitabeli arvuga.

    Returns
    -------
    pl.DataFrame
        Kõik lahknevad (kiht, üksus, seisund) read; tühi tabel tähendab täielikku kooskõla.
    """
    if dist.is_empty():
        return pl.DataFrame()
    nb = {k: int(v["n_bins"]) for k, v in specs.items()}  # type: ignore[call-overload]
    d = dist.with_columns(pl.col("layer_id").replace_strict(nb, return_dtype=pl.Int64).alias("_nb")).filter(
        pl.col("bin") < pl.col("_nb")
    )
    tot = d.group_by(["layer_id", "unit_level", "unit_code", "state"]).agg(pl.col("n").sum().alias("n_hist"))
    j = tot.join(
        cells.select(
            "layer_id", "unit_level", "unit_code", "state", pl.col("n").cast(pl.Int64).alias("n_block")
        ),
        on=["layer_id", "unit_level", "unit_code", "state"],
        how="left",
    )
    return j.filter(pl.col("n_block").is_null() | (pl.col("n_hist") != pl.col("n_block")))


def res_effective(spatial_resolution: float | None) -> float:
    """Arvutuse lahutusvõime (m): madalama lahutusvõimega kihid on viidud 10 m lahutusvõimele, vektorid 10 m."""
    if spatial_resolution is None or spatial_resolution > pipeline.MAX_RES_M:
        return 10.0
    return float(spatial_resolution)


def _join_median(out: dict[str, pl.DataFrame], med: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    """Liida mediaanipõhised veerud (``stats.analyse_layer_median``) keskmisepõhistele tabelitele."""
    keys = {"paarid": ["unit_level", "unit_code", "pair"], "lahtrid": ["unit_level", "unit_code", "state"]}
    res = dict(out)
    for k, on in keys.items():
        if not out[k].is_empty() and not med[k].is_empty():
            res[k] = out[k].join(med[k], on=on, how="left")
    if not out["klassid"].is_empty() and not med["klassid"].is_empty():
        res["klassid"] = out["klassid"].join(
            med["klassid"].with_columns(pl.col("cls").cast(out["klassid"]["cls"].dtype)), on="cls", how="left"
        )
    res["algklassid"] = med["algklassid"]
    return res


def run(
    params: stats.Params | None = None,
    only: set[str] | None = None,
    out_dir: Path | None = None,
    unpaired_median_boot: bool = True,
) -> dict[str, pl.DataFrame]:
    """Analüüsi kõik plokitabelid ja kirjuta tulemused.

    Parameters
    ----------
    params
        Parameetrid (vaikimisi ``stats.Params()``).
    only
        Kui antud, ainult need kihi id-d.
    out_dir
        Väljundkaust (vaikimisi ``data/tulemused``).
    unpaired_median_boot
        Kas arvutada paaritamata mediaanide vahe bootstrap (tundlikkuse variantides ei kasutata).
    """
    params = params or stats.Params()
    out_dir = out_dir or config.RESULTS
    out_dir.mkdir(parents=True, exist_ok=True)
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    ev = catalog.evaluated(cat).filter(pl.col("tyyp").is_in(["raster", "vektor"]))
    classes, used, u = load_context()
    unit_table(classes, used, u).write_parquet(out_dir / "uhikud.parquet")
    n_cl = stats.cluster_index(np.array([stats.E_MIN]), np.array([stats.N_MIN]), params.cluster_blocks)[1]
    W = stats._boot_weights(n_cl, params.n_boot, params.seed)
    pairs: list[pl.DataFrame] = []
    cells: list[pl.DataFrame] = []
    cls_tabs: list[pl.DataFrame] = []
    alg_tabs: list[pl.DataFrame] = []
    diag: list[dict[str, object]] = []
    for r in ev.iter_rows(named=True):
        path = config.BLOCKS / f"{r['id']}.parquet"
        if not path.exists() or (only and r["id"] not in only):
            continue
        t0 = time.time()
        tbl = pl.read_parquet(path)
        res_m = res_effective(r["spatial_resolution"])
        out = stats.analyse_layer(tbl, u, res_m, params, W)
        vdir, bpath = pipeline.val_path(r["id"]), pipeline.blkmed_path(r["id"])
        if vdir.is_dir() and bpath.exists() and not tbl.is_empty():
            med = stats.analyse_layer_median(
                pl.read_parquet(bpath), vdir, u, used, res_m, params, W, unpaired_median_boot
            )
            out = _join_median(out, med)
            if not out["algklassid"].is_empty():
                alg_tabs.append(out["algklassid"].with_columns(pl.lit(r["id"]).alias("layer_id")))
        else:
            log.warning("%s: mediaanide sisend puudub (aggregeeri uuesti)", r["id"])
        for key, lst in (("paarid", pairs), ("lahtrid", cells), ("klassid", cls_tabs)):
            if not out[key].is_empty():
                lst.append(
                    out[key].with_columns(pl.lit(r["id"]).alias("layer_id"), pl.lit(res_m).alias("res_m"))
                )
        for d in diagnostics(tbl, u):
            diag.append({"layer_id": r["id"], **d})
        log.info("%s: %.1f s, %d paari", r["id"], time.time() - t0, out["paarid"].height)

    def _note(r: dict[str, object]) -> str:
        res = r["spatial_resolution"]
        if r["tyyp"] == "raster" and isinstance(res, int | float) and res > pipeline.MAX_RES_M:
            return f"Madalama lahutusvõimega kiht ({res:.0f} m). Arvutuseks viidud baaskaardi 10 m lahutusvõimele; seisundite erinevus tuleb ainult {res:.0f} m ruutude vahelistest erinevustest."
        if r["id"] == "lamm_grd1000_am_drained_2022":
            return "Madalama lahutusvõimega kiht (1 km). Arvutuseks viidud baaskaardi 10 m lahutusvõimele; seisundite erinevus tuleb ainult 1 km ruutude vahelistest erinevustest."
        return ""

    notes = [
        {
            "id": r["id"],
            "meetod": "paaritatud (plokk × alamökosüsteem)"
            if r["tyyp"] == "raster"
            else "paaritatud (vektor rasteriseeritud 10 m)",
            "markus": _note(r),
        }
        for r in ev.iter_rows(named=True)
        if (config.BLOCKS / f"{r['id']}.parquet").exists() and (not only or r["id"] in only)
    ]
    # segumudel (keskmisepõhine, uuriv) jääb võrdluseks eraldi failidesse
    mixed: dict[str, pl.DataFrame] = {}
    if not only or any(i in only for i in ("lamm_grd1000_am_drained_2022",)):
        mp, mc, mn = run_mixing(params, W, classes, u, cat)
        if not mp.is_empty():
            mixed = {"paarid_segumudel": add_fdr(mp, params.alpha), "lahtrid_segumudel": mc}
            notes.extend(mn.select("id", "meetod", "markus").to_dicts())
    pl.DataFrame(notes).write_csv(out_dir / "teenused_lisa.csv")
    res = {
        "paarid": pl.concat(pairs, how="diagonal_relaxed") if pairs else pl.DataFrame(),
        "lahtrid": pl.concat(cells, how="diagonal_relaxed") if cells else pl.DataFrame(),
        "klassid": pl.concat(cls_tabs, how="diagonal_relaxed") if cls_tabs else pl.DataFrame(),
        "algklassid": pl.concat(alg_tabs, how="diagonal_relaxed") if alg_tabs else pl.DataFrame(),
        "diagnostika": pl.DataFrame(diag),
        **mixed,
    }
    dist, dspecs = distributions(u, [r["id"] for r in ev.iter_rows(named=True)])
    if not dist.is_empty():
        bad = check_distributions(dist, dspecs, res["lahtrid"])
        if not bad.is_empty():
            log.warning("jaotus ei ühti plokitabeliga %d real, nt %s", bad.height, bad.head(3).to_dicts())
        res["jaotused"] = dist
        (out_dir / "jaotuse_vahemikud.json").write_text(
            json.dumps(dspecs, ensure_ascii=False), encoding="utf-8"
        )
    if not res["paarid"].is_empty():
        res["paarid"] = add_fdr(res["paarid"], params.alpha)
    for k, v in res.items():
        if not v.is_empty():
            v.write_parquet(out_dir / f"{k}.parquet")
    pl.DataFrame([{k: v for k, v in params.__dict__.items()}]).write_csv(out_dir / "parameetrid.csv")
    return res


#: FDR-perekonnad: (p-väärtus, q-väärtus); ``_med`` = mediaanipõhine (metoodika v2).
_FDR = (
    ("p_m", "q_m"),
    ("p_u", "q_u"),
    ("wilcoxon_p", "q_wilcoxon"),
    ("p_m_med", "q_m_med"),
    ("p_u_med", "q_u_med"),
    ("wilcoxon_p_med", "q_wilcoxon_med"),
)


def add_fdr(paarid: pl.DataFrame, alpha: float) -> pl.DataFrame:
    """Lisa FDR-korrigeeritud q-väärtused (perekond = unit_level) ja olulisuse lipud (keskmise ja mediaani kohta)."""
    parts = []
    for col in ("p_u", "wilcoxon_p", "p_m"):
        if col not in paarid.columns:
            paarid = paarid.with_columns(pl.lit(None, dtype=pl.Float64).alias(col))
    fam = [(pc, qc) for pc, qc in _FDR if pc in paarid.columns]
    for level in ("okosusteem", "alam"):
        d = paarid.filter(pl.col("unit_level") == level)
        if d.is_empty():
            continue
        parts.append(
            d.with_columns(pl.Series(qc, stats.bh_fdr(d[pc].to_numpy().astype(np.float64))) for pc, qc in fam)
        )
    out = pl.concat(parts, how="diagonal_relaxed")
    out = out.with_columns(
        (pl.col("q_m") < alpha).fill_null(False).alias("oluline_m"),
        (pl.col("q_u") < alpha).fill_null(False).alias("oluline_u"),
    ).with_columns(
        (
            pl.col("oluline_m") & pl.col("oluline_u") & (pl.col("delta_m").sign() == pl.col("delta_u").sign())
        ).alias("kooskolas")
    )
    if "q_m_med" in out.columns:
        out = out.with_columns(
            (pl.col("q_m_med") < alpha).fill_null(False).alias("oluline_m_med"),
            (pl.col("q_u_med") < alpha).fill_null(False).alias("oluline_u_med"),
        ).with_columns(
            (
                pl.col("oluline_m_med")
                & pl.col("oluline_u_med")
                & (pl.col("delta_m_med").sign() == pl.col("delta_u_med").sign())
            ).alias("kooskolas_med")
        )
    return out


#: Tundlikkuse variandid: klastri suurus, minimaalne ala ja juhuslik seeme.
VARIANTS: dict[str, dict[str, object]] = {
    "klaster5km": {"cluster_blocks": 5},
    "klaster20km": {"cluster_blocks": 20},
    "ala_0_25ha": {"min_area_ha": 0.25},
    "ala_4ha": {"min_area_ha": 4.0},
    "seeme_2": {"seed": 2},
}

_KEYS = ["layer_id", "unit_level", "unit_code", "pair"]


def sensitivity(
    base: stats.Params, base_pairs: pl.DataFrame, variants: dict[str, dict[str, object]] | None = None
) -> pl.DataFrame:
    """Käivita analüüs variantparameetritega ja võrdle põhijooksuga.

    Parameters
    ----------
    base
        Põhijooksu parameetrid.
    base_pairs
        Põhijooksu ``paarid`` (``run`` tulemus).
    variants
        ``{nimi: {parameeter: väärtus}}``; vaikimisi ``VARIANTS``.

    Returns
    -------
    pl.DataFrame
        Iga variandi ja taseme kohta: võrreldavate hinnangute arv, põhijooksu oluliste hulgast
        säilinud olulised (sama märgiga), uued olulised ja Δ astakkorrelatsioon.
    """
    variants = variants or VARIANTS
    rows: list[dict[str, object]] = []
    # metoodika v2: põhihinnang on mediaanipõhine paaritatud Δ (kui olemas)
    d_col, s_col = (
        ("delta_m_med", "oluline_m_med") if "delta_m_med" in base_pairs.columns else ("delta_m", "oluline_m")
    )
    b = base_pairs.select(
        *_KEYS, pl.col(d_col).alias("d0"), pl.col(s_col).alias("s0"), pl.col("enough_m").alias("e0")
    )
    for name, over in variants.items():
        res = run(
            replace(base, **over),  # type: ignore[arg-type]
            None,
            config.RESULTS / f"tundlikkus_{name}",
            unpaired_median_boot=False,
        )
        v = res["paarid"].select(
            *_KEYS,
            pl.col(d_col).alias("d1"),
            pl.col(s_col).alias("s1"),
            pl.col("enough_m").alias("e1"),
        )
        j = b.join(v, on=_KEYS, how="inner")
        for level in ("okosusteem", "alam"):
            jl = j.filter(pl.col("unit_level") == level)
            both = jl.filter(pl.col("e0") & pl.col("e1"))
            sig0 = both.filter(pl.col("s0"))
            kept = sig0.filter(pl.col("s1") & (pl.col("d0").sign() == pl.col("d1").sign()))
            new = both.filter(~pl.col("s0") & pl.col("s1"))
            rho = both.select(pl.corr("d0", "d1", method="spearman")).item() if both.height > 2 else None
            rows.append(
                {
                    "variant": name,
                    "unit_level": level,
                    "voordluses": both.height,
                    "pohijooksu_olulisi": sig0.height,
                    "sailinud_olulised": kept.height,
                    "sailinud_osa": kept.height / sig0.height if sig0.height else None,
                    "uusi_olulisi": new.height,
                    "spearman_delta": rho,
                    "ei_piisa_variandis": jl.filter(pl.col("e0") & ~pl.col("e1")).height,
                }
            )
    return pl.DataFrame(rows)
