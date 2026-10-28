"""Sõltumatu ümberarvutus: paaritamata ja paaritatud keskmised, tulemustabelid ja veebilehe andmed.

Ei kasuta ``oks.stats`` ega ``oks.kaasnev`` loogikat: arvutab Polarsi liitmistega otse ``data/derived/plokid/*.parquet``
(plokitabel) ja ``*__cls.parquet`` (klassitabel) failidest ning võrdleb:

V1  paaritamata (ühik x seisund) keskmine plokitabelist  vs  ``data/tulemused/lahtrid.parquet``
V2  paaritatud Δ (ploki x alamökosüsteem stratumid)       vs  ``data/tulemused/paarid.parquet`` (``delta_m``)
V3  tüüp x seisund keskmine klassitabelist                vs  ``data/tulemused/kaasnev_tuup_seisund.parquet``
V4  ökosüsteemi keskmine: V1 (plokitabel) vs V3 (klassitabel) – kaks sõltumatut teed samale arvule
V5  veebilehe JSON (``site/data/*.json``)                 vs  tulemusfailid
V6  loogikakontrollid (vahemikud, hinna/koguse suhted, pindala, n)
V7  paaritatud vs paaritamata (märgi kokkulangevus)
V8  metoodika v2 täpsed mediaanid sagedustabelist (``*__val/``; ei kasuta ``oks.median``-it ega plokimediaane):
    ühik x seisund (``lahtrid``), tüüp x seisund (``kaasnev_tuup_seisund``), paaritatud Δ (``paarid.delta_m_med``)

Käivitus: ``uv run python scripts/valideeri_keskmised.py [--site site] [--out data/tulemused/validatsioon_keskmised.json]``
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "tulemused"
BLK = ROOT / "data" / "derived" / "plokid"
log = logging.getLogger("valideeri")
STATE_OF_ULD = {1: "hea", 2: "keskmine", 3: "vilets"}


def rel_err(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.abs(a - b) / np.maximum(np.abs(b), 1e-12)


def class_map() -> pl.DataFrame:
    """kood, alam_kood, okosusteem_kood, seisund (hea/keskmine/vilets) ja klassiindeks (``idx``) 228 seisundiklassile."""
    used = pl.read_parquet(ROOT / "data/derived/klassid_kasutusel.parquet")
    n_states = used.group_by("alam_kood").agg(pl.col("uld").n_unique().alias("k"))
    return used.join(n_states, on="alam_kood").with_columns(
        pl.col("uld").replace_strict(STATE_OF_ULD, return_dtype=pl.String).alias("seisund"),
        (pl.col("k") >= 2).alias("alam_ok"),
    )


def layer_res() -> dict[str, float]:
    t = pl.read_csv(ROOT / "data/teenused.csv")
    return {r["id"]: float(r["spatial_resolution"] or 10.0) for r in t.iter_rows(named=True)}


def v1_unpaired(cm: pl.DataFrame, lahtrid: pl.DataFrame, layers: list[str]) -> dict:
    """Paaritamata keskmine = Σsum / Σn (kõik piksli-read ühikus x seisundis)."""
    rows = []
    for lid in layers:
        p = BLK / f"{lid}.parquet"
        if not p.exists():
            continue
        b = (
            pl.read_parquet(p)
            .with_columns(pl.col("n").cast(pl.Int64))
            .join(
                cm.select("idx", "alam_kood", "okosusteem_kood", "seisund", "alam_ok"),
                left_on="cls",
                right_on="idx",
            )
        )
        eco = (
            b.group_by("okosusteem_kood", "seisund")
            .agg(pl.col("n").sum(), pl.col("sum").sum())
            .with_columns(
                pl.lit("okosusteem").alias("unit_level"), pl.col("okosusteem_kood").alias("unit_code")
            )
        )
        alam = (
            b.filter(pl.col("alam_ok"))
            .group_by("alam_kood", "seisund")
            .agg(pl.col("n").sum(), pl.col("sum").sum())
            .with_columns(pl.lit("alam").alias("unit_level"), pl.col("alam_kood").alias("unit_code"))
        )
        cols = ["unit_level", "unit_code", "seisund", "n", "sum"]
        mine = pl.concat([eco.select(cols), alam.select(cols)]).with_columns(
            (pl.col("sum") / pl.col("n")).alias("mean2")
        )
        ref = lahtrid.filter(pl.col("layer_id") == lid).select(
            "unit_level", "unit_code", pl.col("state").alias("seisund"), "n", "mean"
        )
        j = ref.join(
            mine.select("unit_level", "unit_code", "seisund", pl.col("n").alias("n2"), "mean2"),
            on=["unit_level", "unit_code", "seisund"],
            how="full",
        )
        rows.append((lid, j))
    out = {"layers": len(rows), "cells": 0, "missing": 0, "n_mismatch": 0, "max_rel_err": 0.0, "worst": None}
    for lid, j in rows:
        miss = j.filter(pl.col("n").is_null() | pl.col("n2").is_null())
        both = j.drop_nulls(["n", "n2"])
        out["cells"] += both.height
        out["missing"] += miss.height
        out["n_mismatch"] += both.filter(pl.col("n") != pl.col("n2")).height
        m = both.drop_nulls(["mean", "mean2"])
        if m.height:
            e = rel_err(m["mean2"].to_numpy(), m["mean"].to_numpy())
            if e.max() > out["max_rel_err"]:
                out["max_rel_err"] = float(e.max())
                out["worst"] = f"{lid} {m.row(int(e.argmax()), named=True)}"
    return out


def matched(cm: pl.DataFrame, lid: str, res_m: float, min_area_ha: float = 1.0) -> pl.DataFrame:
    """Paaritatud Δ: stratum = (e_km, n_km, alam_kood); kaal w = n_a n_b / (n_a + n_b)."""
    n_min = max(1, int(round(min_area_ha * 10_000 / res_m**2)))
    b = (
        pl.read_parquet(BLK / f"{lid}.parquet")
        .with_columns(pl.col("n").cast(pl.Float64))
        .join(
            cm.filter(pl.col("alam_ok")).select("idx", "alam_kood", "okosusteem_kood", "seisund"),
            left_on="cls",
            right_on="idx",
        )
    )
    s = b.group_by("e_km", "n_km", "alam_kood", "okosusteem_kood", "seisund").agg(
        pl.col("n").sum(), pl.col("sum").sum()
    )
    out = []
    for pair, (lo, hi) in {
        "vilets→keskmine": ("vilets", "keskmine"),
        "keskmine→hea": ("keskmine", "hea"),
        "vilets→hea": ("vilets", "hea"),
    }.items():
        a = s.filter(pl.col("seisund") == lo).rename({"n": "na", "sum": "sa"}).drop("seisund")
        c = s.filter(pl.col("seisund") == hi).rename({"n": "nb", "sum": "sb"}).drop("seisund")
        j = a.join(c, on=["e_km", "n_km", "alam_kood", "okosusteem_kood"]).filter(
            (pl.col("na") >= n_min) & (pl.col("nb") >= n_min)
        )
        j = j.with_columns(
            (pl.col("sb") / pl.col("nb") - pl.col("sa") / pl.col("na")).alias("d"),
            (pl.col("na") * pl.col("nb") / (pl.col("na") + pl.col("nb"))).alias("w"),
        ).with_columns((pl.col("w") * pl.col("d")).alias("wd"))
        for level, key in (("okosusteem", "okosusteem_kood"), ("alam", "alam_kood")):
            g = (
                j.group_by(key)
                .agg(pl.col("wd").sum(), pl.col("w").sum(), pl.len().alias("n_strata"))
                .with_columns(
                    pl.lit(level).alias("unit_level"),
                    pl.lit(pair).alias("pair"),
                    pl.col(key).alias("unit_code"),
                    (pl.col("wd") / pl.col("w")).alias("delta_m2"),
                )
            )
            out.append(g.select("unit_level", "unit_code", "pair", "delta_m2", "n_strata", "w"))
    return pl.concat(out).with_columns(pl.lit(lid).alias("layer_id"))


def v2_paired(cm: pl.DataFrame, paarid: pl.DataFrame, layers: list[str]) -> dict:
    # metoodika v2: madalama lahutusvõimega kihid on 10 m lahutusvõimel, seega efektiivne lahutus = paarid.res_m
    res = dict(paarid.select("layer_id", "res_m").unique("layer_id").iter_rows())
    parts = [
        matched(cm, lid, float(res.get(lid, 10.0))) for lid in layers if (BLK / f"{lid}.parquet").exists()
    ]
    mine = pl.concat(parts)
    ref = paarid.select(
        "layer_id",
        "unit_level",
        "unit_code",
        "pair",
        "delta_m",
        "n_strata",
        "mean_a",
        "mean_b",
        "delta_u",
        "enough_m",
        "enough_u",
    )
    j = ref.join(mine, on=["layer_id", "unit_level", "unit_code", "pair"], how="left", suffix="_2")
    nan = j.filter(pl.col("delta_m").is_nan())
    has = j.filter(pl.col("delta_m").is_not_null() & ~pl.col("delta_m").is_nan())
    both = has.filter(pl.col("delta_m2").is_not_null())
    e = rel_err(both["delta_m2"].to_numpy(), both["delta_m"].to_numpy())
    absd = np.abs(both["delta_m2"].to_numpy() - both["delta_m"].to_numpy())
    return {
        "rows_with_delta_m (blokitabelist, ilma NaN-ita)": has.height,
        "rows NaN (stratume pole, n_strata=0)": nan.height,
        "recomputed": both.height,
        "unmatched_in_recompute": has.height - both.height,
        "n_strata_mismatch": both.filter(pl.col("n_strata") != pl.col("n_strata_2")).height,
        "max_abs_diff": float(absd.max()) if absd.size else None,
        "max_rel_err": float(e.max()) if e.size else None,
    }


def v3_type_state(cm_all: pl.DataFrame, kt: pl.DataFrame, layers: list[str]) -> dict:
    """Tüüp x seisund keskmine klassitabelist (kõik 264 klassi)."""
    tot = {"cells": 0, "n_mismatch": 0, "max_rel_err": 0.0, "worst": None, "area_mismatch": 0}
    for lid in layers:
        p = BLK / f"{lid}__cls.parquet"
        if not p.exists():
            continue
        c = pl.read_parquet(p).join(cm_all.select("kood", "alam_kood", "uld"), on="kood")
        g = (
            c.group_by("alam_kood", "uld")
            .agg(pl.col("n_valid").sum(), pl.col("sum").sum())
            .with_columns((pl.col("sum") / pl.col("n_valid")).alias("m2"))
        )
        ref = kt.filter(pl.col("layer_id") == lid).select("alam_kood", "uld", "mean", "n_valid", "pindala_ha")
        j = ref.join(g, on=["alam_kood", "uld"]).drop_nulls(["mean", "m2"])
        tot["cells"] += j.height
        tot["n_mismatch"] += j.filter(pl.col("n_valid") != pl.col("n_valid_right")).height
        if j.height:
            e = rel_err(j["m2"].to_numpy(), j["mean"].to_numpy())
            if e.max() > tot["max_rel_err"]:
                tot["max_rel_err"] = float(e.max())
                tot["worst"] = f"{lid} {j.row(int(e.argmax()), named=True)}"
    area = cm_all.group_by("alam_kood", "uld").agg((pl.col("n_pix").sum() * 25 / 10_000).alias("a2"))
    chk = kt.select("alam_kood", "uld", "pindala_ha").unique().join(area, on=["alam_kood", "uld"])
    tot["area_mismatch"] = chk.filter((pl.col("pindala_ha") - pl.col("a2")).abs() > 1e-6).height
    tot["area_rows"] = chk.height
    return tot


def v4_cross(cm: pl.DataFrame, lahtrid: pl.DataFrame, ks: pl.DataFrame, layers: list[str]) -> dict:
    """Ökosüsteemi keskmine seisundi kaupa: plokitabel (V1 tee) vs klassitabel (kaasnev) – peavad ühtima."""
    big = ks.filter(
        pl.col("okosusteem_kood").is_in([1, 2, 3, 4])
        & pl.col("seisund_nimi").is_in(["hea", "keskmine", "vilets"])
    )
    ref = lahtrid.filter(pl.col("unit_level") == "okosusteem").with_columns(
        pl.col("unit_code").alias("okosusteem_kood")
    )
    j = ref.join(
        big,
        left_on=["layer_id", "okosusteem_kood", "state"],
        right_on=["layer_id", "okosusteem_kood", "seisund_nimi"],
        suffix="_k",
    )
    j = j.drop_nulls(["mean", "mean_k"])
    diff = rel_err(j["mean_k"].to_numpy(), j["mean"].to_numpy())
    big_diff = j.with_columns(pl.Series("e", diff)).filter(pl.col("e") > 1e-9)
    return {
        "cells": j.height,
        "max_rel_err": float(diff.max()),
        "cells_over_1e-9": big_diff.height,
        "worst": big_diff.sort("e", descending=True)
        .head(3)
        .select("layer_id", "okosusteem_kood", "state", "mean", "mean_k", "e")
        .to_dicts(),
    }


def sig5(x: float) -> float:
    return x if x == 0 else round(x, 4 - int(math.floor(math.log10(abs(x)))))


def close5(shown: float | None, true: float | None) -> bool:
    """JSON-i väärtus (5 olulist numbrit) vs täpne väärtus; mõlemad tühjad = kokkulangevus."""
    if shown is None or true is None or (isinstance(true, float) and math.isnan(true)):
        return (shown is None) == (true is None or (isinstance(true, float) and math.isnan(true)))
    return abs(shown - true) <= 5e-5 * max(abs(true), 1e-9)


def v5_site(site: Path, lahtrid: pl.DataFrame, ks: pl.DataFrame, kt: pl.DataFrame) -> dict:
    out: dict = {}
    K = json.loads((site / "data/kaasnev.json").read_text(encoding="utf-8"))
    layers = [x["id"] for x in K["kihid"]]
    # tüübid
    exp = {
        (r["okosusteem_kood"], r["alam_kood"], r["uld"], r["layer_id"]): r for r in kt.iter_rows(named=True)
    }
    bad = n = 0
    for row in K["tuubid"]:
        ok, alam, _tuup, uld, _sn, area, cells = row
        for lid, c in zip(layers, cells, strict=True):
            r = exp.get((ok, alam, uld, lid))
            if c is None or r is None:
                continue
            if r["mean"] is None or c[1] is None:
                continue
            n += 1
            # metoodika v2: lahter = [mediaan, keskmine, kate, esineb_osa, staatus, mediaan > 0]
            if not (close5(c[1], r["mean"]) and close5(c[0], r["median"])):
                bad += 1
    out["kaasnev.json tuubid: cells"] = n
    out["kaasnev.json tuubid: mismatches (>5e-5 rel)"] = bad
    expb = {(r["okosusteem_kood"], r["seisund_nimi"], r["layer_id"]): r for r in ks.iter_rows(named=True)}
    bad = n = 0
    for ok, sn, _area, cells in K["suured"]:
        for lid, c in zip(layers, cells, strict=True):
            r = expb.get((ok, sn, lid))
            if c is None or r is None or r["mean"] is None or c[1] is None:
                continue
            n += 1
            if not (close5(c[1], r["mean"]) and close5(c[0], r["median"])):
                bad += 1
    out["kaasnev.json suured: cells (v.a. segumudel)"] = n
    out["kaasnev.json suured: mismatches"] = bad
    # lahtrid.json
    meta = json.loads((site / "data/meta.json").read_text(encoding="utf-8"))
    L = json.loads((site / "data/lahtrid.json").read_text(encoding="utf-8"))
    cols = meta["lahtrid_veerud"]
    ix = {c: i for i, c in enumerate(cols)}
    ids = [t["id"] for t in meta["teenused"]]
    units = meta["uhikud"]
    ref = {
        (r["layer_id"], r["unit_level"], r["unit_code"], r["state"]): r for r in lahtrid.iter_rows(named=True)
    }
    bad = n = 0
    for r in L:
        u = units[r[ix["unit_code"]]]
        key = (ids[r[ix["layer_id"]]], u["tase"], u["kood"], meta["seisundid"][r[ix["state"]]])
        e = ref.get(key)
        n += 1
        mean_bad = (
            e is None
            or (
                r[ix["mean"]] is not None
                and abs(r[ix["mean"]] - e["mean"]) > 5e-5 * max(abs(e["mean"]), 1e-9)
            )
            or r[ix["n"]] != e["n"]
        )
        if mean_bad or ("median" in ix and not close5(r[ix["median"]], e["median"])):
            bad += 1
    out["lahtrid.json: rows"] = n
    out["lahtrid.json: mismatches"] = bad
    return out


def v6_logic(ks: pl.DataFrame, kt: pl.DataFrame, lahtrid: pl.DataFrame) -> dict:
    """Loogikakontrollid, mis ei sõltu ühestki torustiku sammust."""
    out: dict = {}
    res = layer_res()
    # pindala: n_valid * res^2 <= pindala (ha), katvus <= 1
    k = kt.filter(pl.col("n_valid") > 0).with_columns(
        pl.col("layer_id").replace_strict(res, default=10.0, return_dtype=pl.Float64).alias("res")
    )
    k = k.with_columns((pl.col("n_valid") * pl.col("res") ** 2 / 10_000).alias("valid_ha"))
    out["rida kus kehtiv pindala > baaskaardi pindala x 1,02"] = k.filter(
        pl.col("valid_ha") > pl.col("pindala_ha") * 1.02
    ).height
    out["rida kus kate > 1"] = k.filter(pl.col("kate") > 1.0000001).height
    out["rida kus keskmine < 0 (kihid ilma negatiivsete väärtusteta)"] = kt.filter(
        (pl.col("mean") < 0) & (pl.col("layer_id") != "pohlad_saagikus_2020_10m")
    ).height
    # vahemikud
    rng = {
        "elupaigahuve_pakkumine_2022_10m": (0, 10),
        "okosusteemide_tugi_tolmeldajatele_2022_10m": (0, 1),
        "ohusaaste_puhverdusvoime_2022_5m": (0, 10),
        "sidusus_1km_2022_10m": (0, 100),
        "virgestuse_koondvaartus_2022_5m": (0, 255),
    }
    bad = {}
    for lid, (lo, hi) in rng.items():
        d = kt.filter((pl.col("layer_id") == lid) & pl.col("mean").is_not_null())
        bad[lid] = d.filter((pl.col("mean") < lo) | (pl.col("mean") > hi)).height
    out["väljaspool deklareeritud vahemikku"] = bad
    # hinna/koguse suhted ökosüsteemi tasemel (võrdlus ainult sama pindala ja kehtivusega)
    ratios = {}
    e = ks.filter(
        pl.col("okosusteem_kood").is_in([1, 2, 3, 4])
        & pl.col("seisund_nimi").is_in(["hea", "keskmine", "vilets"])
        & pl.col("mean").is_not_null()
    )

    def ratio(num: str, den: str, expect: float, tag: str) -> None:
        a = e.filter(pl.col("layer_id") == num).select(
            "okosusteem_kood", "seisund_nimi", pl.col("mean").alias("a"), pl.col("kate").alias("ka")
        )
        b = e.filter(pl.col("layer_id") == den).select(
            "okosusteem_kood", "seisund_nimi", pl.col("mean").alias("b"), pl.col("kate").alias("kb")
        )
        j = a.join(b, on=["okosusteem_kood", "seisund_nimi"]).filter(pl.col("b") > 0)
        r = (j["a"] / j["b"]).to_numpy()
        ratios[tag] = {"oodatud": expect, "min": float(r.min()), "max": float(r.max()), "n": int(r.size)}

    ratio(
        "mullasusinik_aasta_keskmine_2022_10m",
        "c_tonn_per_ha_final_2022_10m",
        3.67 * 80.68,
        "mulla C: ETS EUR/ha ÷ t C/ha",
    )
    ratio(
        "mullasusinik_aasta_sotsiaalne_kulu_2022_10m",
        "c_tonn_per_ha_final_2022_10m",
        3.67 * 169.77,
        "mulla C: sotsiaalne kulu EUR/ha ÷ t C/ha",
    )
    ratio("seened_hind_2022_10m", "seened_saagikus_2020_10m", 4.5, "seened: EUR/ha ÷ kg/ha")
    ratio(
        "mustikad_pohlad_hind_2022_10m",
        "mustikad_pohlad_saagikus_2020_10m",
        2.5,
        "mustikad/pohlad: EUR/ha ÷ kg/ha",
    )
    out["hinna ja koguse suhted"] = ratios
    # seisundite järjestus: mitu (ühik, kiht) paari, kus hea-vilets erinevus märk ühtib/erineb paaritatud hinnangu märgist
    return out


def v7_matched_vs_unmatched(paarid: pl.DataFrame) -> dict:
    p = paarid.filter(pl.col("enough_m") & pl.col("enough_u") & (pl.col("pair") == "vilets→hea"))
    flip = p.filter(pl.col("delta_m").sign() != pl.col("delta_u").sign()).filter(
        (pl.col("delta_m") != 0) & (pl.col("delta_u") != 0)
    )
    out: dict = {}
    for lvl in ("okosusteem", "alam"):
        q = p.filter(pl.col("unit_level") == lvl)
        out[lvl] = {
            "võrreldavaid": q.height,
            "märk erineb": flip.filter(pl.col("unit_level") == lvl).height,
            "mediaan |Δm−Δu| / |Δu|": float(
                ((q["delta_m"] - q["delta_u"]).abs() / q["delta_u"].abs().clip(lower_bound=1e-12)).median()
            ),
        }
    zero = paarid.filter((pl.col("mean_a") == 0) & (pl.col("mean_b") == 0))
    out["paare kus mõlemad keskmised = 0 (POSITIVE_MIN filtrit analüüsis ei ole)"] = {
        "rida": zero.height,
        "neist enough_m": zero.filter(pl.col("enough_m")).height,
        "kihte": zero["layer_id"].n_unique(),
    }
    return out


def wmedian(d: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Täpne mediaan sagedustabelist (väärtus, kordus ``n``): paarisarvu korral kahe keskmise järgu keskmine."""
    g = d.group_by(*keys, "value").agg(pl.col("n").sum()).sort(*keys, "value")
    g = g.with_columns(pl.col("n").cum_sum().over(keys).alias("c"), pl.col("n").sum().over(keys).alias("N"))
    lo = (
        g.filter(pl.col("c") >= (pl.col("N") + 1) // 2)
        .group_by(keys)
        .agg(pl.col("value").min().alias("lo"), pl.col("N").first())
    )
    hi = g.filter(pl.col("c") >= pl.col("N") // 2 + 1).group_by(keys).agg(pl.col("value").min().alias("hi"))
    return (
        lo.join(hi, on=keys)
        .with_columns(((pl.col("lo") + pl.col("hi")) / 2).alias("median"))
        .drop("lo", "hi")
    )


def _val(lid: str) -> Path:
    return BLK / f"{lid}__val"


def _scan(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path).with_columns(
        pl.col("value").cast(pl.Float64), pl.col("n").cast(pl.Int64), pl.col("kood").cast(pl.Int64)
    )


def _cmp(ref: pl.DataFrame, mine: pl.DataFrame, keys: list[str], col: str, out: dict, tag: str) -> None:
    # NaN (nt nullist erinevaid piksleid ei ole) = väärtus puudub
    j = ref.join(mine, on=keys, how="full", coalesce=True, suffix="_2").with_columns(
        pl.col(col, f"{col}_2").fill_nan(None)
    )
    miss = j.filter(
        pl.col(col).is_null() & pl.col(f"{col}_2").is_not_null()
        | pl.col(col).is_not_null() & pl.col(f"{col}_2").is_null()
    )
    both = j.drop_nulls([col, f"{col}_2"])
    e = rel_err(both[f"{col}_2"].to_numpy(), both[col].to_numpy())
    out[f"{tag}: võrreldud"] = out.get(f"{tag}: võrreldud", 0) + both.height
    out[f"{tag}: puudub ühel poolel"] = out.get(f"{tag}: puudub ühel poolel", 0) + miss.height
    bad = int((e > 1e-6).sum())
    out[f"{tag}: lahknevusi (> 1e-6 rel)"] = out.get(f"{tag}: lahknevusi (> 1e-6 rel)", 0) + bad
    if bad:
        out.setdefault("näited", []).append(f"{tag} {both.row(int(e.argmax()), named=True)}")


def v8_medians(
    cm: pl.DataFrame,
    cm_all: pl.DataFrame,
    lahtrid: pl.DataFrame,
    kt: pl.DataFrame,
    paarid: pl.DataFrame,
    layers: list[str],
    max_rows: int,
) -> dict:
    """Metoodika v2 mediaanid sõltumatult: Polarsi kumulatiivne summa üle sorteeritud sagedustabeli."""
    out: dict = {"kihte": 0, "ühik/tüüp mediaanid vahele jäetud (sagedustabel > max_rows)": []}
    res = dict(paarid.select("layer_id", "res_m").unique("layer_id").iter_rows())
    cmk = cm.select("kood", "alam_kood", "okosusteem_kood", "seisund", "alam_ok")
    for lid in layers:
        vdir = _val(lid)
        if not vdir.exists():
            continue
        out["kihte"] += 1
        files = sorted(vdir.glob("n*.parquet"))
        rows = pl.scan_parquet(files).select(pl.len()).collect().item()
        # 1) ühik x seisund ja tüüp x seisund (kogu Eesti) – ainult mõõduka suurusega sagedustabelid
        if rows <= max_rows:
            v = pl.concat([_scan(f) for f in files])
            b = v.join(cmk, on="kood")
            for nz, col in ((False, "median"), (True, "median_nz")):
                x = b.filter(pl.col("value") != 0) if nz else b
                eco = wmedian(x, ["okosusteem_kood", "seisund"]).select(
                    pl.lit("okosusteem").alias("unit_level"),
                    pl.col("okosusteem_kood").alias("unit_code"),
                    pl.col("seisund").alias("state"),
                    pl.col("median").alias(col),
                )
                alam = wmedian(x.filter(pl.col("alam_ok")), ["alam_kood", "seisund"]).select(
                    pl.lit("alam").alias("unit_level"),
                    pl.col("alam_kood").alias("unit_code"),
                    pl.col("seisund").alias("state"),
                    pl.col("median").alias(col),
                )
                ref = lahtrid.filter(pl.col("layer_id") == lid).select(
                    "unit_level", "unit_code", "state", col
                )
                _cmp(
                    ref,
                    pl.concat([eco, alam]),
                    ["unit_level", "unit_code", "state"],
                    col,
                    out,
                    f"lahtrid.{col}",
                )
            t = wmedian(v.join(cm_all.select("kood", "alam_kood", "uld"), on="kood"), ["alam_kood", "uld"])
            ref = kt.filter((pl.col("layer_id") == lid) & pl.col("median").is_not_null()).select(
                "alam_kood", "uld", "median"
            )
            _cmp(
                ref,
                t.select("alam_kood", "uld", "median").filter(
                    pl.col("alam_kood").is_in(ref["alam_kood"].implode())
                ),
                ["alam_kood", "uld"],
                "median",
                out,
                "kaasnev_tuup_seisund.median",
            )
            del v, b
        else:
            out["ühik/tüüp mediaanid vahele jäetud (sagedustabel > max_rows)"].append(
                f"{lid} ({rows:,} rida)"
            )
        # 2) paaritatud: stratum = (1 km plokk, alamökosüsteem); iga fail on üks ploki-rida, seega stratumid ei ületa faili piiri
        st = pl.concat(
            [
                wmedian(
                    _scan(f).join(cmk.filter(pl.col("alam_ok")), on="kood"),
                    ["e_km", "n_km", "alam_kood", "okosusteem_kood", "seisund"],
                )
                for f in files
            ]
        )
        n_min = max(1, int(round(1.0 * 10_000 / float(res.get(lid, 10.0)) ** 2)))
        parts = []
        for pair, (lo, hi) in {
            "vilets→keskmine": ("vilets", "keskmine"),
            "keskmine→hea": ("keskmine", "hea"),
            "vilets→hea": ("vilets", "hea"),
        }.items():
            a = st.filter(pl.col("seisund") == lo).select(
                "e_km",
                "n_km",
                "alam_kood",
                "okosusteem_kood",
                pl.col("N").alias("na"),
                pl.col("median").alias("ma"),
            )
            c = st.filter(pl.col("seisund") == hi).select(
                "e_km", "n_km", "alam_kood", pl.col("N").alias("nb"), pl.col("median").alias("mb")
            )
            j = a.join(c, on=["e_km", "n_km", "alam_kood"]).filter(
                (pl.col("na") >= n_min) & (pl.col("nb") >= n_min)
            )
            j = j.with_columns(
                (pl.col("na") * pl.col("nb") / (pl.col("na") + pl.col("nb"))).alias("w")
            ).with_columns((pl.col("w") * (pl.col("mb") - pl.col("ma"))).alias("wd"))
            for level, key in (("okosusteem", "okosusteem_kood"), ("alam", "alam_kood")):
                g = j.group_by(key).agg(pl.col("wd").sum(), pl.col("w").sum())
                parts.append(
                    g.select(
                        pl.lit(level).alias("unit_level"),
                        pl.col(key).cast(pl.Int64).alias("unit_code"),
                        pl.lit(pair).alias("pair"),
                        (pl.col("wd") / pl.col("w")).alias("delta_m_med"),
                    )
                )
        ref = paarid.filter((pl.col("layer_id") == lid) & pl.col("delta_m_med").is_not_null()).select(
            "unit_level", "unit_code", "pair", "delta_m_med"
        )
        mine = pl.concat(parts).join(
            ref.select("unit_level", "unit_code", "pair"), on=["unit_level", "unit_code", "pair"]
        )
        _cmp(ref, mine, ["unit_level", "unit_code", "pair"], "delta_m_med", out, "paarid.delta_m_med")
        log.info("V8 %s: %d rida", lid, rows)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(ROOT / "site"))
    ap.add_argument("--out", default=str(RES / "validatsioon_keskmised.json"))
    ap.add_argument(
        "--max-rows",
        type=int,
        default=60_000_000,
        help="V8: suurim sagedustabeli ridade arv ühiku mediaanideks",
    )
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cm = class_map()
    cm_all = pl.read_parquet(ROOT / "data/derived/klassid.parquet")
    lahtrid = pl.read_parquet(RES / "lahtrid.parquet")
    paarid = pl.read_parquet(RES / "paarid.parquet")
    kt = pl.read_parquet(RES / "kaasnev_tuup_seisund.parquet")
    ks = pl.read_parquet(RES / "kaasnev_suured.parquet")
    layers = sorted(lahtrid["layer_id"].unique().to_list())
    kt_layers = sorted(kt["layer_id"].unique().to_list())
    out = {
        "V1 paaritamata (plokitabel vs lahtrid.parquet)": v1_unpaired(cm, lahtrid, layers),
        "V2 paaritatud Δ (sõltumatu stratifitseerimine vs paarid.parquet)": v2_paired(cm, paarid, layers),
        "V3 tüüp x seisund (klassitabel vs kaasnev_tuup_seisund.parquet)": v3_type_state(
            cm_all, kt, kt_layers
        ),
        "V4 ökosüsteemi keskmine: plokitabel vs klassitabel": v4_cross(cm, lahtrid, ks, layers),
        "V5 veebilehe JSON": v5_site(Path(a.site), lahtrid, ks, kt),
        "V6 loogika": v6_logic(ks, kt, lahtrid),
        "V7 paaritatud vs paaritamata": v7_matched_vs_unmatched(paarid),
        "V8 mediaanid (sagedustabel vs tulemused)": v8_medians(
            cm, cm_all, lahtrid, kt, paarid, layers, a.max_rows
        ),
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2, default=float), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2, default=float))


if __name__ == "__main__":
    main()
