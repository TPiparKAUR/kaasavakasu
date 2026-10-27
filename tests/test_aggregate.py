"""Aggregeerimise testid tehisrastritega (teada vastus)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest
import rasterio
from rasterio.transform import from_origin

from oks import aggregate

N_CLASSES = 2


def _write(path: Path, arr: np.ndarray, res: float, x0: float, y0: float, nodata: float | None) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=arr.dtype,
        crs="EPSG:3301",
        transform=from_origin(x0, y0, res, res),
        nodata=nodata,
    ) as ds:
        ds.write(arr, 1)


@pytest.fixture
def baas(tmp_path: Path) -> Path:
    det = np.zeros((400, 400), dtype=np.uint16)  # 5 m, 2 km x 2 km
    det[:, :200] = 10110  # lääne pool: hea
    det[:, 200:] = 10141  # ida pool: vilets
    p = tmp_path / "baas.tif"
    _write(p, det, 5.0, 400_000.0, 6_501_000.0, 0)
    return p


@pytest.fixture
def lut() -> np.ndarray:
    lut = np.full(65536, -1, dtype=np.int16)
    lut[10110] = 0
    lut[10141] = 1
    return lut


def _by_key(df):  # noqa: ANN001, ANN202
    return {(r["e_km"], r["n_km"], r["cls"]): r for r in df.iter_rows(named=True)}


def test_aligned_10m_layer_sums(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    rows = np.arange(200, dtype=np.float32)[:, None] * np.ones((1, 200), dtype=np.float32)
    src = tmp_path / "svc.tif"
    _write(src, rows, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    d = _by_key(df)
    assert len(d) == 4  # 2 plokki ida-läänes x 2 põhja-lõunas
    top_west = d[(400, 6500, 0)]
    assert top_west["n"] == 100 * 100
    assert top_west["sum"] == pytest.approx(100 * sum(range(100)))
    assert top_west["sumsq"] == pytest.approx(100 * sum(r * r for r in range(100)))
    bottom_east = d[(401, 6499, 1)]
    assert bottom_east["sum"] == pytest.approx(100 * sum(range(100, 200)))
    assert df["n"].sum() == 200 * 200


def test_nodata_and_extra_invalid_are_excluded(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.full((200, 200), 5.0, dtype=np.float32)
    arr[0, 0] = -9999.0  # deklareeritud NoData
    arr[0, 1] = np.nan
    arr[0, 2] = 255.0  # sentinel, antud invalid-i kaudu
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", invalid=(255.0,)), src, baas, lut, N_CLASSES
    )
    assert df["n"].sum() == 200 * 200 - 3
    assert df["sum"].sum() == pytest.approx(5.0 * (200 * 200 - 3))


def test_same_grid_5m_layer(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.ones((400, 400), dtype=np.uint8)
    src = tmp_path / "svc5.tif"
    _write(src, arr, 5.0, 400_000.0, 6_501_000.0, 255.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert df["n"].sum() == 400 * 400
    assert set(df["cls"].to_list()) == {0, 1}


def test_shifted_grid_uses_nearest_class_and_keeps_totals(
    tmp_path: Path, baas: Path, lut: np.ndarray
) -> None:
    arr = np.full((190, 190), 2.0, dtype=np.float32)
    src = tmp_path / "shifted.tif"
    _write(src, arr, 10.0, 400_003.0, 6_500_997.0, -9999.0)  # nihutatud 3 m
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert df["n"].sum() == 190 * 190
    assert df["sum"].sum() == pytest.approx(2.0 * 190 * 190)
    west = df.filter(df["cls"] == 0)["n"].sum()
    east = df.filter(df["cls"] == 1)["n"].sum()
    assert west + east == 190 * 190
    # piir 401000: x-keskpunktid 400008..400998 (<401000) -> 100 veergu läände
    assert west == 100 * 190


def test_pixels_without_state_are_dropped(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    lut2 = lut.copy()
    lut2[10141] = -1  # ida pool ilma seisundita
    arr = np.ones((200, 200), dtype=np.float32)
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut2, N_CLASSES)
    assert set(df["cls"].to_list()) == {0}
    assert df["n"].sum() == 100 * 200


def test_rejects_wrong_crs(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    src = tmp_path / "bad.tif"
    with rasterio.open(
        src,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(0, 0, 0.1, 0.1),
    ) as ds:
        ds.write(np.ones((10, 10), dtype=np.float32), 1)
    with pytest.raises(ValueError, match="CRS"):
        aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)


def test_zero_values_count_as_valid_zero(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """NoData = 0 on kehtiv null (lähtekasu loogikakontroll: 25 ha 100-st, ülejäänud nullid)."""
    arr = np.zeros((200, 200), dtype=np.uint8)
    arr[:50, :100] = 8  # 50 x 100 = 5000 positiivset piksilit läänepoolses klassis
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, 0.0)  # deklareeritud NoData on 0
    excl = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert excl["n"].sum() == 5000  # vana käitumine: nullid välja
    incl = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", zero_values=(0.0,)), src, baas, lut, N_CLASSES
    )
    assert incl["n"].sum() == 200 * 200
    west = incl.filter(incl["cls"] == 0)
    assert west["sum"].sum() / west["n"].sum() == pytest.approx(8 * 5000 / (100 * 200))


def test_extra_zero_value_255_acts_as_zero(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.full((200, 200), 4, dtype=np.uint8)
    arr[:, :20] = 255  # tabeli märkus: 255 käitub kui 0
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, 0.0)
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", zero_values=(0.0, 255.0)), src, baas, lut, N_CLASSES
    )
    assert df["n"].sum() == 200 * 200
    assert df["sum"].sum() == pytest.approx(4.0 * 200 * 180)


def test_class_stats_cover_classes_without_state(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """Klassitabel hõlmab ka seisundita klassid (rannik) ning loeb kehtivad, nullid ja positiivsed eraldi."""
    lut_all = np.full(65536, -1, dtype=np.int16)
    lut_all[10110] = 0
    lut_all[10141] = 1
    lut2 = lut.copy()
    lut2[10141] = -1  # ida pool: seisundita (blokitabelist välja)
    arr = np.full((200, 200), 2.0, dtype=np.float32)
    arr[:, 100:] = 0.0
    arr[0, 100] = -9999.0  # NoData idapoolses klassis
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    stats = np.zeros((2, aggregate.N_CLS_STATS), dtype=np.float64)
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif"), src, baas, lut2, N_CLASSES, lut_all=lut_all, cls_stats=stats
    )
    assert set(df["cls"].to_list()) == {0}
    west, east = stats
    names = aggregate.CLS_STATS
    assert west[names.index("n_total")] == 100 * 200 and west[names.index("n_pos")] == 100 * 200
    assert east[names.index("n_total")] == 100 * 200
    assert east[names.index("n_valid")] == 100 * 200 - 1
    assert east[names.index("n_zero")] == 100 * 200 - 1 and east[names.index("n_pos")] == 0
    assert west[names.index("sum")] == pytest.approx(2.0 * 100 * 200)


def test_extent_outside_service_raster_is_nodata_zero(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """K7: baaskaardi pikslid väljaspool teenuse ruudustikku on NoData -> null (kui NoData on null)."""
    arr = np.full((200, 100), 3.0, dtype=np.float32)  # katab ainult lääne poole (400000..401000)
    src = tmp_path / "west.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    excl = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert excl["n"].sum() == 200 * 100
    incl = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", zero_values=(-9999.0,)), src, baas, lut, N_CLASSES
    )
    assert incl["n"].sum() == 200 * 200
    east = incl.filter(incl["cls"] == 1)
    assert east["n"].sum() == 200 * 100 and east["sum"].sum() == 0


def test_extended_grid_keeps_lattice_with_float_resolution(tmp_path: Path) -> None:
    """Ebatäpne piksel (10.000000000000002 m) ja nihutatud algpunkt: laiendus jääb samasse võrgustikku."""
    src = tmp_path / "odd.tif"
    with rasterio.open(
        src,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:3301",
        transform=from_origin(400_010.0, 6_500_900.0, 10.000000000000002, 10.000000000000002),
        nodata=-9999.0,
    ) as ds:
        ds.write(np.ones((10, 10), dtype=np.float32), 1)
    with rasterio.open(src) as ds:
        grid, c0, r0 = aggregate.extended_grid(ds, (400_000.0, 6_500_000.0, 400_200.0, 6_501_000.0))
    assert (c0, r0) == (-1, -10)
    assert grid.width == 20 and grid.height == 100
    assert grid.transform.c == pytest.approx(400_000.0) and grid.transform.f == pytest.approx(6_501_000.0)


def test_float32_minimum_sentinel_is_zero(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """Tabeli NoData (float64 kujul) tabab float32 sentinel-väärtust täpselt."""
    nd = -3.399999952144364e38
    arr = np.full((200, 200), 2.0, dtype=np.float32)
    arr[:, :50] = np.float32(nd)
    src = tmp_path / "f32.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, float(np.float32(nd)))
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", zero_values=(nd,)), src, baas, lut, N_CLASSES
    )
    assert df["n"].sum() == 200 * 200
    assert df["sum"].sum() == pytest.approx(2.0 * 200 * 150)


def test_segment_medians_match_numpy() -> None:
    rng = np.random.default_rng(3)
    n = 20_000
    e = rng.integers(0, 4, n)
    g = rng.integers(0, 5, n)
    x = np.where(rng.random(n) < 0.4, 0.0, rng.integers(-3, 9, n).astype(np.float64))
    m = aggregate.segment_medians(e, g, x)
    for i in range(m["n"].size):
        sel = (e == m["e_km"][i]) & (g == m["group"][i])
        assert m["n"][i] == sel.sum()
        assert m["median"][i] == np.median(x[sel])
        nz = x[sel][x[sel] != 0]
        assert m["n_nz"][i] == nz.size
        assert (np.isnan(m["median_nz"][i]) and nz.size == 0) or m["median_nz"][i] == np.median(nz)


def test_value_table_and_block_medians_are_exact(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """Sagedustabelist taastatud mediaan ja plokimediaanid võrduvad np.median-iga toorpikslitel."""
    rng = np.random.default_rng(7)
    arr = rng.random((200, 200)).astype(np.float32)
    arr[rng.random((200, 200)) < 0.3] = 0
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    grp = np.full(65536, -1, dtype=np.int64)
    grp[10110], grp[10141] = 1, 2
    blk: list[pl.DataFrame] = []
    vdir = tmp_path / "val"
    aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif"),
        src,
        baas,
        lut,
        N_CLASSES,
        val_dir=vdir,
        groupings={"g": grp},
        blk_med=blk,
    )
    vt = pl.read_parquet(vdir / "*.parquet")
    assert vt["n"].sum() == 200 * 200
    west = vt.filter(vt["kood"] == 10110).sort("value")
    vals = np.repeat(west["value"].to_numpy(), west["n"].to_numpy())
    assert np.median(vals) == np.median(arr[:, :100])
    bm = pl.concat(blk)
    r = bm.filter((bm["e_km"] == 401) & (bm["n_km"] == 6500) & (bm["group"] == 2)).row(0, named=True)
    block = arr[:100, 100:].astype(np.float64)
    assert r["n"] == block.size and r["median"] == np.median(block)
    assert r["median_nz"] == np.median(block[block != 0])
