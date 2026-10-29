"""Baaskaardi pindala ja seisundikaardistuse sõltumatu kontroll rastrist (vajab ``data/cache/Baaskaart``).

Loeb ``OS_det_seisund_det_2022_5m.tif`` ja ``seisund_uldine_2022_5m.tif`` ribade kaupa, loendab pikslid koodi x seisundi
kaupa ja võrdleb ``data/derived/klassid.parquet`` (``n_pix``, ``uld``) ning ``baaskaart_ristiks_5m.parquet`` sisuga.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    det_p = ROOT / "data/cache/Baaskaart/OS_det_seisund_det_2022_5m.tif"
    uld_p = ROOT / "data/cache/Baaskaart/seisund_uldine_2022_5m.tif"
    cnt = np.zeros(65536 * 8, dtype=np.int64)
    with rasterio.open(det_p) as d, rasterio.open(uld_p) as u:
        assert d.shape == u.shape and d.transform == u.transform
        h, w = d.shape
        for r0 in range(0, h, 1024):
            win = Window(0, r0, w, min(1024, h - r0))
            dv, uv = d.read(1, window=win), u.read(1, window=win)
            m = dv != 0
            cnt += np.bincount(dv[m].astype(np.int64) * 8 + uv[m].astype(np.int64), minlength=cnt.size)
    idx = np.flatnonzero(cnt)
    raster = pl.DataFrame(
        {"kood": (idx // 8).astype(np.int32), "uld": (idx % 8).astype(np.int8), "n": cnt[idx]}
    )
    per_code = raster.group_by("kood").agg(
        pl.col("uld").n_unique().alias("n_uld"), pl.col("uld").first(), pl.col("n").sum()
    )
    cls = pl.read_parquet(ROOT / "data/derived/klassid.parquet")
    j = cls.join(per_code, on="kood", how="full", suffix="_r")
    out = {
        "koode rastris": per_code.height,
        "koode klassid.parquet": cls.height,
        "koode mitme seisundiga": per_code.filter(pl.col("n_uld") > 1).height,
        "n_pix lahknevusi": j.filter(pl.col("n_pix") != pl.col("n")).height,
        "uld lahknevusi": j.filter(pl.col("uld") != pl.col("uld_r")).height,
        "pindala kokku km2 (rastrist)": float(per_code["n"].sum() * 25 / 1e6),
        "pindala kokku km2 (klassid.parquet)": float(cls["n_pix"].sum() * 25 / 1e6),
        "pindala seisundi (uld) kaupa km2": {
            int(k): float(v)
            for k, v in raster.group_by("uld")
            .agg(pl.col("n").sum())
            .sort("uld")
            .select("uld", pl.col("n") * 25 / 1e6)
            .iter_rows()
        },
    }
    (ROOT / "data/tulemused/validatsioon_baaskaart.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
