"""Statistikamooduli testid sünteetilise andmestikuga (teadaolev efekt)."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from oks import stats


def _used() -> pl.DataFrame:
    # eco 1 (alam 10100): hea=0, keskmine=1, vilets=2 ; eco 3 (alam 30100): sama
    rows = [
        (0, 10110, 10100, 1, 1),
        (1, 10130, 10100, 1, 2),
        (2, 10141, 10100, 1, 3),
        (3, 30110, 30100, 3, 1),
        (4, 30130, 30100, 3, 2),
        (5, 30140, 30100, 3, 3),
    ]
    return pl.DataFrame(
        rows, schema=["idx", "kood", "alam_kood", "okosusteem_kood", "uld"], orient="row"
    ).with_columns(pl.col("idx").cast(pl.UInt32))


def _synthetic(
    effects: dict[int, tuple[float, float, float]], seed: int = 1, n_px: int = 200, tau: float = 0.0
) -> pl.DataFrame:
    """40x40 plokki; efekt klassi kohta (vilets, keskmine, hea); plokiefekt SD 5, piksli SD 1."""
    rng = np.random.default_rng(seed)
    rows = []
    for e in range(400, 440):
        for n in range(6400, 6440):
            block = rng.normal(0, 5)
            for cls, eco in ((0, 1), (1, 1), (2, 1), (3, 3), (4, 3), (5, 3)):
                state = 3 - _used().filter(pl.col("idx") == cls)["uld"].item()
                mu = 100 + block + effects[eco][state] + (rng.normal(0, tau) if tau else 0.0)
                s = n_px * mu
                s2 = n_px * (mu**2 + 1.0)
                rows.append((e, n, cls, n_px, s, s2))
    return pl.DataFrame(rows, schema=["e_km", "n_km", "cls", "n", "sum", "sumsq"], orient="row").with_columns(
        pl.col("e_km").cast(pl.Int16),
        pl.col("n_km").cast(pl.Int16),
        pl.col("cls").cast(pl.Int16),
        pl.col("n").cast(pl.Int32),
    )


@pytest.fixture(scope="module")
def result() -> dict[str, pl.DataFrame]:
    u = stats.make_units(_used())
    tbl = _synthetic({1: (10.0, 12.0, 15.0), 3: (7.0, 7.0, 7.0)})
    p = stats.Params(n_boot=400, min_strata=20)
    return stats.analyse_layer(tbl, u, 10.0, p)


def test_make_units() -> None:
    u = stats.make_units(_used())
    assert u.eco_codes == (1, 3)
    assert u.alam_codes == (10100, 30100)
    assert list(u.cls_state) == [2, 1, 0, 2, 1, 0]  # hea=2 ... vilets=0


def test_known_effect_is_recovered(result: dict[str, pl.DataFrame]) -> None:
    r = result["paarid"].filter((pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 1))
    d = {row["pair"]: row for row in r.iter_rows(named=True)}
    assert d["vilets→keskmine"]["delta_m"] == pytest.approx(2.0, abs=1e-9)
    assert d["keskmine→hea"]["delta_m"] == pytest.approx(3.0, abs=1e-9)
    assert d["vilets→hea"]["delta_m"] == pytest.approx(5.0, abs=1e-9)
    # paaritamata hinnang on sama (kõik plokid sisaldavad kõiki seisundeid)
    assert d["vilets→hea"]["delta_u"] == pytest.approx(5.0, abs=1e-9)
    assert d["vilets→hea"]["rel_m"] == pytest.approx(5.0 / 110.0, rel=0.2)
    assert d["vilets→hea"]["p_m"] < 0.01
    assert d["vilets→hea"]["ci_m_lo"] <= 5.0 <= d["vilets→hea"]["ci_m_hi"]


def test_noisy_effect_ci_covers_truth_and_has_width() -> None:
    u = stats.make_units(_used())
    tbl = _synthetic({1: (10.0, 12.0, 15.0), 3: (7.0, 7.0, 7.0)}, seed=5, tau=2.0)
    r = stats.analyse_layer(tbl, u, 10.0, stats.Params(n_boot=600))["paarid"]
    row = r.filter(
        (pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 1) & (pl.col("pair") == "vilets→hea")
    ).row(0, named=True)
    assert row["ci_m_hi"] - row["ci_m_lo"] > 0
    assert row["ci_m_lo"] < 5.0 < row["ci_m_hi"]
    assert row["p_m"] < 0.01
    null = r.filter(
        (pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 3) & (pl.col("pair") == "vilets→hea")
    ).row(0, named=True)
    assert null["ci_m_lo"] < 0 < null["ci_m_hi"]
    assert null["p_m"] > 0.05


def test_null_effect_is_not_significant(result: dict[str, pl.DataFrame]) -> None:
    r = result["paarid"].filter((pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 3))
    for row in r.iter_rows(named=True):
        assert abs(row["delta_m"]) < 1e-9
        assert row["ci_m_lo"] <= 0 <= row["ci_m_hi"] or row["delta_m"] == 0


def test_pooled_sd_matches_pixel_sd(result: dict[str, pl.DataFrame]) -> None:
    c = result["lahtrid"].filter((pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 3))
    # pikslisisene SD on 1; plokkide vaheline SD ~5 lisandub kogu-SD-sse
    assert c["sd"].min() > 4.5  # kogu-SD sisaldab plokiefekti


def test_cell_table_has_all_states(result: dict[str, pl.DataFrame]) -> None:
    c = result["lahtrid"].filter((pl.col("unit_level") == "alam") & (pl.col("unit_code") == 10100))
    assert sorted(c["state"].to_list()) == ["hea", "keskmine", "vilets"]
    assert c["n"].min() == 40 * 40 * 200


def test_unmatched_differs_from_matched_under_confounding() -> None:
    """Kui 'hea' esineb ainult kõrge plokiefektiga plokkides, eksib paaritamata hinnang, paaritatud mitte."""
    rng = np.random.default_rng(3)
    rows = []
    for e in range(400, 440):
        for n in range(6400, 6440):
            block = rng.normal(0, 5)
            for cls in (0, 1, 2):
                state = 2 - cls  # cls0 = hea ... cls2 = vilets
                # 'hea' ainult plokkides block>0, 'vilets' kõikjal
                if state == 2 and block <= 0:
                    continue
                mu = 100 + block + 3.0 * state
                rows.append((e, n, cls, 200, 200 * mu, 200 * (mu**2 + 1)))
    tbl = pl.DataFrame(rows, schema=["e_km", "n_km", "cls", "n", "sum", "sumsq"], orient="row").with_columns(
        pl.col("e_km").cast(pl.Int16),
        pl.col("n_km").cast(pl.Int16),
        pl.col("cls").cast(pl.Int16),
        pl.col("n").cast(pl.Int32),
    )
    u = stats.make_units(_used())
    r = stats.analyse_layer(tbl, u, 10.0, stats.Params(n_boot=200))["paarid"]
    row = r.filter(
        (pl.col("unit_level") == "alam") & (pl.col("unit_code") == 10100) & (pl.col("pair") == "vilets→hea")
    ).row(0, named=True)
    assert row["delta_m"] == pytest.approx(6.0, abs=1e-6)  # tõeline efekt 3.0 * 2
    assert row["delta_u"] > 8.0  # valikuline esinemine paisutab paaritamata hinnangut


def test_min_area_excludes_small_strata() -> None:
    u = stats.make_units(_used())
    tbl = _synthetic({1: (10.0, 12.0, 15.0), 3: (7.0, 7.0, 7.0)}, n_px=50)  # 50 px * 100 m2 = 0.5 ha < 1 ha
    r = stats.analyse_layer(tbl, u, 10.0, stats.Params(n_boot=100))["paarid"]
    assert r["n_strata"].max() == 0
    assert r["enough_m"].sum() == 0


def test_bh_fdr_matches_reference() -> None:
    p = np.array([0.01, 0.04, 0.03, 0.005, np.nan, 0.5])
    q = stats.bh_fdr(p)
    # käsitsi: m=5; sorted 0.005,0.01,0.03,0.04,0.5 -> *5/rank = .025,.025,.05,.05,.5
    assert q[3] == pytest.approx(0.025)
    assert q[0] == pytest.approx(0.025)
    assert q[2] == pytest.approx(0.05)
    assert q[1] == pytest.approx(0.05)
    assert q[5] == pytest.approx(0.5)
    assert np.isnan(q[4])


def test_cluster_index_bounds() -> None:
    e = np.array([369, 739, 740, 1000], dtype=np.int64)
    n = np.array([6377, 6634, 6635, 9000], dtype=np.int64)
    idx, total = stats.cluster_index(e, n, 10)
    assert idx.min() >= 0
    assert idx.max() < total


def test_cluster_expr_matches_cluster_index() -> None:
    rng = np.random.default_rng(3)
    e = np.concatenate([rng.integers(360, 750, 500), [368, 369, 740]]).astype(np.int64)
    n = np.concatenate([rng.integers(6370, 6640, 500), [6376, 6377, 6635]]).astype(np.int64)
    for cs in (5, 10, 20):
        got = pl.DataFrame({"e_km": e.astype(np.int16), "n_km": n.astype(np.int16)}).select(
            stats.cluster_expr(cs)
        )
        assert np.array_equal(got.to_series().to_numpy(), stats.cluster_index(e, n, cs)[0])


def test_eta_squared_pure_class_effect() -> None:
    # kaks klassi, ühtlane sisemine väärtus -> η² = 1
    tbl = pl.DataFrame(
        {"cls": [0, 1], "n": [100, 100], "sum": [100 * 1.0, 100 * 3.0], "sumsq": [100 * 1.0, 100 * 9.0]}
    )
    assert stats.eta_squared(tbl, np.array([0, 1])) == pytest.approx(1.0)
    # sama grupp -> η² = 0
    assert stats.eta_squared(tbl, np.array([0, 0])) == pytest.approx(0.0)


def test_median_estimates_match_brute_force(tmp_path) -> None:  # noqa: ANN001
    """Mediaanipõhised hinnangud (metoodika v2) võrduvad otse toorpikslitest arvutatuga."""
    from oks import aggregate, pipeline

    used = _used().with_columns(pl.lit("A").alias("seisund_algne"))
    u = stats.make_units(used)
    rng = np.random.default_rng(2)
    e_l, n_l, k_l, x_l = [], [], [], []
    shift = {1: 0.0, 2: 1.5, 3: 4.0}  # uld -> lisand (hea suurim)
    for e in range(400, 430):
        for n in range(6400, 6402):
            for k, uld in zip(used["kood"], used["uld"], strict=True):
                m = int(rng.integers(90, 160))
                x = np.round(rng.gamma(2, 2, m) + shift[uld], 1)
                x[rng.random(m) < 0.3] = 0
                e_l.append(np.full(m, e))
                n_l.append(np.full(m, n))
                k_l.append(np.full(m, k))
                x_l.append(x)
    ex, nx, kx, xv = (np.concatenate(a) for a in (e_l, n_l, k_l, x_l))
    vdir = tmp_path / "val"
    vdir.mkdir()
    grp = pipeline.groupings(used)
    blk = []
    for n_km in np.unique(nx):
        s = nx == n_km
        aggregate.value_counts(ex[s], kx[s], xv[s]).with_columns(
            pl.lit(n_km, dtype=pl.Int16).alias("n_km")
        ).write_parquet(vdir / f"n{n_km}.parquet")
        for g, arr in grp.items():
            m = aggregate.segment_medians(ex[s], arr[kx[s]], xv[s])
            blk.append(
                pl.DataFrame(m).with_columns(pl.lit(g).alias("grouping"), pl.lit(int(n_km)).alias("n_km"))
            )
    p = stats.Params(n_boot=200, min_strata=20)
    res = stats.analyse_layer_median(pl.concat(blk), vdir, u, used, 10.0, p)
    eco1_hea = np.isin(kx, [10110])
    cell = (
        res["lahtrid"]
        .filter(
            (pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 1) & (pl.col("state") == "hea")
        )
        .row(0, named=True)
    )
    assert cell["median"] == np.median(xv[eco1_hea])
    assert cell["median_nz"] == np.median(xv[eco1_hea & (xv != 0)])
    # paaritatud: stratum = plokk x alam; d = mediaan_hea - mediaan_vilets; w = na nb / (na + nb)
    num = den = 0.0
    for e in range(400, 430):
        for n in range(6400, 6402):
            b = (ex == e) & (nx == n)
            xa, xb = xv[b & (kx == 10141)], xv[b & (kx == 10110)]
            if xa.size >= 100 and xb.size >= 100:
                w = xa.size * xb.size / (xa.size + xb.size)
                num += w * (np.median(xb) - np.median(xa))
                den += w
    pr = (
        res["paarid"]
        .filter(
            (pl.col("unit_level") == "alam")
            & (pl.col("unit_code") == 10100)
            & (pl.col("pair") == "vilets→hea")
        )
        .row(0, named=True)
    )
    assert pr["delta_m_med"] == pytest.approx(num / den, abs=1e-12)
    assert pr["delta_u_med"] == np.median(xv[kx == 10110]) - np.median(xv[kx == 10141])
    assert np.isfinite(pr["ci_u_med_lo"]) and pr["ci_u_med_lo"] <= pr["ci_u_med_hi"]
    kl = res["klassid"].filter(pl.col("cls") == 2).row(0, named=True)
    assert kl["median"] == np.median(xv[kx == 10141])
    assert not res["algklassid"].is_empty()
