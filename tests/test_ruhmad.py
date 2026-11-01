"""Metoodika v3: kuivad ja märjad metsad statistilise analüüsi ühikuna (``oks.ruhmad``).

Sünteetiline andmestik: mets (eco 3) kolme alamökosüsteemiga (30100 kuiv, 30200 märg, 31100 muu) ja rohumaa
(eco 1, 10100), igaühel kolm seisundit. Kontrollitakse, et rühma hinnangud on samad mis v2 ökosüsteemi/alamökosüsteemi
hinnangud, kui rühm koosneb samadest stratumitest, ja et metsa hinnang laguneb rühmadeks.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from oks import aggregate, analysis, kaasnev, pipeline, ruhmad, stats

ALAMS = {10100: 1, 30100: 3, 30200: 3, 31100: 3}  # alam -> ökosüsteem
SUFFIX = {1: 10, 2: 30, 3: 41}  # uld -> koodi lõpp
STATE_NAME = {1: "hea", 2: "keskmine", 3: "vilets"}


def _used() -> pl.DataFrame:
    rows = []
    i = 0
    for alam, eco in ALAMS.items():
        for uld in (1, 2, 3):
            rows.append((i, alam + SUFFIX[uld], alam, eco, uld, "A", STATE_NAME[uld], 1.0 + i))
            i += 1
    return pl.DataFrame(
        rows,
        schema=[
            "idx",
            "kood",
            "alam_kood",
            "okosusteem_kood",
            "uld",
            "seisund_algne",
            "seisund",
            "pindala_km2",
        ],
        orient="row",
    ).with_columns(pl.col("idx").cast(pl.UInt32))


@pytest.fixture(scope="module")
def data(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """Pikslid -> sagedustabel, plokimediaanid ja plokisummad; v2 ja rühmaühikute analüüs."""
    tmp = tmp_path_factory.mktemp("ruhmad")
    used = _used()
    rng = np.random.default_rng(7)
    # alamökosüsteemi ja seisundi efekt (vilets, keskmine, hea); kuivas ja märjas metsas erinev suund
    effect = {10100: (0, 1, 2), 30100: (0, 2, 5), 30200: (3, 2, 0), 31100: (0, 1, 1)}
    e_l, n_l, k_l, x_l = [], [], [], []
    for e in range(400, 430):
        for n in range(6400, 6404):
            bg = rng.normal(0, 2)
            for r in used.iter_rows(named=True):
                if r["alam_kood"] == 31100 and rng.random() < 0.5:
                    continue  # muu kooslus esineb hõredamalt
                m = int(rng.integers(100, 180))
                x = np.round(rng.gamma(2, 2, m) + 10 + bg + effect[r["alam_kood"]][3 - r["uld"]], 1)
                x[rng.random(m) < 0.2] = 0
                e_l.append(np.full(m, e))
                n_l.append(np.full(m, n))
                k_l.append(np.full(m, r["kood"]))
                x_l.append(x)
    ex, nx, kx, xv = (np.concatenate(a) for a in (e_l, n_l, k_l, x_l))
    vdir = tmp / "val"
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
    blkmed = pl.concat(blk)
    k2i = dict(zip(used["kood"].to_list(), used["idx"].to_list(), strict=True))
    cls = np.array([k2i[int(k)] for k in kx])
    tbl = (
        pl.DataFrame({"e_km": ex, "n_km": nx, "cls": cls, "x": xv})
        .group_by("e_km", "n_km", "cls")
        .agg(pl.len().alias("n"), pl.col("x").sum().alias("sum"), (pl.col("x") ** 2).sum().alias("sumsq"))
        .with_columns(
            pl.col("e_km").cast(pl.Int16),
            pl.col("n_km").cast(pl.Int16),
            pl.col("cls").cast(pl.Int16),
            pl.col("n").cast(pl.Int32),
        )
        .sort("e_km", "n_km", "cls")
    )
    u = stats.make_units(used)
    ug = ruhmad.make_group_units(used)
    p = stats.Params(n_boot=200, min_strata=20)
    W = stats._boot_weights(
        stats.cluster_index(np.array([stats.E_MIN]), np.array([stats.N_MIN]), 10)[1], 200, p.seed
    )
    return {
        "used": used,
        "vdir": vdir,
        "blkmed": blkmed,
        "tbl": tbl,
        "pix": (ex, nx, kx, xv),
        "p": p,
        "W": W,
        "u": u,
        "ug": ug,
        "med_u": stats.analyse_layer_median(blkmed, vdir, u, used, 10.0, p, W),
        "med_g": stats.analyse_layer_median(
            ruhmad.group_blkmed(blkmed, vdir, used), vdir, ug, used, 10.0, p, W
        ),
        "mean_u": stats.analyse_layer(tbl, u, 10.0, p, W),
        "mean_g": stats.analyse_layer(tbl, ug, 10.0, p, W),
    }


def _row(df: pl.DataFrame, level: str, code: int, pair: str = "vilets→hea") -> dict[str, object]:
    return df.filter(
        (pl.col("unit_level") == level) & (pl.col("unit_code") == code) & (pl.col("pair") == pair)
    ).row(0, named=True)


def _same(a: dict[str, object], b: dict[str, object], cols: list[str]) -> None:
    for c in cols:
        x, y = a[c], b[c]
        if isinstance(x, float) and np.isnan(x):
            assert isinstance(y, float) and np.isnan(y), c
        else:
            assert y == pytest.approx(x, rel=1e-9, abs=1e-12), c


MED_COLS = [
    "median_a",
    "median_b",
    "delta_m_med",
    "rel_m_med",
    "ci_m_med_lo",
    "ci_m_med_hi",
    "p_m_med",
    "delta_u_med",
    "ci_u_med_lo",
    "ci_u_med_hi",
    "p_u_med",
    "mw_p_med",
    "level_a_m_med",
    "level_b_m_med",
    "sum_w_m_med",
]
MEAN_COLS = [
    "n_a",
    "n_b",
    "mean_a",
    "mean_b",
    "delta_m",
    "ci_m_lo",
    "ci_m_hi",
    "p_m",
    "n_strata",
    "n_clusters_m",
]


def test_group_definition_single_source() -> None:
    assert {g.code: (g.name, g.alam_codes) for g in ruhmad.GROUPS.values()} == kaasnev.FOREST_SPLIT
    # koosseis (otsus K1, 2026-11-01) ja v2 tulemustabeli jaotus on samad
    assert kaasnev.FOREST_SPLIT == {
        31: ("Kuivad metsad", (30100, 30500, 30600, 30700, 31000)),
        32: ("Märjad metsad", (30200, 30300, 30400, 30800, 30900)),
    }
    assert kaasnev.DRY_FOREST == ruhmad.DRY_FOREST and kaasnev.WET_FOREST == ruhmad.WET_FOREST
    alams = [a for g in ruhmad.GROUPS.values() for a in g.alam_codes]
    assert len(alams) == len(set(alams))
    assert not {31100, 31200} & set(alams)
    assert not set(ruhmad.GROUPS) & {1, 2, 3, 4, 5, 6}


def test_overlapping_groups_rejected() -> None:
    bad = {91: ruhmad.Group(91, "a", 3, (30100,)), 92: ruhmad.Group(92, "b", 3, (30100,))}
    with pytest.raises(ValueError, match="kahes rühmas"):
        ruhmad.make_group_units(_used(), bad)


def test_make_group_units(data: dict[str, object]) -> None:
    ug = data["ug"]
    assert isinstance(ug, stats.Units)
    used = _used()
    assert ug.eco_codes == (31, 32)
    assert ug.alam_codes == (30100, 30200)
    idx = used["idx"].to_numpy()
    alam = used["alam_kood"].to_numpy()
    assert set(ug.cls_eco[idx[alam == 30100]]) == {0}
    assert set(ug.cls_eco[idx[alam == 30200]]) == {1}
    assert set(ug.cls_eco[idx[np.isin(alam, [31100, 10100])]]) == {-1}
    np.testing.assert_array_equal(ug.cls_state, data["u"].cls_state)  # type: ignore[attr-defined]


def test_group_block_medians_exact(data: dict[str, object]) -> None:
    """Rühma plokimediaanid sagedustabelist = ``segment_medians`` toorpikslitel."""
    ex, nx, kx, xv = data["pix"]  # type: ignore[misc]
    kg = ruhmad.kood_groups(_used())
    garr = np.full(65536, -1, dtype=np.int64)
    garr[kg["kood"].to_numpy()] = kg["group"].to_numpy()
    want = []
    for n_km in np.unique(nx):
        s = (nx == n_km) & (garr[kx] >= 0)
        m = aggregate.segment_medians(ex[s], garr[kx[s]], xv[s])
        want.append(pl.DataFrame(m).with_columns(pl.lit(int(n_km)).alias("n_km")))
    w = pl.concat(want).sort("n_km", "e_km", "group")
    got = ruhmad.block_medians(data["vdir"], kg).sort("n_km", "e_km", "group")  # type: ignore[arg-type]
    assert got.height == w.height
    for c in ("e_km", "group", "n", "n_nz"):
        assert got[c].to_list() == w[c].cast(pl.Int64).to_list(), c
    np.testing.assert_array_equal(got["median"].to_numpy(), w["median"].to_numpy())
    np.testing.assert_array_equal(got["median_nz"].to_numpy(), w["median_nz"].to_numpy())
    assert set(got["grouping"].unique().to_list()) == {"eco"}


@pytest.mark.parametrize("pair", stats.PAIR_NAMES)
def test_group_of_one_alam_equals_alam(data: dict[str, object], pair: str) -> None:
    """Sünteetilises andmestikus on igas rühmas üks alamökosüsteem: rühma read = alam-read (v2)."""
    for gcode, alam in ((31, 30100), (32, 30200)):
        _same(
            _row(data["med_u"]["paarid"], "alam", alam, pair),
            _row(data["med_g"]["paarid"], "okosusteem", gcode, pair),
            MED_COLS,
        )  # type: ignore[index]
        _same(
            _row(data["mean_u"]["paarid"], "alam", alam, pair),
            _row(data["mean_g"]["paarid"], "okosusteem", gcode, pair),
            MEAN_COLS,
        )  # type: ignore[index]


def test_group_of_all_alams_equals_eco(data: dict[str, object]) -> None:
    """Rühm, mis sisaldab ökosüsteemi kõiki alamökosüsteeme, annab ökosüsteemi (v2) read."""
    used, vdir, blkmed, p, W, tbl = (data[k] for k in ("used", "vdir", "blkmed", "p", "W", "tbl"))
    allg = {39: ruhmad.Group(39, "kogu mets", 3, (30100, 30200, 31100))}
    ug = ruhmad.make_group_units(used, allg)  # type: ignore[arg-type]
    blk_g = pl.concat(
        [
            blkmed.filter(pl.col("grouping") == "alam").select(  # type: ignore[union-attr]
                [
                    pl.col(c).cast(t)
                    for c, t in ruhmad.block_medians(vdir, ruhmad.kood_groups(used, allg)).schema.items()
                ]  # type: ignore[arg-type]
            ),
            ruhmad.block_medians(vdir, ruhmad.kood_groups(used, allg)),  # type: ignore[arg-type]
        ]
    )
    med = stats.analyse_layer_median(blk_g, vdir, ug, used, 10.0, p, W)  # type: ignore[arg-type]
    mean = stats.analyse_layer(tbl, ug, 10.0, p, W)  # type: ignore[arg-type]
    for pair in stats.PAIR_NAMES:
        _same(
            _row(data["med_u"]["paarid"], "okosusteem", 3, pair),
            _row(med["paarid"], "okosusteem", 39, pair),
            MED_COLS,
        )  # type: ignore[index]
        _same(
            _row(data["mean_u"]["paarid"], "okosusteem", 3, pair),
            _row(mean["paarid"], "okosusteem", 39, pair),
            MEAN_COLS,
        )  # type: ignore[index]


@pytest.mark.parametrize("pair", stats.PAIR_NAMES)
def test_forest_decomposition(data: dict[str, object], pair: str) -> None:
    """Δ_mets = Σ W_g·Δ_g / Σ W_g üle kuiva ja märja metsa ning muu koosluse (W = kaalude summa)."""
    med_u, med_g = data["med_u"]["paarid"], data["med_g"]["paarid"]  # type: ignore[index]
    parts = [
        _row(med_g, "okosusteem", 31, pair),
        _row(med_g, "okosusteem", 32, pair),
        _row(med_u, "alam", 31100, pair),
    ]
    num = sum(r["sum_w_m_med"] * r["delta_m_med"] for r in parts)  # type: ignore[operator]
    den = sum(r["sum_w_m_med"] for r in parts)  # type: ignore[misc]
    forest = _row(med_u, "okosusteem", 3, pair)
    assert forest["delta_m_med"] == pytest.approx(num / den, rel=1e-12)
    assert forest["sum_w_m_med"] == pytest.approx(den, rel=1e-12)
    # stratumite arv: mets = kuiv + märg + muu
    mean_u, mean_g = data["mean_u"]["paarid"], data["mean_g"]["paarid"]  # type: ignore[index]
    n = sum(int(_row(mean_g, "okosusteem", g, pair)["n_strata"]) for g in (31, 32))  # type: ignore[call-overload]
    n += int(_row(mean_u, "alam", 31100, pair)["n_strata"])  # type: ignore[call-overload]
    assert int(_row(mean_u, "okosusteem", 3, pair)["n_strata"]) == n  # type: ignore[call-overload]


def test_dry_and_wet_differ_in_synthetic_data(data: dict[str, object]) -> None:
    """Sünteetiline efekt on kuivas metsas positiivne ja märjas negatiivne; rühmad näitavad seda, mets mitte selgelt."""
    med_g = data["med_g"]["paarid"]  # type: ignore[index]
    assert _row(med_g, "okosusteem", 31)["delta_m_med"] > 0  # type: ignore[operator]
    assert _row(med_g, "okosusteem", 32)["delta_m_med"] < 0  # type: ignore[operator]


def test_levels_consistent(data: dict[str, object]) -> None:
    """Paaritatud tasemed: level_b − level_a = Δ; Δ % = Δ / |level_a|."""
    pr = data["med_u"]["paarid"].filter(pl.col("delta_m_med").is_not_nan())  # type: ignore[index]
    assert pr.height > 0
    a, b, d = (pr[c].to_numpy() for c in ("level_a_m_med", "level_b_m_med", "delta_m_med"))
    np.testing.assert_allclose(b - a, d, rtol=1e-9, atol=1e-12)
    rel = pr["rel_m_med"].to_numpy()
    ok = np.abs(a) > 1e-12
    np.testing.assert_allclose(rel[ok], d[ok] / np.abs(a[ok]), rtol=1e-12)


def test_fdr_groups_separate() -> None:
    """Rühmade read ei muuda ökosüsteemi ja alamökosüsteemi q-väärtusi (eraldi FDR-perekond)."""
    rng = np.random.default_rng(3)

    def frame(level: str, n: int) -> pl.DataFrame:
        p = rng.uniform(0, 0.2, n)
        return pl.DataFrame(
            {
                "unit_level": [level] * n,
                "unit_code": list(range(n)),
                "pair": ["vilets→hea"] * n,
                **{c: p for c in ("p_m", "p_u", "wilcoxon_p", "p_m_med", "p_u_med", "wilcoxon_p_med")},
                **{c: rng.normal(size=n) for c in ("delta_m", "delta_u", "delta_m_med", "delta_u_med")},
            }
        )

    v2 = pl.concat([frame("okosusteem", 30), frame("alam", 80)])
    v3 = pl.concat([v2, frame(ruhmad.LEVEL, 12)])
    keys = ["unit_level", "unit_code", "pair"]
    a = analysis.add_fdr(v2, 0.05).sort(keys)
    b = analysis.add_fdr(v3, 0.05).filter(pl.col("unit_level") != ruhmad.LEVEL).sort(keys)
    for c in ("q_m", "q_u", "q_m_med", "q_u_med", "q_wilcoxon_med", "oluline_m_med", "kooskolas_med"):
        assert a[c].to_list() == b[c].to_list(), c
    g = analysis.add_fdr(v3, 0.05).filter(pl.col("unit_level") == ruhmad.LEVEL)
    np.testing.assert_allclose(g["q_m_med"].to_numpy(), stats.bh_fdr(g["p_m_med"].to_numpy()))


def test_relabel_keeps_only_group_rows(data: dict[str, object]) -> None:
    r = ruhmad.relabel(data["med_g"]["paarid"])  # type: ignore[index]
    assert set(r["unit_level"].unique().to_list()) == {ruhmad.LEVEL}
    assert set(r["unit_code"].unique().to_list()) == {31, 32}


def test_assert_same_rows_detects_difference(data: dict[str, object]) -> None:
    a = data["mean_u"]["paarid"]  # type: ignore[index]
    b = data["mean_g"]["paarid"]  # type: ignore[index]
    analysis._assert_same_rows(a, b, ["unit_level", "unit_code", "pair"], "test")  # alam-read samad
    bad = b.with_columns(
        pl.when(pl.col("unit_level") == "alam")
        .then(pl.col("delta_m") + 1e-3)
        .otherwise(pl.col("delta_m"))
        .alias("delta_m")
    )
    with pytest.raises(RuntimeError, match="delta_m"):
        analysis._assert_same_rows(a, bad, ["unit_level", "unit_code", "pair"], "test")


def test_group_unit_table(data: dict[str, object]) -> None:
    used = _used()
    t = analysis.group_unit_table(used, data["ug"])  # type: ignore[arg-type]
    assert t["unit_level"].to_list() == [ruhmad.LEVEL] * 2
    assert t["unit_code"].to_list() == [31, 32]
    assert set(t["eco_code"].to_list()) == {3}
    dry = used.filter(pl.col("alam_kood") == 30100)
    for s in stats.STATES:
        assert t.filter(pl.col("unit_code") == 31)[f"pind_{s}"].item() == pytest.approx(
            dry.filter(pl.col("seisund") == s)["pindala_km2"].sum()
        )


def test_distribution_group_is_sum_of_alams(tmp_path: Path, data: dict[str, object]) -> None:
    used = _used()
    rng = np.random.default_rng(5)
    cls = np.repeat(used["idx"].to_numpy().astype(np.int16), 4)
    pl.DataFrame(
        {
            "cls": cls,
            "bin": np.tile(np.arange(4, dtype=np.int16), used.height),
            "n": rng.integers(1, 99, cls.size),
        }
    ).write_parquet(tmp_path / "k__hist.parquet")
    (tmp_path / "k__hist.json").write_text(json.dumps({"n_bins": 3}), encoding="utf-8")
    d, _ = analysis.distributions(data["u"], ["k"], tmp_path, ug=data["ug"])  # type: ignore[arg-type]
    for gcode, alam in ((31, 30100), (32, 30200)):
        g = d.filter((pl.col("unit_level") == ruhmad.LEVEL) & (pl.col("unit_code") == gcode)).sort(
            "state", "bin"
        )
        a = d.filter((pl.col("unit_level") == "alam") & (pl.col("unit_code") == alam)).sort("state", "bin")
        assert g.height > 0 and g["n"].to_list() == a["n"].to_list()
    # ilma rühmadeta on väljund sama mis v2-s (rühmaread puuduvad)
    d2, _ = analysis.distributions(data["u"], ["k"], tmp_path)  # type: ignore[arg-type]
    assert d2.sort(d2.columns).equals(d.filter(pl.col("unit_level") != ruhmad.LEVEL).sort(d2.columns))


def test_group_cells_match_results_table_median(data: dict[str, object]) -> None:
    """Rühma seisundi mediaan statistilises analüüsis = tulemustabeli (``kaasnev.median_table``) mediaan."""
    from oks import median

    used = _used()
    vt = median.ValueTable.load(data["vdir"])  # type: ignore[arg-type]
    grp = used.filter(pl.col("alam_kood").is_in(list(ruhmad.DRY_FOREST))).with_columns(pl.lit(31).alias("g"))
    want = kaasnev.median_table(vt, grp, ["g", "seisund"])
    cells = data["med_g"]["lahtrid"].filter(  # type: ignore[index]
        (pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 31)
    )
    for r in want.iter_rows(named=True):
        c = cells.filter(pl.col("state") == r["seisund"]).row(0, named=True)
        assert c["median"] == r["median"]
        assert c["median_nz"] == r["median_nz"]
