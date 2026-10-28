"""Metoodikate võrdlus v1 → v2: kirjutab ``data/tulemused/vordlus_{kihid,lahtrid,paarid}.csv``.

v1 tulemused võetakse git'ist commit'ist ``V1_COMMIT`` (metoodika v1 viimane seis), v2 tulemused kaustast
``data/tulemused``. Käivitus pärast ``oks analyse`` ja ``oks kaasnev``: ``uv run python scripts/vordle_metoodikad.py``.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

import polars as pl

from oks import config, pipeline, vordlus

V1_COMMIT = "5aa4596"
V1_FILES = ("kaasnev_tuup_seisund.parquet", "paarid.parquet")

log = logging.getLogger("vordle_metoodikad")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    names = dict(pl.read_csv(config.ROOT / "data/teenused.csv").select("id", "nimi").iter_rows())
    vector = {lid for lid, *_ in pipeline.FIELD_LAYERS}
    with tempfile.TemporaryDirectory() as tmp:
        v1 = Path(tmp)
        for f in V1_FILES:
            blob = subprocess.run(
                ["git", "show", f"{V1_COMMIT}:data/tulemused/{f}"],
                cwd=config.ROOT,
                check=True,
                capture_output=True,
            ).stdout
            (v1 / f).write_bytes(blob)
        out = vordlus.compare(v1, config.RESULTS, names, vector)
    for k, df in out.items():
        path = config.RESULTS / f"vordlus_{k}.csv"
        df.write_csv(path)
        log.info("%s: %d rida", path.name, df.height)


if __name__ == "__main__":
    main()
