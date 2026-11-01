"""Metoodika v3: ökosüsteemi alamrühmad (kuivad ja märjad metsad) statistilise analüüsi ühikuna.

Rühm koosneb alamökosüsteemidest. Rühma hinnangud arvutatakse samade funktsioonidega kui ökosüsteemi hinnangud
(``stats.analyse_layer``, ``stats.analyse_layer_median``): ühikute objektis (``make_group_units``) on rühmad
ökosüsteemi kohal ja nende alamökosüsteemid alamökosüsteemi kohal. Paaritatud hinnangu stratum (1 km plokk ×
alamökosüsteem), kaal, bootstrap ja parameetrid on samad mis v2-s; muutub ainult see, milliste stratumite üle
koondatakse. Otsused: ``docs/metoodika_v3_otsused.md``.

Rühmade koosseis on ühes kohas (``GROUPS``) ja seda kasutavad ka lähtekasu tulemustabelid (``kaasnev``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

from . import stats

#: Analüüsitulemuste tase (``unit_level``) rühmadele.
LEVEL = "ruhm"


@dataclass(frozen=True)
class Group:
    """Ökosüsteemi alamrühm: kood, nimi, ökosüsteem ja alamökosüsteemide koodid (``alam_kood``)."""

    code: int
    name: str
    eco: int
    alam_codes: tuple[int, ...]


#: Kuivad metsad: salu-, palu-, laane-, loo- ja nõmmemets.
DRY_FOREST: tuple[int, ...] = (30100, 30500, 30600, 30700, 31000)
#: Märjad metsad: soovikumets, samblasoomets, rohusoomets, kõdusoomets, rabastuv mets.
WET_FOREST: tuple[int, ...] = (30200, 30300, 30400, 30800, 30900)

#: Rühmad koodi järgi (kood ei kattu ühegi ökosüsteemi koodiga 1..6). „Muu (metsa)kooslus“ (31100, 31200) ei kuulu
#: kumbagi rühma, vaid ainult kogu metsa.
GROUPS: dict[int, Group] = {
    31: Group(31, "Kuivad metsad", 3, DRY_FOREST),
    32: Group(32, "Märjad metsad", 3, WET_FOREST),
}


def _alam_to_group(groups: dict[int, Group]) -> dict[int, int]:
    """``alam_kood`` -> rühma kood; kontrollib, et rühmad ei kattu."""
    out: dict[int, int] = {}
    for g in groups.values():
        for a in g.alam_codes:
            if a in out:
                raise ValueError(f"alamökosüsteem {a} on kahes rühmas ({out[a]}, {g.code})")
            out[a] = g.code
    return out


def make_group_units(used: pl.DataFrame, groups: dict[int, Group] | None = None) -> stats.Units:
    """Ühikud, kus rühmad on ökosüsteemi kohal ja rühmade alamökosüsteemid alamökosüsteemi kohal.

    Klass kuulub rühma, kui tema alamökosüsteem on rühmas ja ökosüsteem on rühma ökosüsteem. Nagu ``stats.make_units``,
    on alamökosüsteem ühik ainult siis, kui tal on vähemalt kaks seisundit; seisundi kaardistus on sama.

    Parameters
    ----------
    used
        ``baas.class_lut`` klassitabel (``idx, alam_kood, okosusteem_kood, uld``).
    groups
        Rühmad (vaikimisi ``GROUPS``).
    """
    groups = groups or GROUPS
    codes = tuple(sorted(groups))
    a2g = _alam_to_group(groups)
    g_ix = {c: i for i, c in enumerate(codes)}
    n_states = used.group_by("alam_kood").agg(pl.col("uld").n_unique().alias("k"))
    alam_codes = tuple(
        sorted(c for c in n_states.filter(pl.col("k") >= 2)["alam_kood"].to_list() if c in a2g)
    )
    alam_ix = {c: i for i, c in enumerate(alam_codes)}
    n = int(used["idx"].to_numpy().max()) + 1
    cls_alam = np.full(n, -1, dtype=np.int32)
    cls_eco = np.full(n, -1, dtype=np.int32)
    cls_state = np.full(n, -1, dtype=np.int8)
    alam_eco = np.full(len(alam_codes), -1, dtype=np.int32)
    for r in used.iter_rows(named=True):
        i = r["idx"]
        cls_state[i] = 3 - int(r["uld"])
        gc = a2g.get(r["alam_kood"])
        if gc is None or r["okosusteem_kood"] != groups[gc].eco:
            continue
        cls_eco[i] = g_ix[gc]
        if r["alam_kood"] in alam_ix:
            cls_alam[i] = alam_ix[r["alam_kood"]]
            alam_eco[alam_ix[r["alam_kood"]]] = g_ix[gc]
    return stats.Units(codes, alam_codes, cls_alam, cls_eco, cls_state, alam_eco)


def kood_groups(used: pl.DataFrame, groups: dict[int, Group] | None = None) -> pl.DataFrame:
    """Baaskaardi koodid -> plokimediaani rühm ``rühma_kood * 10 + uld`` (nagu ``pipeline.groupings``)."""
    groups = groups or GROUPS
    a2g = _alam_to_group(groups)
    rows = [
        (int(r["kood"]), a2g[r["alam_kood"]] * 10 + int(r["uld"]))
        for r in used.iter_rows(named=True)
        if r["alam_kood"] in a2g
        and r["okosusteem_kood"] == groups[a2g[r["alam_kood"]]].eco
        and r["uld"] in (1, 2, 3)
    ]
    return pl.DataFrame(rows, schema={"kood": pl.Int32, "group": pl.Int64}, orient="row")


def _weighted_medians(d: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Täpne mediaan iga ``keys`` rühma kohta loendustest (``value``, ``n``); paarisarvu korral kahe keskmise keskmine.

    Sama reegel mis ``aggregate.segment_medians`` (järgud ``(N-1)//2`` ja ``N//2``, väärtused float64-na).
    """
    s = d.sort([*keys, "value"]).with_columns(
        pl.col("n").cum_sum().over(keys).alias("_cum"), pl.col("n").sum().over(keys).alias("_tot")
    )
    lo = (pl.col("_tot") - 1) // 2
    hi = pl.col("_tot") // 2
    return (
        s.group_by(keys, maintain_order=True)
        .agg(
            pl.col("_tot").first().alias("n"),
            pl.col("value").filter(pl.col("_cum") > lo).first().alias("_lo"),
            pl.col("value").filter(pl.col("_cum") > hi).first().alias("_hi"),
        )
        .select(*keys, "n", ((pl.col("_lo") + pl.col("_hi")) / 2).alias("median"))
    )


def block_medians(val_dir: Path, kood_group: pl.DataFrame) -> pl.DataFrame:
    """Plokimediaanid plokk × rühm × seisund sagedustabelist (``aggregate.value_counts`` failid).

    Tulemus on samas vormis kui ``pipeline.blkmed_path`` fail rühmitusega ``"eco"`` (``group = kood * 10 + uld``),
    nii et ``stats.analyse_layer_median`` saab seda kasutada rühmaühikutega (``make_group_units``). Iga piksel on üks
    vaatlus; ``median_nz`` on nullist erinevate pikslite mediaan (``NaN``, kui neid ei ole).
    """
    keys = ["n_km", "e_km", "group"]
    parts: list[pl.DataFrame] = []
    for f in sorted(val_dir.glob("n*.parquet")):
        d = (
            pl.read_parquet(f)
            .join(kood_group, on="kood", how="inner")
            .group_by([*keys, "value"])
            .agg(pl.col("n").cast(pl.Int64).sum())
            .with_columns(
                pl.col("value").cast(pl.Float64), pl.col("n_km").cast(pl.Int64), pl.col("e_km").cast(pl.Int64)
            )
        )
        if d.is_empty():
            continue
        allm = _weighted_medians(d, keys)
        nz = _weighted_medians(d.filter(pl.col("value") != 0), keys).rename(
            {"n": "n_nz", "median": "median_nz"}
        )
        parts.append(
            allm.join(nz, on=keys, how="left").with_columns(
                pl.col("n_nz").fill_null(0), pl.col("median_nz").fill_null(float("nan"))
            )
        )
    schema = {
        "e_km": pl.Int64,
        "group": pl.Int64,
        "n": pl.Int64,
        "median": pl.Float64,
        "n_nz": pl.Int64,
        "median_nz": pl.Float64,
        "grouping": pl.String,
        "n_km": pl.Int64,
    }
    if not parts:
        return pl.DataFrame(schema=schema)
    return (
        pl.concat(parts)
        .with_columns(pl.lit("eco").alias("grouping"))
        .select([pl.col(c).cast(t) for c, t in schema.items()])
    )


def group_blkmed(blk: pl.DataFrame, val_dir: Path, used: pl.DataFrame) -> pl.DataFrame:
    """Rühmaühikute plokimediaanid: v2 alamökosüsteemi read (``blk``) + rühma read sagedustabelist."""
    alam = blk.filter(pl.col("grouping") == "alam")
    grp = block_medians(val_dir, kood_groups(used))
    return pl.concat([alam.select([pl.col(c).cast(grp.schema[c]) for c in grp.columns]), grp])


def relabel(df: pl.DataFrame) -> pl.DataFrame:
    """Rühmaühikute analüüsi tulemusest rühma read: tase ``okosusteem`` -> ``LEVEL`` (alam-read jäetakse välja)."""
    if df.is_empty() or "unit_level" not in df.columns:
        return df
    return df.filter(pl.col("unit_level") == "okosusteem").with_columns(pl.lit(LEVEL).alias("unit_level"))
