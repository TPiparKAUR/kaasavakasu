"""Metoodikate võrdlus: v1 (keskmised, NoData välja) → v2 (täpsed mediaanid, NoData = 0).

Erinevus jagatakse kaheks osaks:

1. **valimireeglid** – v1 keskmine vs v2 keskmine (sama statistik, muutunud on ainult see, millised pikslid
   loetakse ja millise väärtusega);
2. **statistik** – v2 keskmine vs v2 mediaan (sama valim, muutunud on ainult statistik).

Olulisuse muutus jagatakse samamoodi: v1 ``oluline_m`` → v2 ``oluline_m`` → v2 ``oluline_m_med``.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from . import catalog, kaasnev_export

#: Valimi muutuse põhjus kihi kaupa (järjekord = prioriteet).
CAUSES: dict[str, str] = {
    "madal_lahutus": "Madalama lahutusvõimega kiht viidi 10 m lahutusvõimele (v1-s oli ainult segumudel)",
    "vektor": "Vektorkiht: polügoonist väljas, tühi ja −1 loetakse nulliks; kattumisel suurim väärtus",
    "erand": "Erandkiht: NoData jääb välja nagu v1-s",
    "nodata0": "NoData loetakse nulliks (v1-s jäeti välja)",
    "sama": "Valim ei muutunud",
    "puudub": "Kihil ei ole tüübi × seisundi tabelit ühes versioonis",
}

#: Olulisuse muutuse klassid (ökosüsteemi ja alamökosüsteemi paarid).
SIG_CLASSES: tuple[str, ...] = (
    "jäi oluliseks, sama suund",
    "muutus oluliseks",
    "ei ole enam oluline",
    "suund muutus",
    "ei olnud ega ole oluline",
    "hinnang lisandus",
    "hinnang kadus",
    "andmeid ei piisa",
)

#: ``kate`` suurenemine, millest alates loetakse NoData nulliks muutmine valimit mõjutavaks.
KATE_TOL = 1e-3

_CELL_KEYS = ["layer_id", "okosusteem_kood", "okosusteem", "alam_kood", "tuup", "seisund_nimi"]
_PAIR_KEYS = ["layer_id", "unit_level", "unit_code", "pair"]


def cause(layer_id: str, vector: bool, kate_v1: float | None, kate_v2: float | None) -> str:
    """Kihi valimi muutuse põhjus (``CAUSES`` võti)."""
    if layer_id in kaasnev_export.LOW_RES_LAYERS:
        return "madal_lahutus"
    if kate_v1 is None or kate_v2 is None:
        return "puudub"
    if vector:
        return "vektor"
    if layer_id in catalog.NODATA_EXCLUDED:
        return "erand"
    if kate_v2 - kate_v1 > KATE_TOL:
        return "nodata0"
    return "sama"


def sig_class(o1: bool | None, s1: float | None, o2: bool | None, s2: float | None) -> str:
    """Olulisuse muutuse klass (``o`` = oluline, ``s`` = Δ märk; ``None`` = hinnangut ei ole või andmeid ei piisa)."""
    if o1 is None and o2 is None:
        return "andmeid ei piisa"
    if o1 is None:
        return "hinnang lisandus"
    if o2 is None:
        return "hinnang kadus"
    if o1 and o2:
        return "jäi oluliseks, sama suund" if (s1 or 0) * (s2 or 0) > 0 else "suund muutus"
    if o2:
        return "muutus oluliseks"
    if o1:
        return "ei ole enam oluline"
    return "ei olnud ega ole oluline"


def _rel(a: pl.Expr, b: pl.Expr) -> pl.Expr:
    """Suhteline muutus ``b / a − 1``; ``a == 0`` korral null (``b == 0``) või tühi."""
    return pl.when(a != 0).then(b / a - 1).when(b == 0).then(0.0).otherwise(None)


def cells(v1: Path, v2: Path) -> pl.DataFrame:
    """Tüüp × seisund lahtrid: v1 keskmine, v2 keskmine ja mediaan."""
    a = pl.read_parquet(v1 / "kaasnev_tuup_seisund.parquet").select(
        *_CELL_KEYS, pl.col("mean").alias("mean_v1"), pl.col("kate").alias("kate_v1")
    )
    b = pl.read_parquet(v2 / "kaasnev_tuup_seisund.parquet").select(
        *_CELL_KEYS,
        "pindala_ha",
        pl.col("mean").alias("mean_v2"),
        pl.col("median").alias("median_v2"),
        pl.col("kate").alias("kate_v2"),
        pl.col("esineb_osa").alias("esineb_osa_v2"),
    )
    return (
        a.join(b, on=_CELL_KEYS, how="full", coalesce=True)
        .with_columns(
            _rel(pl.col("mean_v1"), pl.col("mean_v2")).alias("rel_valim"),
            _rel(pl.col("mean_v2"), pl.col("median_v2")).alias("rel_statistik"),
        )
        .sort(_CELL_KEYS)
    )


def pairs(v1: Path, v2: Path) -> pl.DataFrame:
    """Seisundipaarid: v1 Δ keskmine → v2 Δ keskmine → v2 Δ mediaan ja olulisuse muutus.

    ``oluline_*`` on tühi, kui hinnangut ei ole või andmeid ei piisa (``enough_m`` väär).
    """
    a = pl.read_parquet(v1 / "paarid.parquet").select(
        *_PAIR_KEYS,
        pl.col("delta_m").alias("delta_v1"),
        pl.when(pl.col("enough_m")).then(pl.col("oluline_m")).alias("oluline_v1"),
    )
    b = pl.read_parquet(v2 / "paarid.parquet").select(
        *_PAIR_KEYS,
        pl.col("delta_m").alias("delta_v2_mean"),
        pl.when(pl.col("enough_m")).then(pl.col("oluline_m")).alias("oluline_v2_mean"),
        pl.col("delta_m_med").alias("delta_v2_med"),
        pl.when(pl.col("enough_m")).then(pl.col("oluline_m_med")).alias("oluline_v2_med"),
    )
    j = a.join(b, on=_PAIR_KEYS, how="full", coalesce=True)

    def cls(o1: str, d1: str, o2: str, d2: str) -> pl.Series:
        return pl.Series(
            [sig_class(r[o1], r[d1], r[o2], r[d2]) for r in j.select(o1, d1, o2, d2).iter_rows(named=True)],
            dtype=pl.String,
        )

    return j.with_columns(
        cls("oluline_v1", "delta_v1", "oluline_v2_mean", "delta_v2_mean").alias("muutus_valim"),
        cls("oluline_v2_mean", "delta_v2_mean", "oluline_v2_med", "delta_v2_med").alias("muutus_statistik"),
        cls("oluline_v1", "delta_v1", "oluline_v2_med", "delta_v2_med").alias("muutus_kokku"),
    ).sort(_PAIR_KEYS)


def layers(c: pl.DataFrame, p: pl.DataFrame, names: dict[str, str], vector: set[str]) -> pl.DataFrame:
    """Kihi kokkuvõte: põhjus, katvus, tüüpiline muutus ja olulisuse muutus ökosüsteemi tasandil."""
    w = pl.col("pindala_ha").fill_null(0.0)
    cs = c.group_by("layer_id").agg(
        ((pl.col("kate_v1") * w).sum() / w.filter(pl.col("kate_v1").is_not_null()).sum())
        .fill_nan(None)
        .alias("kate_v1"),
        ((pl.col("kate_v2") * w).sum() / w.filter(pl.col("kate_v2").is_not_null()).sum())
        .fill_nan(None)
        .alias("kate_v2"),
        pl.col("rel_valim").abs().median().alias("abs_rel_valim_mediaan"),
        pl.col("rel_statistik").abs().median().alias("abs_rel_statistik_mediaan"),
        ((pl.col("median_v2") == 0) & (pl.col("mean_v2") > 0)).mean().alias("osa_mediaan_null"),
    )
    eco = p.filter(pl.col("unit_level") == "okosusteem")
    ps = eco.group_by("layer_id").agg(
        pl.col("oluline_v1").fill_null(False).sum().alias("olulisi_v1"),
        pl.col("oluline_v2_mean").fill_null(False).sum().alias("olulisi_v2_keskmine"),
        pl.col("oluline_v2_med").fill_null(False).sum().alias("olulisi_v2_mediaan"),
        (pl.col("muutus_kokku") == "suund muutus").sum().alias("suund_muutus"),
        (pl.col("muutus_kokku") == "hinnang lisandus").sum().alias("hinnang_lisandus"),
    )
    out = cs.join(ps, on="layer_id", how="full", coalesce=True)
    return (
        out.with_columns(
            pl.col("layer_id").replace_strict(names, default=None).alias("nimi"),
            pl.Series(
                [
                    cause(r["layer_id"], r["layer_id"] in vector, r["kate_v1"], r["kate_v2"])
                    for r in out.select("layer_id", "kate_v1", "kate_v2").iter_rows(named=True)
                ],
                dtype=pl.String,
            ).alias("pohjus"),
        )
        .select("layer_id", "nimi", "pohjus", *[x for x in out.columns if x != "layer_id"])
        .sort("pohjus", "layer_id")
    )


def compare(v1: Path, v2: Path, names: dict[str, str], vector: set[str]) -> dict[str, pl.DataFrame]:
    """Koosta võrdlustabelid ``{"kihid", "lahtrid", "paarid"}``.

    Parameters
    ----------
    v1, v2
        v1 ja v2 tulemuste kaustad (``kaasnev_tuup_seisund.parquet``, ``paarid.parquet``).
    names
        ``{layer_id: nimi}``.
    vector
        Vektorkihtide id-d.
    """
    c = cells(v1, v2)
    p = pairs(v1, v2)
    return {"kihid": layers(c, p, names, vector), "lahtrid": c, "paarid": p}
