"""Lähtekasu tabelite (``kaasnev``), indikaatorite ja nõuete järjepidevuse testid."""

from __future__ import annotations

import polars as pl
import pytest

from oks import catalog, indikaatorid, kaasnev, nouded


def _stats(rows: list[tuple[int, int, int, int, int, int, float, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "layer_id": "x",
                "kood": k,
                "n_total": nt,
                "n_valid": nv,
                "n_zero": nz,
                "n_pos": npos,
                "n_neg": nn,
                "sum": s,
                "sumsq": ss,
            }
            for k, nt, nv, nz, npos, nn, s, ss in rows
        ]
    )


def _classes() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "kood": [1, 2, 3],
            "okosusteem_kood": [3, 3, 3],
            "okosusteem": ["Metsad"] * 3,
            "alam_kood": [100, 100, 200],
            "tuup": ["Palumets", "Palumets", "Laanemets"],
            "uld": [1, 1, 1],
            "seisund_nimi": ["hea"] * 3,
            "pindala_ha": [10.0, 30.0, 5.0],
        }
    )


def test_mean_includes_zeros_and_pools_classes() -> None:
    """Lähtekasu loogikakontroll: 25 ha 100-st mustikat -> keskmine kogu klassi pindala kohta."""
    # kaks klassi: 40 pikslit (10 positiivset, sum 100) + 60 pikslit (15 positiivset, sum 150)
    st = _stats([(1, 40, 40, 30, 10, 0, 100.0, 1000.0), (2, 60, 60, 45, 15, 0, 150.0, 1500.0)])
    out = kaasnev.type_state(st, _classes().filter(pl.col("alam_kood") == 100))
    row = out.row(0, named=True)
    assert row["mean"] == pytest.approx(250 / 100)
    assert row["esineb_osa"] == pytest.approx(0.25)
    assert row["staatus"] == kaasnev.STATUS_OK
    assert row["pindala_ha"] == pytest.approx(40.0)


def test_status_rules() -> None:
    cls = _classes()
    st = _stats(
        [
            (1, 1000, 1000, 995, 5, 0, 5.0, 5.0),  # 0,5 % nullist erinevat: ei paku
            (2, 1000, 20, 0, 20, 0, 40.0, 80.0),  # katvus 2 %: ei hinnatud
            (3, 1000, 600, 0, 600, 0, 300.0, 200.0),  # katvus 60 %: osaline
        ]
    )
    out = kaasnev.summarise(st, cls, ["alam_kood", "tuup"]).sort("alam_kood")
    by = {(r["alam_kood"], r["staatus"]) for r in out.iter_rows(named=True)}
    # alam 100: klassid 1 ja 2 koos: valid 1020/2000 (51 %), nonzero 25/1020 (2,5 %): osaline
    assert (100, kaasnev.STATUS_PARTIAL) in by
    assert (200, kaasnev.STATUS_PARTIAL) in by
    only1 = kaasnev.summarise(st.filter(pl.col("kood") == 1), cls, ["alam_kood"])
    assert only1["staatus"].to_list() == [kaasnev.STATUS_NONE]
    only2 = kaasnev.summarise(st.filter(pl.col("kood") == 2), cls, ["alam_kood"])
    assert only2["staatus"].to_list() == [kaasnev.STATUS_MISSING]


def test_big_classes_weight_by_valid_pixels_and_skip_other() -> None:
    cls = pl.concat(
        [
            _classes(),
            pl.DataFrame(
                {
                    "kood": [4],
                    "okosusteem_kood": [6],
                    "okosusteem": ["Asustus ja muu"],
                    "alam_kood": [600],
                    "tuup": ["Veekogud"],
                    "uld": [5],
                    "seisund_nimi": ["hindamata"],
                    "pindala_ha": [99.0],
                }
            ),
        ]
    )
    st = _stats(
        [
            (1, 100, 100, 0, 100, 0, 100.0, 100.0),
            (3, 300, 300, 0, 300, 0, 900.0, 2700.0),
            (4, 10, 10, 0, 10, 0, 10.0, 10.0),
        ]
    )
    big = kaasnev.big_classes(st, cls)
    assert set(big["okosusteem"].to_list()) == {"Metsad"}  # „muud“ ei liideta
    hea = big.filter(pl.col("seisund_nimi") == "hea").row(0, named=True)
    assert hea["mean"] == pytest.approx((100 + 900) / 400)


def test_indicator_layers_are_unique_and_known() -> None:
    layers = indikaatorid.all_layers()
    assert len(layers) == len(set(layers))
    cat = pl.read_csv(catalog.Path(__file__).parents[1] / "data" / "teenused.csv")
    known = set(cat["id"].to_list())
    missing = [x for x in layers if x not in known]
    assert not missing, missing


def test_every_evaluated_layer_belongs_to_an_indicator() -> None:
    cat = catalog.build_catalogue(
        catalog.Path(__file__).parents[1] / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        catalog.Path(__file__).parents[1] / "data/arhiiv_failid.csv",
    )
    ev = catalog.evaluated(cat).filter(pl.col("fail").is_not_null())["id"].to_list()
    orphans = [x for x in ev if x not in indikaatorid.LAYER_TO_INDICATOR]
    assert not orphans, orphans


def test_zero_values_policy() -> None:
    assert catalog.zero_values("seened_hind_2022_10m", 0.0) == (0.0,)
    assert catalog.zero_values("ohusaaste_puhverdusvoime_2022_5m", 0.0) == (0.0, 255.0)
    assert catalog.zero_values("mustikad_pohlad_saagikus_2020_10m", 9999.0) == ()
    # metoodika v2: NoData on kehtiv null kõigis kihtides peale kolme erandi
    assert catalog.zero_values("c_tonn_per_ha_final_2022_10m", -1.0) == (-1.0,)
    assert catalog.zero_values("seened_saagikus_2020_10m", -3.399999952144364e38) == (-3.399999952144364e38,)
    assert catalog.zero_values("pohlad_saagikus_2020_10m", -128.0) == ()
    assert catalog.zero_values("mustikad_pohlad_hind_2022_10m", 9999.0) == ()
    assert catalog.zero_values("kasemahl_saagikus_2020_10m", -3.402823060737097e38) == ()
    assert catalog.zero_values("elupaigahuve_pakkumine_2022_10m", None) == ()


def test_strength_scale() -> None:
    assert indikaatorid.strength(0.05) == "nõrk"
    assert indikaatorid.strength(-0.2) == "keskmine"
    assert indikaatorid.strength(0.8) == "tugev"
    assert indikaatorid.strength(None) == ""


def test_requirements_have_valid_status() -> None:
    allowed = {nouded.DONE, nouded.PART, nouded.WAIT, nouded.TODO}
    ids = [r["id"] for r in nouded.REQUIREMENTS]
    assert len(ids) == len(set(ids))
    assert all(r["staatus"] in allowed for r in nouded.REQUIREMENTS)


def test_forest_split_into_dry_and_wet() -> None:
    cls = pl.DataFrame(
        {
            "kood": [1, 2, 3],
            "okosusteem_kood": [3, 3, 3],
            "okosusteem": ["Metsad"] * 3,
            "alam_kood": [kaasnev.DRY_FOREST[0], kaasnev.WET_FOREST[0], 31100],
            "tuup": ["Salumets", "Soovikumets", "Muu (metsa)kooslus"],
            "uld": [1, 1, 1],
            "seisund_nimi": ["hea"] * 3,
            "pindala_ha": [10.0, 20.0, 5.0],
        }
    )
    st = _stats(
        [
            (1, 100, 100, 0, 100, 0, 1000.0, 1.0),
            (2, 100, 100, 0, 100, 0, 200.0, 1.0),
            (3, 100, 100, 0, 100, 0, 0.0, 0.0),
        ]
    )
    big = kaasnev.big_classes(st, cls).filter(pl.col("seisund_nimi") == "hea")
    by = {r["okosusteem"]: r["mean"] for r in big.iter_rows(named=True)}
    assert by["Kuivad metsad"] == pytest.approx(10.0)
    assert by["Märjad metsad"] == pytest.approx(2.0)
    assert by["Metsad"] == pytest.approx(1200 / 300)  # „Muu (metsa)kooslus“ ainult metsa kogus
    assert not set(kaasnev.DRY_FOREST) & set(kaasnev.WET_FOREST)
    assert (
        kaasnev.DISPLAY_ORDER[3]
        < kaasnev.DISPLAY_ORDER[31]
        < kaasnev.DISPLAY_ORDER[32]
        < kaasnev.DISPLAY_ORDER[4]
    )


def test_median_table_pools_pixels_not_class_medians(tmp_path) -> None:  # noqa: ANN001
    """Rühma mediaan arvutatakse klasside pikslite ühendist (mitte klasside mediaanidest)."""
    import numpy as np

    from oks import aggregate, median

    a = np.array([0, 0, 0, 1, 9], dtype=np.float32)  # klass 1: mediaan 0
    b = np.array([5, 6, 7], dtype=np.float32)  # klass 2: mediaan 6
    x = np.concatenate([a, b])
    k = np.array([1] * a.size + [2] * b.size)
    vdir = tmp_path / "val"
    vdir.mkdir()
    aggregate.value_counts(np.full(x.size, 400), k, x).with_columns(
        pl.lit(6500, dtype=pl.Int16).alias("n_km")
    ).write_parquet(vdir / "n6500.parquet")
    group = pl.DataFrame({"kood": [1, 2], "g": ["x", "x"]})
    out = kaasnev.median_table(median.ValueTable.load(vdir), group, ["g"]).row(0, named=True)
    assert out["median"] == np.median(x)  # 3.0, mitte (0 + 6) / 2
    assert out["median_nz"] == np.median(x[x != 0])
