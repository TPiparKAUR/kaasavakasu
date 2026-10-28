"""Töönäide: ühe kihi (seened_saagikus_2020_10m), ökosüsteemi Metsad paaritatud ja paaritamata Δ (vilets → hea) käsitsi.

Näitab (1) paaritamata keskmised (Σsum/Σn), (2) paaritatud stratumid (plokk x alamökosüsteem), kaalud ja Δ,
(3) kui suur osa piksleid paaritatud hinnangus osaleb. Sõltumatu: ei kasuta ``oks.stats``.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
LID = "seened_saagikus_2020_10m"
N_MIN = 100  # 10 m raster: 1 ha = 100 pikslit


def main() -> None:
    cm = pl.read_parquet(ROOT / "data/derived/klassid_kasutusel.parquet")
    ns = cm.group_by("alam_kood").agg(pl.col("uld").n_unique().alias("k"))
    cm = cm.join(ns, on="alam_kood").with_columns(
        pl.col("uld")
        .replace_strict({1: "hea", 2: "keskmine", 3: "vilets"}, return_dtype=pl.String)
        .alias("s")
    )
    b = (
        pl.read_parquet(ROOT / f"data/derived/plokid/{LID}.parquet")
        .with_columns(pl.col("n").cast(pl.Int64))
        .join(cm.select("idx", "alam_kood", "okosusteem_kood", "s", "k"), left_on="cls", right_on="idx")
        .filter(pl.col("okosusteem_kood") == 3)
    )
    un = (
        b.group_by("s")
        .agg(pl.col("n").sum(), pl.col("sum").sum())
        .with_columns((pl.col("sum") / pl.col("n")).alias("mean"))
    )
    print("PAARITAMATA (kõik Metsad-piksli read):")
    print(un)
    mu = {r["s"]: r["mean"] for r in un.iter_rows(named=True)}
    print(f"  Δ_u = {mu['hea']:.6f} − {mu['vilets']:.6f} = {mu['hea'] - mu['vilets']:.6f} kg/ha")
    st = (
        b.filter(pl.col("k") >= 2)
        .group_by("e_km", "n_km", "alam_kood", "s")
        .agg(pl.col("n").sum(), pl.col("sum").sum())
    )
    a = st.filter(pl.col("s") == "vilets").rename({"n": "na", "sum": "sa"}).drop("s")
    h = st.filter(pl.col("s") == "hea").rename({"n": "nb", "sum": "sb"}).drop("s")
    j = a.join(h, on=["e_km", "n_km", "alam_kood"]).filter((pl.col("na") >= N_MIN) & (pl.col("nb") >= N_MIN))
    j = (
        j.with_columns(
            (pl.col("sa") / pl.col("na")).alias("ma"),
            (pl.col("sb") / pl.col("nb")).alias("mb"),
            (pl.col("na") * pl.col("nb") / (pl.col("na") + pl.col("nb"))).alias("w"),
        )
        .with_columns((pl.col("mb") - pl.col("ma")).alias("d"))
        .with_columns((pl.col("w") * pl.col("d")).alias("wd"))
    )
    print("\nPAARITATUD: stratumeid =", j.height, "; näide 3 stratumit:")
    print(
        j.sort("w", descending=True)
        .head(3)
        .select("e_km", "n_km", "alam_kood", "na", "nb", "ma", "mb", "d", "w")
    )
    dm = j["wd"].sum() / j["w"].sum()
    print(f"  Δ_m = Σ w·d / Σ w = {j['wd'].sum():.3f} / {j['w'].sum():.3f} = {dm:.6f} kg/ha")
    tot = {s: int(un.filter(pl.col("s") == s)["n"][0]) for s in ("vilets", "hea")}
    used_a, used_b = int(j["na"].sum()), int(j["nb"].sum())
    print(
        f"  paaritatud hinnangus osalevaid piksleid: vilets {used_a:,} / {tot['vilets']:,} = {used_a / tot['vilets']:.1%}; hea {used_b:,} / {tot['hea']:,} = {used_b / tot['hea']:.1%}"
    )
    print(
        f"  stratumite keskmine ma (kaaluga w): {(j['w'] * j['ma']).sum() / j['w'].sum():.4f}  → rel_m = Δ_m / |ma| = {dm / ((j['w'] * j['ma']).sum() / j['w'].sum()):.4f}"
    )


if __name__ == "__main__":
    main()
