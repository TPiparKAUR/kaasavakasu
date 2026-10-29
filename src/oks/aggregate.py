"""Teenuse raster -> 1 km plokkide tabel ``(plokk, detailne klass)``: n, Σx, Σx².

Iga teenuse raster loetakse ploki-ridade kaupa (mälu on piiratud). Baaskaart
(``OS_det_seisund_det``) taasproovitakse teenuse ruudustikule lähima naabri meetodil,
nii et teenuse väärtusi ei interpoleerita. Ploki kuuluvus määratakse piksli keskpunkti
järgi EPSG:3301 1000 m ruudustikus.
"""

from __future__ import annotations

import logging
import math
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from numpy.typing import NDArray
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window

from . import config
from .hist import HistSpec, bin_index

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LayerSpec:
    """Aggregeeritava rastri kirjeldus."""

    id: str
    rel: str
    invalid: tuple[float, ...] = field(default_factory=tuple)
    zero_values: tuple[float, ...] = field(default_factory=tuple)


#: Veerud klassitabelis ``cls_stats`` (kujuga ``(klasse, N_CLS_STATS)``).
CLS_STATS = ("n_total", "n_valid", "n_zero", "n_pos", "n_neg", "sum", "sumsq")
N_CLS_STATS = len(CLS_STATS)


@dataclass(frozen=True)
class Grid:
    """Teenuse ruudustik (vajadusel laiendatud baaskaardi ulatuseni samas võrgustikus)."""

    transform: Affine
    width: int
    height: int
    crs: CRS


def extended_grid(
    ds: rasterio.DatasetReader, bounds: tuple[float, float, float, float]
) -> tuple[Grid, int, int]:
    """Laienda teenuse ruudustik ``bounds`` (baaskaardi ulatus) katvaks, säilitades algpunkti võrgu ja piksli.

    Ruudustikust väljapoole jäävad baaskaardi pikslid on teenuse NoData (metoodika v2: kehtiv null, kui all
    on baaskaardi kood). Kui ruudustik katab ulatuse, on tulemus sama mis ``ds`` (nihked 0).

    Returns
    -------
    tuple[Grid, int, int]
        Laiendatud ruudustik ja selle esimese veeru/rea nihe teenuse ruudustikus (``<= 0``).
    """
    t = ds.transform
    left, bottom, right, top = bounds
    eps = 1e-6  # ujukoma: nt piksel 10.000000000000002 m
    c0 = min(0, math.floor((left - t.c) / t.a + eps))
    c1 = max(ds.width, math.ceil((right - t.c) / t.a - eps))
    r0 = min(0, math.floor((t.f - top) / -t.e + eps))
    r1 = max(ds.height, math.ceil((t.f - bottom) / -t.e - eps))
    return Grid(t @ Affine.translation(c0, r0), c1 - c0, r1 - r0, ds.crs), c0, r0


def _read_padded(
    ds: rasterio.DatasetReader, grid: Grid, c0: int, r0: int, a: int, b: int
) -> tuple[NDArray[np.generic], NDArray[np.bool_]]:
    """Laiendatud ruudustiku read ``a:b``: väärtused ja GDAL-i mask; väljaspool teenuse rastrit NoData."""
    if c0 == 0 and r0 == 0 and grid.width == ds.width:
        win = Window(0, a, ds.width, b - a)
        return ds.read(1, window=win), ds.read_masks(1, window=win) > 0
    fill = ds.nodata if ds.nodata is not None else 0
    val = np.full((b - a, grid.width), fill, dtype=ds.dtypes[0])
    mask = np.zeros((b - a, grid.width), dtype=bool)
    sa, sb = max(a + r0, 0), min(b + r0, ds.height)
    ca, cb = max(0, -c0), min(grid.width, ds.width - c0)
    if sb > sa and cb > ca:
        win = Window(ca + c0, sa, cb - ca, sb - sa)
        val[sa - r0 - a : sb - r0 - a, ca:cb] = ds.read(1, window=win)
        mask[sa - r0 - a : sb - r0 - a, ca:cb] = ds.read_masks(1, window=win) > 0
    return val, mask


def validity(
    val: NDArray[np.generic],
    mask: NDArray[np.bool_],
    invalid: NDArray[np.float64],
    zero_values: tuple[float, ...],
) -> tuple[NDArray[np.bool_], NDArray[np.generic]]:
    """Kehtivate pikslite mask ja väärtused (``zero_values`` loetakse kehtivaks nulliks).

    Parameters
    ----------
    val
        Rastri väärtused.
    mask
        GDAL-i kehtivuse mask (``read_masks > 0``); NoData väärtuse pikslid on ``False``.
    invalid
        Lisaks välistatavad sentinel-väärtused.
    zero_values
        Väärtused, mis tähendavad „teenust ei ole“ ja loetakse nulliks (ka siis, kui need on NoData).

    Returns
    -------
    tuple[NDArray[np.bool_], NDArray[np.generic]]
        ``ok`` ja väärtused, kus ``zero_values`` on asendatud nulliga.
    """
    ok = mask.copy()
    if val.dtype.kind == "f":
        ok &= np.isfinite(val)
    if invalid.size:
        ok &= ~np.isin(val, invalid.astype(val.dtype))
    if zero_values:
        zero = np.isin(val, np.asarray(zero_values, dtype=val.dtype))
        ok |= zero
        if val.dtype.kind == "f":
            ok &= np.isfinite(val) | zero
        val = np.where(zero, np.zeros((), dtype=val.dtype), val)
    return ok, val


def _row_runs(ds: Grid) -> list[tuple[int, int, int]]:
    """Jaga rastri read 1 km ploki-ridadeks: ``(r0, r1, ploki_rida_n_km)``."""
    t = ds.transform
    cy = t.f + (np.arange(ds.height) + 0.5) * t.e
    brow = np.floor(cy / config.BLOCK_M).astype(np.int64)
    edges = np.flatnonzero(np.diff(brow)) + 1
    starts = np.concatenate(([0], edges))
    ends = np.concatenate((edges, [ds.height]))
    return [(int(a), int(b), int(brow[a])) for a, b in zip(starts, ends, strict=True)]


def _baas_chunk(
    baas: rasterio.DatasetReader, ds: Grid, r0: int, r1: int, same_grid: bool
) -> NDArray[np.uint16]:
    """Baaskaardi koodid teenuse rastri ridadele ``r0:r1``."""
    win = Window(0, r0, ds.width, r1 - r0)
    if same_grid:
        return baas.read(1, window=win)
    dst = np.zeros((r1 - r0, ds.width), dtype=np.uint16)
    reproject(
        source=rasterio.band(baas, 1),
        destination=dst,
        dst_transform=ds.transform @ Affine.translation(0, r0),
        dst_crs=ds.crs,
        resampling=Resampling.nearest,
        src_nodata=0,
        dst_nodata=0,
    )
    return dst


def _accumulate_classes(
    codes: NDArray[np.uint16],
    val: NDArray[np.generic],
    ok: NDArray[np.bool_],
    lut_all: NDArray[np.int16],
    cls_stats: NDArray[np.float64],
) -> None:
    """Lisa ühe ploki-rea klassistatistika (kõik baaskaardi klassid) massiivi ``cls_stats``."""
    n_cls = cls_stats.shape[0]
    ci = lut_all[codes].astype(np.int64)
    inside = ci >= 0
    if not inside.any():
        return
    cls_stats[:, 0] += np.bincount(ci[inside], minlength=n_cls)
    sel = inside & ok
    if not sel.any():
        return
    c = ci[sel]
    x = val[sel].astype(np.float64)
    cls_stats[:, 1] += np.bincount(c, minlength=n_cls)
    cls_stats[:, 2] += np.bincount(c[x == 0], minlength=n_cls)
    cls_stats[:, 3] += np.bincount(c[x > 0], minlength=n_cls)
    cls_stats[:, 4] += np.bincount(c[x < 0], minlength=n_cls)
    cls_stats[:, 5] += np.bincount(c, weights=x, minlength=n_cls)
    cls_stats[:, 6] += np.bincount(c, weights=x * x, minlength=n_cls)


def _value_dtype(dtype: np.dtype[np.generic]) -> type[np.floating]:
    """Sagedustabeli väärtuse tüüp: float32, kui see esitab kõik väärtused täpselt, muidu float64."""
    exact32 = dtype == np.float32 or (dtype.kind in "iu" and dtype.itemsize <= 2)
    return np.float32 if exact32 else np.float64


def value_counts(e_km: NDArray[np.int64], kood: NDArray[np.int64], x: NDArray[np.generic]) -> pl.DataFrame:
    """Kadudeta sagedustabel ``(e_km, kood, väärtus) -> n``: iga erinev väärtus on oma rida (mitte vahemik).

    Sorteeritud koodi, väärtuse ja ploki järgi, et koodi kaupa lugemine saaks Parqueti statistikat kasutada.
    """
    o = np.lexsort((e_km, x, kood))
    e, k, v = e_km[o], kood[o], x[o]
    change = (k[1:] != k[:-1]) | (v[1:] != v[:-1]) | (e[1:] != e[:-1])
    st = np.flatnonzero(np.concatenate(([True], change))) if v.size else np.empty(0, dtype=np.int64)
    n = np.diff(np.append(st, v.size))
    return pl.DataFrame(
        {
            "e_km": e[st].astype(np.int16),
            "kood": k[st].astype(np.int32),
            "value": v[st].astype(_value_dtype(x.dtype)),
            "n": n.astype(np.int32),
        }
    )


def segment_medians(
    e_km: NDArray[np.int64], group: NDArray[np.int64], x: NDArray[np.float64]
) -> dict[str, NDArray[np.generic]]:
    """Täpsed mediaanid iga ``(e_km, group)`` kohta: kõik pikslid ja ainult nullist erinevad pikslid.

    Iga piksel on üks vaatlus; paarisarvu korral kahe keskmise väärtuse keskmine (nagu ``np.median``).
    Ühe sortimisega: sorteeritud lõigus on nullid järjest, nii et k-s nullist erinev väärtus on indeksil
    ``k`` (kui ``k`` < negatiivsete arv) või ``k + nullide arv``.
    """
    o = np.lexsort((x, group, e_km))
    e, g, v = e_km[o], group[o], x[o]
    st = np.flatnonzero(np.concatenate(([True], (e[1:] != e[:-1]) | (g[1:] != g[:-1]))))
    n = np.diff(np.append(st, v.size))
    med = (v[st + (n - 1) // 2] + v[st + n // 2]) / 2
    neg = np.add.reduceat((v < 0).astype(np.int64), st)
    zer = np.add.reduceat((v == 0).astype(np.int64), st)
    nnz = n - zer
    med_nz = np.full(n.size, np.nan)
    h = nnz > 0
    lo, hi = (nnz[h] - 1) // 2, nnz[h] // 2
    pick_lo = v[st[h] + lo + np.where(lo >= neg[h], zer[h], 0)]
    pick_hi = v[st[h] + hi + np.where(hi >= neg[h], zer[h], 0)]
    med_nz[h] = (pick_lo + pick_hi) / 2
    return {"e_km": e[st], "group": g[st], "n": n, "median": med, "n_nz": nnz, "median_nz": med_nz}


def aggregate_layer(
    spec: LayerSpec,
    src: Path,
    baas_det: Path,
    lut: NDArray[np.int16],
    n_classes: int,
    hist: HistSpec | None = None,
    hist_counts: NDArray[np.int64] | None = None,
    lut_all: NDArray[np.int16] | None = None,
    cls_stats: NDArray[np.float64] | None = None,
    val_dir: Path | None = None,
    groupings: dict[str, NDArray[np.int64]] | None = None,
    blk_med: list[pl.DataFrame] | None = None,
) -> pl.DataFrame:
    """Koonda üks teenuse raster plokkide kaupa.

    Parameters
    ----------
    spec
        Kihi kirjeldus (``invalid`` = lisaks NoData-le välistatavad sentinel-väärtused).
    src
        Teenuse rastri kohalik fail.
    baas_det
        ``OS_det_seisund_det_2022_5m.tif`` kohalik fail.
    lut
        Tulemus ``baas.class_lut``-ist.
    n_classes
        Klasside arv (``lut`` max väärtus + 1).
    hist, hist_counts
        Valikuline jaotus: ``hist`` on vahemikud (``hist.choose_spec``) ja ``hist_counts`` täidetav
        massiiv kujuga ``(n_classes, hist.n_bins + 1)``; viimane veerg on täpsete nullide arv.
    lut_all, cls_stats
        Valikuline klassitabel KÕIGI baaskaardi klasside kohta (ka seisundita ja rannik): ``lut_all`` on
        ``kood -> klassiindeks`` (``-1`` = klassita) ja ``cls_stats`` täidetav massiiv kujuga
        ``(klasse, N_CLS_STATS)`` (veerud ``CLS_STATS``): pikslid kokku, kehtivad, nullid, positiivsed,
        negatiivsed, Σx, Σx².
    val_dir
        Valikuline kaust kadudeta sagedustabelile (``value_counts``; üks fail ploki-rea kohta,
        ``n{n_km}.parquet``): kõik kehtivad baasklassi pikslid täpsete mediaanide jaoks.
    groupings, blk_med
        Valikulised rühmitused ``nimi -> massiiv kood -> rühm`` (``-1`` = ei kuulu) ja nimekiri, kuhu lisatakse
        iga ploki ja rühma täpne mediaan (``segment_medians``; veerud ``grouping, e_km, n_km, group, n,
        median, n_nz, median_nz``).

    Teenuse ruudustik laiendatakse baaskaardi ulatuseni (``extended_grid``); laiendatud pikslid on NoData.

    Returns
    -------
    pl.DataFrame
        Veerud ``e_km, n_km`` (ploki lääne-/lõunanurk km-des), ``cls`` (klassiindeks),
        ``n`` (pikslite arv), ``sum``, ``sumsq`` (Float64).
    """
    parts: list[pl.DataFrame] = []
    with rasterio.open(src) as ds, rasterio.open(baas_det) as baas:
        if ds.crs is None or ds.crs.to_epsg() != 3301:
            raise ValueError(f"{spec.id}: CRS ei ole EPSG:3301 ({ds.crs})")
        if ds.transform.e >= 0 or ds.transform.b != 0 or ds.transform.d != 0:
            raise ValueError(f"{spec.id}: ootamatu (mitte põhja-suunaline) transform")
        grid, c0, g0 = extended_grid(ds, tuple(baas.bounds))
        t = grid.transform
        cx = t.c + (np.arange(grid.width) + 0.5) * t.a
        bcol = np.floor(cx / config.BLOCK_M).astype(np.int64)
        col_vals, col_inv = np.unique(bcol, return_inverse=True)
        same_grid = grid.transform == baas.transform and (grid.height, grid.width) == baas.shape
        invalid = np.asarray(spec.invalid, dtype=np.float64)
        if val_dir is not None:
            shutil.rmtree(val_dir, ignore_errors=True)
            val_dir.mkdir(parents=True)
        for r0, r1, brow in _row_runs(grid):
            val, mask = _read_padded(ds, grid, c0, g0, r0, r1)
            ok, val = validity(val, mask, invalid, spec.zero_values)
            codes = _baas_chunk(baas, grid, r0, r1, same_grid)
            if lut_all is not None and cls_stats is not None:
                _accumulate_classes(codes, val, ok, lut_all, cls_stats)
            if val_dir is not None or groupings:
                base_ok = ok & ((lut_all if lut_all is not None else lut)[codes] >= 0)
                e_all = col_vals[np.broadcast_to(col_inv, val.shape)]
                if val_dir is not None and base_ok.any():
                    value_counts(e_all[base_ok], codes[base_ok].astype(np.int64), val[base_ok]).with_columns(
                        pl.lit(brow, dtype=pl.Int16).alias("n_km")
                    ).write_parquet(val_dir / f"n{brow}.parquet", compression="zstd", row_group_size=65_536)
                for gname, garr in (groupings or {}).items():
                    gid = garr[codes]
                    sel = ok & (gid >= 0)
                    if blk_med is None or not sel.any():
                        continue
                    m = segment_medians(e_all[sel], gid[sel], val[sel].astype(np.float64))
                    blk_med.append(
                        pl.DataFrame(m).with_columns(
                            pl.lit(gname).alias("grouping"), pl.lit(brow, dtype=pl.Int64).alias("n_km")
                        )
                    )
            idx = lut[codes]
            ok &= idx >= 0
            if not ok.any():
                continue
            col = np.broadcast_to(col_inv, val.shape)[ok].astype(np.int64)
            key = idx[ok].astype(np.int64) + n_classes * col
            x = val[ok].astype(np.float64)
            if hist is not None and hist_counts is not None:
                cls_ok = idx[ok].astype(np.int64)
                nb = hist.n_bins
                hist_counts[:, :nb] += np.bincount(
                    cls_ok * nb + bin_index(x, hist), minlength=n_classes * nb
                ).reshape(n_classes, nb)
                zero = x == 0
                if zero.any():
                    hist_counts[:, nb] += np.bincount(cls_ok[zero], minlength=n_classes)
            size = n_classes * col_vals.size
            n = np.bincount(key, minlength=size)
            s1 = np.bincount(key, weights=x, minlength=size)
            s2 = np.bincount(key, weights=x * x, minlength=size)
            nz = np.flatnonzero(n)
            parts.append(
                pl.DataFrame(
                    {
                        "e_km": col_vals[nz // n_classes].astype(np.int16),
                        "n_km": np.full(nz.size, brow, dtype=np.int16),
                        "cls": (nz % n_classes).astype(np.int16),
                        "n": n[nz].astype(np.int32),
                        "sum": s1[nz],
                        "sumsq": s2[nz],
                    }
                )
            )
    if not parts:
        return pl.DataFrame(
            schema={
                "e_km": pl.Int16,
                "n_km": pl.Int16,
                "cls": pl.Int16,
                "n": pl.Int32,
                "sum": pl.Float64,
                "sumsq": pl.Float64,
            }
        )
    return pl.concat(parts)
