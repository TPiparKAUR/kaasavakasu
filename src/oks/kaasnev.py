"""Kaasneva kasu kvantitatiivsed tulemustabelid lähtekasu järgi.

Lähtekas (``docs/lahteulesanne.md``) nõuab:

* iga detailse ökosüsteemitüübi (nt rannaniit, loopealne, sinihelmikaniit) kohta teenuse keskväärtust
  seisundiklassides hea / keskmine / vilets (+ määramata) ja tüübi pindala (ha);
* suurte ökosüsteemide (mets, soo, niit, põld, rannik) väljundit pindalaga kaalutud keskmistena;
* keskväärtusi **kogu klassi pindala kohta**, nullid kaasa arvatud (loogikakontroll: kui 100 ha palumetsast
  25 ha-l kasvavad mustikad, arvutatakse keskmine kogu 100 ha kohta);
* märget, kui teenust tüübis ei esine, ja järeldust „ei paku“, kui seda on väga-väga vähe.

Sisendiks on klassitabelid (``pipeline.write_cls``): iga kihi kohta kõigi 264 baaskaardi klassi pikslite arv,
kehtivate, nullide, positiivsete ja negatiivsete arv ning Σx, Σx².
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from . import catalog, config, median

log = logging.getLogger(__name__)

#: Klass loetakse „teenust ei hinnatud“, kui kehtivate pikslite osa klassi pikslitest on väiksem.
COVER_MIN = 0.05
#: Märge „osaline kate“, kui kehtivate pikslite osa on väiksem (keskmine kehtib katvale osale).
COVER_FULL = 0.9

#: Baaskaardi seisundikoodid ``seisund_uldine`` (lähtekas, tabel „Taustaks“).
STATE_LABELS: dict[int, str] = {1: "hea", 2: "keskmine", 3: "vilets", 4: "määramata", 5: "hindamata"}
STATE_ORDER: list[str] = ["hea", "keskmine", "vilets", "määramata", "hindamata"]

#: Suured ökosüsteemid (lähtekasu „mets, soo, niit, põld, rannik“); asustus ja muu ei liideta.
BIG_CLASSES: dict[int, str] = {
    1: "Niit (rohumaad)",
    2: "Soo",
    3: "Mets",
    4: "Põld",
    5: "Rannik",
}
OTHER_CLASS = 6

#: Metsa jaotus kuivadeks ja märjaks metsaks (kommentaar lähtekasule): ``alam_kood``-id (baaskaardi ökosüsteemitüübid).
DRY_FOREST: tuple[int, ...] = (30100, 30500, 30600, 30700, 31000)  # salu-, palu-, laane-, loo-, nõmmemets
WET_FOREST: tuple[int, ...] = (
    30200,
    30300,
    30400,
    30800,
    30900,
)  # soovikumets, sambla-, rohu-, kõdusoomets, rabastuv
FOREST_SPLIT: dict[int, tuple[str, tuple[int, ...]]] = {
    31: ("Kuivad metsad", DRY_FOREST),
    32: ("Märjad metsad", WET_FOREST),
}
BIG_CLASSES.update({k: v[0] for k, v in FOREST_SPLIT.items()})
#: Kuvamisjärjekord (kuivad ja märjad metsad kohe metsa järel).
DISPLAY_ORDER: dict[int, float] = {1: 1.0, 2: 2.0, 3: 3.0, 31: 3.1, 32: 3.2, 4: 4.0, 5: 5.0}

STATUS_OK = "ok"
STATUS_PARTIAL = "osaline kate"
STATUS_NONE = "ei paku"
STATUS_MISSING = "ei hinnatud"
STATUS_MIXED = "uuriv (segumudel)"


def class_table() -> pl.DataFrame:
    """Kõik 264 baaskaardi klassi: kood, tüüp, ökosüsteem, seisund (märgend) ja pindala (ha)."""
    cls = pl.read_parquet(config.DERIVED / "klassid.parquet")
    return cls.with_columns(
        pl.col("uld").replace_strict(STATE_LABELS, return_dtype=pl.String).alias("seisund_nimi"),
        (pl.col("n_pix") * 25 / 10_000).alias("pindala_ha"),
    )


def load_class_stats(layer_ids: Sequence[str], blocks: Path | None = None) -> pl.DataFrame:
    """Loe kihtide klassitabelid üheks pikaks tabeliks (``layer_id`` + ``kood`` + loendused).

    Parameters
    ----------
    layer_ids
        Kihtide id-d.
    blocks
        Kaust (vaikimisi ``config.BLOCKS``).

    Returns
    -------
    pl.DataFrame
        Kihid, mille klassitabelit ei ole, jäetakse välja (hoiatus logis).
    """
    base = blocks or config.BLOCKS
    parts = []
    for lid in layer_ids:
        p = base / f"{lid}__cls.parquet"
        if not p.exists():
            log.warning("klassitabel puudub: %s", lid)
            continue
        parts.append(pl.read_parquet(p).with_columns(pl.lit(lid).alias("layer_id")))
    return pl.concat(parts) if parts else pl.DataFrame()


def summarise(stats: pl.DataFrame, group: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Liida klassitabelid gruppidesse ja arvuta keskmine, katvus, esinemise osa ja staatus.

    Parameters
    ----------
    stats
        Tulemus ``load_class_stats``-ist.
    group
        Tabel ``kood`` + ``keys`` (mis klass kuhu gruppi kuulub).
    keys
        Grupeerimisveerud (nt ``["okosusteem_kood", "alam_kood", "uld"]``).

    Returns
    -------
    pl.DataFrame
        Veerud ``keys`` + ``layer_id``, ``n_total``, ``n_valid``, ``kate`` (kehtivate osa), ``esineb_osa``
        (nullist erinevate osa kehtivatest), ``mean``, ``sd`` (pikslitasemel, kirjeldav), ``staatus``.
    """
    j = stats.join(group.select("kood", *keys), on="kood", how="inner")
    g = j.group_by([*keys, "layer_id"]).agg(
        pl.col("n_total").sum(),
        pl.col("n_valid").sum(),
        pl.col("n_zero").sum(),
        (pl.col("n_pos").sum() + pl.col("n_neg").sum()).alias("n_nonzero"),
        pl.col("sum").sum(),
        pl.col("sumsq").sum(),
    )
    g = g.with_columns(
        (pl.col("n_valid") / pl.col("n_total")).alias("kate"),
        pl.when(pl.col("n_valid") > 0).then(pl.col("n_nonzero") / pl.col("n_valid")).alias("esineb_osa"),
        pl.when(pl.col("n_valid") > 0).then(pl.col("sum") / pl.col("n_valid")).alias("mean"),
    ).with_columns(
        pl.when(pl.col("n_valid") > 0)
        .then(((pl.col("sumsq") / pl.col("n_valid") - pl.col("mean") ** 2).clip(lower_bound=0)).sqrt())
        .alias("sd")
    )
    return g.with_columns(
        pl.when((pl.col("n_valid") == 0) | (pl.col("kate") < COVER_MIN))
        .then(pl.lit(STATUS_MISSING))
        .when(pl.col("esineb_osa") < catalog.POSITIVE_MIN)
        .then(pl.lit(STATUS_NONE))
        .when(pl.col("kate") < COVER_FULL)
        .then(pl.lit(STATUS_PARTIAL))
        .otherwise(pl.lit(STATUS_OK))
        .alias("staatus")
    ).drop("n_nonzero", "n_zero", "sum", "sumsq")


def type_state(stats: pl.DataFrame, classes: pl.DataFrame) -> pl.DataFrame:
    """Teenuse keskväärtus iga detailse ökosüsteemitüübi ja seisundi kohta.

    Rida = ``(ökosüsteem, tüüp, seisund)``; ``pindala_ha`` on baaskaardi pindala (kõik klassi pikslid).
    """
    keys = ["okosusteem_kood", "okosusteem", "alam_kood", "tuup", "uld", "seisund_nimi"]
    area = classes.group_by(keys).agg(pl.col("pindala_ha").sum(), pl.len().alias("klasse"))
    s = summarise(stats, classes, keys)
    return area.join(s, on=keys, how="left").sort("okosusteem_kood", "alam_kood", "uld")


def big_classes(stats: pl.DataFrame, classes: pl.DataFrame) -> pl.DataFrame:
    """Suurte ökosüsteemide (niit, soo, mets, põld, rannik) pindalaga kaalutud keskmised seisundi kaupa.

    Kaal on kehtiv pindala (Σ pikslid), st tüübi keskmine kaalutakse sama tüübi kehtiva pindalaga; tüübid,
    kus teenust ei hinnatud, kaalu ei anna. Lisarida ``kokku (hea+keskmine+vilets)`` ja ``kokku (kõik)``.
    ``Asustus ja muu`` ei liideta (lähtekas: „Klassi MUUD pole vaja kokku liita“).
    Mets on lisaks jagatud kuivadeks (salu-, palu-, laane-, loo-, nõmmemets) ja märjaks (soovikumets, sambla-, rohu-,
    kõdusoomets, rabastuv mets) metsaks; „Muu (metsa)kooslus“ jääb ainult metsa kogusse.
    """
    keys = ["okosusteem_kood", "okosusteem", "seisund_nimi"]
    res = pl.concat([_big(stats, sub, keys) for sub in _big_groups(classes)])
    return (
        res.with_columns(
            pl.col("seisund_nimi")
            .replace_strict(
                {
                    s: i
                    for i, s in enumerate(
                        [*STATE_ORDER, "kokku (hea+keskmine+vilets)", "kokku (kõik seisundid)"]
                    )
                },
                default=99,
                return_dtype=pl.Int64,
            )
            .alias("_o")
        )
        .with_columns(
            pl.col("okosusteem_kood")
            .replace_strict(DISPLAY_ORDER, default=99.0, return_dtype=pl.Float64)
            .alias("_e")
        )
        .sort("_e", "_o")
        .drop("_o", "_e")
    )


def _big_groups(classes: pl.DataFrame) -> list[pl.DataFrame]:
    """Suurte ökosüsteemide klassirühmad: seisundi kaupa ja kaks „kokku“ rida (kuivad/märjad metsad eraldi)."""
    base = classes.filter(pl.col("okosusteem_kood").is_in([1, 2, 3, 4, 5]))
    forest = base.filter(pl.col("okosusteem_kood") == 3)
    split = [
        forest.filter(pl.col("alam_kood").is_in(list(codes))).with_columns(
            pl.lit(code).cast(forest.schema["okosusteem_kood"]).alias("okosusteem_kood"),
            pl.lit(name).alias("okosusteem"),
        )
        for code, (name, codes) in FOREST_SPLIT.items()
    ]
    base = pl.concat([base, *split])
    out = [base]
    for label, ulds in (
        ("kokku (hea+keskmine+vilets)", [1, 2, 3]),
        ("kokku (kõik seisundid)", [1, 2, 3, 4, 5]),
    ):
        out.append(base.filter(pl.col("uld").is_in(ulds)).with_columns(pl.lit(label).alias("seisund_nimi")))
    return out


def median_table(vt: median.ValueTable, group: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Täpne pikslimediaan iga rühma klasside ühendis (kõik pikslid ja nullist erinevad; metoodika v2).

    Valim on sama mis ``summarise`` keskväärtusel: kõik kehtivad pikslid, nullid kaasa arvatud.
    """
    rows = []
    for r in group.group_by(keys).agg(pl.col("kood")).iter_rows(named=True):
        ks = [int(k) for k in r["kood"]]
        _n, m = vt.median(ks)
        _nnz, mnz = vt.median(ks, nonzero=True)
        rows.append({**{k: r[k] for k in keys}, "median": m, "median_nz": mnz})
    return pl.DataFrame(rows, schema_overrides={k: group.schema[k] for k in keys})


def _big(stats: pl.DataFrame, classes: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    area = classes.group_by(keys).agg(pl.col("pindala_ha").sum())
    return area.join(summarise(stats, classes, keys), on=keys, how="left")


def build(layer_ids: Sequence[str], out_dir: Path | None = None) -> dict[str, pl.DataFrame]:
    """Koosta ja kirjuta tulemustabelid (``kaasnev_tuup_seisund``, ``kaasnev_suured``).

    Parameters
    ----------
    layer_ids
        Kihtide id-d (sama järjekord veergudes).
    out_dir
        Väljund (vaikimisi ``config.RESULTS``).
    """
    out_dir = out_dir or config.RESULTS
    classes = class_table()
    stats = load_class_stats(layer_ids)
    res = {"tuup_seisund": type_state(stats, classes), "suured": big_classes(stats, classes)}
    res = add_medians(res, classes, layer_ids)
    for k, v in res.items():
        v.write_parquet(out_dir / f"kaasnev_{k}.parquet")
    return res


def add_medians(
    res: dict[str, pl.DataFrame], classes: pl.DataFrame, layer_ids: Sequence[str], blocks: Path | None = None
) -> dict[str, pl.DataFrame]:
    """Lisa tulemustabelitele täpsed mediaanid (``median``, ``median_nz``) kihi sagedustabelist.

    Sagedustabel loetakse kihi kaupa üks kord (suurte kihtide mälu); kihid, millel see puudub, jäävad tühjaks.
    """
    base = blocks or config.BLOCKS
    ts_keys = ["okosusteem_kood", "okosusteem", "alam_kood", "tuup", "uld", "seisund_nimi"]
    big_keys = ["okosusteem_kood", "okosusteem", "seisund_nimi"]
    big_groups = pl.concat(_big_groups(classes))
    parts_t, parts_b = [], []
    for lid in layer_ids:
        vdir = base / f"{lid}__val"
        if not vdir.is_dir():
            log.warning("sagedustabel puudub: %s", lid)
            continue
        vt = median.ValueTable.load(vdir)
        parts_t.append(median_table(vt, classes, ts_keys).with_columns(pl.lit(lid).alias("layer_id")))
        parts_b.append(median_table(vt, big_groups, big_keys).with_columns(pl.lit(lid).alias("layer_id")))
        del vt
    out = dict(res)
    for name, parts, keys in (("tuup_seisund", parts_t, ts_keys), ("suured", parts_b, big_keys)):
        if parts:
            out[name] = res[name].join(pl.concat(parts), on=[*keys, "layer_id"], how="left")
    return out
