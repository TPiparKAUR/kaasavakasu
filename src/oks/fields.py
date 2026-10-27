"""Vektorkihtide (põllumassiivid) rasteriseerimine baaskaardi 10 m ruudustikule.

``toiduteenus_2022`` ja ``biotorje_2022`` on põllumassiivide polügoonid (sama ``pollu_id``).
Atribuut rasteriseeritakse ploki-ridade kaupa ja kirjutatakse tihendatud GeoTIFF-ina, mille
järel kasutatakse sama aggregeerimisliini nagu rastrite puhul.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pyogrio
import rasterio
import shapely
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import Window

from . import config

log = logging.getLogger(__name__)

#: Baaskaardi 10 m ruudustik (ühtib baaskaardi 5 m kihi servadega).
X0, Y0, RES = 369_000.0, 6_635_000.0, 10.0
WIDTH, HEIGHT = 37_100, 25_800
ROWS_PER_STRIPE = 100  # = 1 km

Mapper = Callable[[np.ndarray], np.ndarray]


def rasterize_attribute(
    gpkg: Path, attribute: str, out: Path, mapper: Mapper | None = None, nodata: float = -9999.0
) -> Path:
    """Rasteriseeri polügooni atribuut ``out`` GeoTIFF-i (float32, 10 m, EPSG:3301).

    Parameters
    ----------
    gpkg
        GeoPackage'i fail.
    attribute
        Atribuudi veerg.
    out
        Sihtfail.
    mapper
        Valikuline teisendus (nt tähtklassid -> arvud); peab tagastama ``float64`` massiivi.
    nodata
        NoData-väärtus.

    Notes
    -----
    Piksel saab polügooni väärtuse, kui selle keskpunkt jääb polügooni sisse
    (``all_touched=False``). Metoodika v2 vektorireeglid: NULL (NaN) ja ``-1`` -> 0; kattuvate polügoonide
    korral maksimum. Polügoonist väljas jääb ``nodata`` (aggregeerimisel loetakse see nulliks).
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.tif")
    transform = from_origin(X0, Y0, RES, RES)
    with rasterio.open(
        tmp,
        "w",
        driver="GTiff",
        height=HEIGHT,
        width=WIDTH,
        count=1,
        dtype="float32",
        crs="EPSG:3301",
        transform=transform,
        nodata=nodata,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
    ) as dst:
        for r0 in range(0, HEIGHT, ROWS_PER_STRIPE):
            h = min(ROWS_PER_STRIPE, HEIGHT - r0)
            ytop = Y0 - r0 * RES
            bbox = (X0, ytop - h * RES, X0 + WIDTH * RES, ytop)
            meta, _fids, geoms, fields = pyogrio.raw.read(gpkg, columns=[attribute], bbox=bbox)
            if len(geoms) == 0:
                continue
            vals = np.asarray(fields[0])
            vals = mapper(vals) if mapper else vals.astype("float64")
            vals = np.where(~np.isfinite(vals) | (vals == -1), 0.0, vals)
            # GDAL põletab kujundid järjekorras ja viimane võidab: kasvav järjekord annab kattuvusel maksimumi
            order = np.argsort(vals, kind="stable")
            shapes = [
                (g, float(v))
                for g, v in zip(shapely.from_wkb(geoms)[order], vals[order], strict=True)
                if g is not None
            ]
            if not shapes:
                continue
            arr = rasterize(
                shapes,
                out_shape=(h, WIDTH),
                transform=transform @ rasterio.Affine.translation(0, r0),
                fill=nodata,
                dtype="float32",
                all_touched=False,
            )
            dst.write(arr, 1, window=Window(0, r0, WIDTH, h))
            if (r0 // ROWS_PER_STRIPE) % 50 == 0:
                log.info(
                    "%s/%s: riba %d/%d",
                    gpkg.name,
                    attribute,
                    r0 // ROWS_PER_STRIPE + 1,
                    HEIGHT // ROWS_PER_STRIPE,
                )
    tmp.replace(out)
    return out


def value_class_to_number(a: np.ndarray) -> np.ndarray:
    """Teisenda väärtusklassid ``A..D`` arvudeks 1..4 (tundmatud -> NaN)."""
    mp = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0}
    return np.array([mp.get(str(x), np.nan) for x in a], dtype="float64")


def cached_gpkg(rel: str) -> Path:
    """Tee GeoPackage'i kohaliku koopia juurde (laadib alla, kui puudub)."""
    from . import fetch

    return fetch.download(rel, config.CACHE / "vektor" / rel)
