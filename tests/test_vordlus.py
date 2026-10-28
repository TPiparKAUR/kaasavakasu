"""Metoodikate võrdluse (v1 → v2) testid."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from oks import vordlus


def test_sig_class() -> None:
    assert vordlus.sig_class(True, 1.0, True, 2.0) == "jäi oluliseks, sama suund"
    assert vordlus.sig_class(True, 1.0, True, -2.0) == "suund muutus"
    assert vordlus.sig_class(False, 1.0, True, 2.0) == "muutus oluliseks"
    assert vordlus.sig_class(True, 1.0, False, 2.0) == "ei ole enam oluline"
    assert vordlus.sig_class(False, 1.0, False, 2.0) == "ei olnud ega ole oluline"
    assert vordlus.sig_class(None, None, False, 2.0) == "hinnang lisandus"
    assert vordlus.sig_class(True, 1.0, None, None) == "hinnang kadus"
    assert vordlus.sig_class(None, None, None, None) == "andmeid ei piisa"
    assert set(vordlus.SIG_CLASSES) >= {"andmeid ei piisa", "suund muutus"}


def test_cause_priority() -> None:
    assert vordlus.cause("lamm_grd1000_am_drained_2022", True, 0.1, 1.0) == "madal_lahutus"
    assert vordlus.cause("toiduteenus_2022", True, 0.1, 1.0) == "vektor"
    assert vordlus.cause("kasemahl_saagikus_2020_10m", False, 0.4, 0.4) == "erand"
    assert vordlus.cause("x", False, 0.5, 0.9) == "nodata0"
    assert vordlus.cause("x", False, 0.9, 0.9) == "sama"
    assert vordlus.cause("x", False, None, 0.9) == "puudub"


def _write(d: Path, cells: pl.DataFrame, pairs: pl.DataFrame) -> Path:
    d.mkdir()
    cells.write_parquet(d / "kaasnev_tuup_seisund.parquet")
    pairs.write_parquet(d / "paarid.parquet")
    return d


def test_compare_splits_sample_and_statistic(tmp_path: Path) -> None:
    key = {"layer_id": ["x"], "okosusteem_kood": [3], "okosusteem": ["Metsad"], "alam_kood": [100]}
    key |= {"tuup": ["Palumets"], "seisund_nimi": ["hea"]}
    v1 = _write(
        tmp_path / "v1",
        pl.DataFrame(key | {"mean": [4.0], "kate": [0.5]}),
        pl.DataFrame(
            {
                "layer_id": ["x", "x"],
                "unit_level": ["okosusteem"] * 2,
                "unit_code": [3, 3],
                "pair": ["vilets→hea", "vilets→keskmine"],
                "delta_m": [1.0, 1.0],
                "oluline_m": [True, True],
                "enough_m": [True, False],
            }
        ),
    )
    v2 = _write(
        tmp_path / "v2",
        pl.DataFrame(
            key | {"pindala_ha": [10.0], "mean": [2.0], "median": [0.0], "kate": [1.0], "esineb_osa": [0.4]}
        ),
        pl.DataFrame(
            {
                "layer_id": ["x", "x"],
                "unit_level": ["okosusteem"] * 2,
                "unit_code": [3, 3],
                "pair": ["vilets→hea", "vilets→keskmine"],
                "delta_m": [0.5, 0.3],
                "oluline_m": [True, True],
                "delta_m_med": [-0.2, 0.1],
                "oluline_m_med": [True, False],
                "enough_m": [True, True],
            }
        ),
    )
    out = vordlus.compare(v1, v2, {"x": "X"}, set())
    c = out["lahtrid"].row(0, named=True)
    assert c["rel_valim"] == pytest.approx(-0.5)  # 4 -> 2: ainult valimireeglid
    assert c["rel_statistik"] == pytest.approx(-1.0)  # keskmine 2 -> mediaan 0
    p = {r["pair"]: r for r in out["paarid"].iter_rows(named=True)}
    assert p["vilets→hea"]["muutus_valim"] == "jäi oluliseks, sama suund"
    assert p["vilets→hea"]["muutus_statistik"] == "suund muutus"
    assert p["vilets→keskmine"]["muutus_kokku"] == "hinnang lisandus"  # v1-s andmeid ei piisanud
    k = out["kihid"].row(0, named=True)
    assert (k["pohjus"], k["nimi"], k["kate_v1"], k["kate_v2"]) == ("nodata0", "X", 0.5, 1.0)
    assert (k["olulisi_v1"], k["olulisi_v2_mediaan"], k["suund_muutus"], k["hinnang_lisandus"]) == (
        1,
        1,
        1,
        1,
    )
