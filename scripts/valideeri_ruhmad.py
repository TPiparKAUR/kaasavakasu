"""Metoodika v3 kontrollid V-R2…V-R7 kuivade ja märgade metsade (tase ``ruhm``) tulemustel.

V-R2  metsa paaritatud Δ = rühmade ja muu koosluse kaalutud keskmine (kaal = ``sum_w_m_med``)
V-R3  metsa paaride arv = kuiva metsa + märja metsa + muu koosluse paaride arv
V-R4  rühma seisundi mediaan = tulemustabeli (``kaasnev_suured``) mediaan samale rühmale ja seisundile
V-R5  rühma jaotus = rühma alamökosüsteemide jaotuste summa
V-R6  paaritatud tasemed: level_b − level_a = Δ (kõigil tasemetel)
V-R7  rühmade FDR on arvutatud ainult rühmade p-väärtustest (oma perekond)

Väljund: ``data/tulemused/validatsioon_ruhmad.json``; lõpetab koodiga 1, kui leidub erinevusi.

Käivitus: ``uv run python scripts/valideeri_ruhmad.py``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import polars as pl

from oks import ruhmad, stats

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "tulemused"
TOL = 1e-9
log = logging.getLogger("valideeri_ruhmad")


def _close(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (np.isnan(a) & np.isnan(b)) | (np.abs(a - b) <= 1e-12 + TOL * np.abs(a))


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = pl.read_parquet(RES / "paarid.parquet")
    lah = pl.read_parquet(RES / "lahtrid.parquet")
    dist = pl.read_parquet(RES / "jaotused.parquet")
    big = pl.read_parquet(RES / "kaasnev_suured.parquet")
    units = pl.read_parquet(RES / "uhikud.parquet")
    forest_alams = units.filter((pl.col("unit_level") == "alam") & (pl.col("eco_code") == 3))[
        "unit_code"
    ].to_list()
    in_group = {a for g in ruhmad.GROUPS.values() for a in g.alam_codes}
    other = [a for a in forest_alams if a not in in_group]
    res: dict[str, dict[str, object]] = {}

    # V-R2, V-R3
    keys = ["layer_id", "pair"]
    forest = p.filter((pl.col("unit_level") == "okosusteem") & (pl.col("unit_code") == 3))
    parts = p.filter(
        (pl.col("unit_level") == ruhmad.LEVEL)
        | ((pl.col("unit_level") == "alam") & pl.col("unit_code").is_in(other))
    )
    agg = parts.group_by(keys).agg(
        (pl.col("sum_w_m_med").fill_nan(0) * pl.col("delta_m_med").fill_nan(0)).sum().alias("num"),
        pl.col("sum_w_m_med").fill_nan(0).sum().alias("den"),
        pl.col("n_strata").sum().alias("n_sum"),
    )
    j = forest.join(agg, on=keys, how="inner").filter(pl.col("den") > 0)
    d_ok = _close(j["delta_m_med"].to_numpy(), (j["num"] / j["den"]).to_numpy())
    n_ok = j["n_strata"].to_numpy() == j["n_sum"].to_numpy()
    res["V-R2"] = {"vorreldud": j.height, "erinevusi": int((~d_ok).sum())}
    res["V-R3"] = {"vorreldud": j.height, "erinevusi": int((~n_ok).sum())}

    # V-R4
    g = lah.filter(pl.col("unit_level") == ruhmad.LEVEL).select(
        "layer_id",
        pl.col("unit_code").alias("okosusteem_kood"),
        pl.col("state").alias("seisund_nimi"),
        "median",
        "median_nz",
    )
    k = big.filter(pl.col("okosusteem_kood").is_in(list(ruhmad.GROUPS))).select(
        "layer_id",
        pl.col("okosusteem_kood").cast(pl.Int64),
        "seisund_nimi",
        pl.col("median").alias("median_k"),
        pl.col("median_nz").alias("median_nz_k"),
    )
    jj = g.join(k, on=["layer_id", "okosusteem_kood", "seisund_nimi"], how="inner")
    m_ok = _close(jj["median"].to_numpy(), jj["median_k"].to_numpy()) & _close(
        jj["median_nz"].to_numpy(), jj["median_nz_k"].to_numpy()
    )
    res["V-R4"] = {
        "vorreldud": jj.height,
        "rühma_lahtreid": g.height,
        "erinevusi": int((~m_ok).sum()) + (g.height - jj.height),
    }

    # V-R5
    a2g = {a: c for c, gg in ruhmad.GROUPS.items() for a in gg.alam_codes}
    alam_sum = (
        dist.filter((pl.col("unit_level") == "alam") & pl.col("unit_code").is_in(list(a2g)))
        .with_columns(pl.col("unit_code").replace_strict(a2g, return_dtype=pl.Int64))
        .group_by("layer_id", "unit_code", "state", "bin")
        .agg(pl.col("n").sum().alias("n_alam"))
    )
    gd = dist.filter(pl.col("unit_level") == ruhmad.LEVEL).join(
        alam_sum, on=["layer_id", "unit_code", "state", "bin"], how="full", coalesce=True
    )
    res["V-R5"] = {
        "vorreldud": gd.height,
        "erinevusi": gd.filter(pl.col("n").fill_null(0) != pl.col("n_alam").fill_null(0)).height,
    }

    # V-R6
    e = p.filter(pl.col("delta_m_med").is_not_nan() & pl.col("level_a_m_med").is_not_nan())
    l_ok = _close(e["delta_m_med"].to_numpy(), (e["level_b_m_med"] - e["level_a_m_med"]).to_numpy())
    # tasemete vahe on arvutatud teises järjekorras, seega abs. tolerants ujukomaarvude suurusjärgu järgi
    scale = np.maximum(np.abs(e["level_a_m_med"].to_numpy()), np.abs(e["level_b_m_med"].to_numpy()))
    l_ok |= (
        np.abs(e["delta_m_med"].to_numpy() - (e["level_b_m_med"] - e["level_a_m_med"]).to_numpy())
        <= 1e-9 * scale
    )
    res["V-R6"] = {"vorreldud": e.height, "erinevusi": int((~l_ok).sum())}

    # V-R7
    gp = p.filter(pl.col("unit_level") == ruhmad.LEVEL)
    q = stats.bh_fdr(gp["p_m_med"].to_numpy().astype(np.float64))
    res["V-R7"] = {"vorreldud": gp.height, "erinevusi": int((~_close(q, gp["q_m_med"].to_numpy())).sum())}

    total = sum(int(v["erinevusi"]) for v in res.values())  # type: ignore[call-overload]
    for k_, v in res.items():
        log.info("%s: %s", k_, v)
    (RES / "validatsioon_ruhmad.json").write_text(
        json.dumps({"kontrollid": res, "erinevusi_kokku": total}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    log.info("KOKKU erinevusi: %d", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
