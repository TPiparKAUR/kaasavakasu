"""Vektorireeglite (metoodika v2) testid: kattuvusel maksimum, NULL ja -1 -> 0, polügoonist väljas NoData."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyogrio.raw
import pytest
import rasterio
import shapely
from rasterio.windows import Window

from oks import fields


def _gpkg(path: Path, geoms: list[shapely.Geometry], vals: list[float]) -> Path:
    pyogrio.raw.write(
        path,
        shapely.to_wkb(np.array(geoms, dtype=object)),
        [np.array(vals, dtype=np.float64)],
        ["v"],
        driver="GPKG",
        crs="EPSG:3301",
        geometry_type="Polygon",
    )
    return path


def test_rasterize_rules(tmp_path: Path) -> None:
    x0, y0 = fields.X0, fields.Y0
    box = lambda c0, r0, c1, r1: shapely.box(x0 + c0 * 10, y0 - r1 * 10, x0 + c1 * 10, y0 - r0 * 10)  # noqa: E731
    geoms = [box(0, 0, 4, 4), box(2, 2, 6, 6), box(0, 6, 2, 8), box(4, 6, 6, 8), box(6, 0, 8, 2)]
    vals = [5.0, 3.0, np.nan, -1.0, 2.0]
    # failis on 5 enne 3: ilma sortimiseta võidaks kattuvusel viimane (3)
    src = _gpkg(tmp_path / "v.gpkg", geoms, vals)
    out = fields.rasterize_attribute(src, "v", tmp_path / "v.tif")
    with rasterio.open(out) as ds:
        a = ds.read(1, window=Window(0, 0, 10, 10))
        nd = ds.nodata
    assert a[3, 3] == 5.0  # kattuvus 5 ja 3 -> maksimum
    assert a[5, 5] == 3.0
    assert a[7, 1] == 0.0  # NULL -> 0
    assert a[7, 5] == 0.0  # -1 -> 0
    assert a[1, 7] == 2.0
    assert a[9, 9] == nd  # polügoonist väljas: NoData (aggregeerimisel null)


def test_resample_coarse_to_10m_keeps_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """930 m raster -> 10 m lähima naabriga: väärtus kordub ruudu sees, väljaspool on NoData."""
    from rasterio.transform import from_origin

    from oks import pipeline

    monkeypatch.setattr(fields, "X0", 400_000.0)
    monkeypatch.setattr(fields, "Y0", 6_500_000.0)
    monkeypatch.setattr(fields, "WIDTH", 300)
    monkeypatch.setattr(fields, "HEIGHT", 200)
    src = tmp_path / "c.tif"
    with rasterio.open(
        src,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        crs="EPSG:3301",
        transform=from_origin(400_000.0, 6_500_000.0, 930.0, 930.0),
        nodata=255.0,
    ) as ds:
        ds.write(np.array([[1.5, 2.5], [3.5, 255.0]], dtype=np.float32), 1)
    out = pipeline.resample_to_10m(src, tmp_path / "c10.tif")
    with rasterio.open(out) as ds:
        a = ds.read(1)
        assert ds.res == (10.0, 10.0) and ds.crs.to_epsg() == 3301
    assert a[0, 0] == 1.5 and a[92, 92] == 1.5  # keskpunkt 925 m < 930 m
    assert a[0, 93] == 2.5 and a[93, 0] == 3.5
    assert a[100, 100] == 255.0  # algne NoData jääb NoData-ks (aggregeerimisel null)
    assert a[0, 200] == 255.0  # väljaspool algset rastrit
