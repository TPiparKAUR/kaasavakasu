"""Tulemused -> veebilehe andmed (kompaktne JSON) ja allalaaditavad CSV-d."""

from __future__ import annotations

import json
import math
import shutil
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from . import catalog, config, stats, vordlus

#: Ümardus (olulisi numbreid) JSON-is; täpsed väärtused on CSV-s.
SIG = 5

#: Allalaaditava ``tulemused_paarid.csv`` veerud: ``paarid.parquet`` veerg -> CSV veerg (järjekord = CSV järjekord).
#: Metoodika v2: ainult mediaanipõhised hinnangud; keskmisepõhised paaride hinnangud (``delta_m``, ``delta_u`` jt) ei
#: ole CSV-s, et neid ei aetaks segi. ``keskmine_*`` on seisundi kirjeldav keskmine (stsenaariumi pindalaarvutus).
CSV_COLUMNS: dict[str, str] = {
    "teenus": "teenus",
    "layer_id": "kiht_id",
    "unit_level": "tase",
    "unit_code": "uksuse_kood",
    "uhik_nimi": "uksus",
    "pair": "seisundipaar",
    "res_m": "arvutuse_lahutus_m",
    "n_a": "pikslid_halvem",
    "n_b": "pikslid_parem",
    "median_a": "mediaan_halvem",
    "median_b": "mediaan_parem",
    "mean_a": "keskmine_halvem",
    "mean_b": "keskmine_parem",
    "delta_m_med": "paaritatud_delta",
    "rel_m_med": "paaritatud_delta_suhteline",
    "ci_m_med_lo": "paaritatud_ci95_alumine",
    "ci_m_med_hi": "paaritatud_ci95_ulemine",
    "p_m_med": "paaritatud_p",
    "q_m_med": "paaritatud_q_fdr",
    "oluline_m_med": "paaritatud_oluline",
    "enough_m": "paaritatud_andmeid_piisavalt",
    "n_strata": "paaritatud_paaride_arv",
    "n_clusters_m": "paaritatud_klastrite_arv",
    "median_d_m_med": "paaritatud_paarierinevuste_mediaan",
    "share_pos_m_med": "paaritatud_positiivsete_paaride_osa",
    "wilcoxon_p_med": "paaritatud_wilcoxon_p",
    "q_wilcoxon_med": "paaritatud_wilcoxon_q_fdr",
    "delta_u_med": "paaritamata_delta",
    "rel_u_med": "paaritamata_delta_suhteline",
    "ci_u_med_lo": "paaritamata_ci95_alumine",
    "ci_u_med_hi": "paaritamata_ci95_ulemine",
    "p_u_med": "paaritamata_p",
    "q_u_med": "paaritamata_q_fdr",
    "oluline_u_med": "paaritamata_oluline",
    "enough_u": "paaritamata_andmeid_piisavalt",
    "blocks_a": "paaritamata_plokke_halvem",
    "blocks_b": "paaritamata_plokke_parem",
    "cliff_u_med": "paaritamata_cliffi_delta_plokid",
    "mw_p_med": "paaritamata_mann_whitney_p_plokid",
    "kooskolas_med": "oluline_molemal_hinnangul",
}


def _r(x: object) -> object:
    """Ümarda ujukomaarv ``SIG`` olulise numbrini; ``NaN``/``inf`` -> ``None``."""
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        if not math.isfinite(x):
            return None
        if x == 0:
            return 0
        return round(x, SIG - 1 - int(math.floor(math.log10(abs(x)))))
    return x


def _rows(df: pl.DataFrame, cols: list[str]) -> list[list[object]]:
    return [[_r(v) for v in row] for row in df.select(cols).iter_rows()]


def build_data(results: Path, out: Path, sensitivity: Path | None = None) -> dict[str, Any]:
    """Koosta ``meta.json``, ``paarid.json``, ``lahtrid.json``, ``klassid.json`` ja CSV-d.

    Parameters
    ----------
    results
        ``data/tulemused`` (``analysis.run`` väljund).
    out
        Väljundkaust (``site/data``).
    sensitivity
        Valikuline tundlikkuse kokkuvõtte CSV.
    """
    out.mkdir(parents=True, exist_ok=True)
    paarid = pl.read_parquet(results / "paarid.parquet")
    lahtrid = pl.read_parquet(results / "lahtrid.parquet")
    klassid = pl.read_parquet(results / "klassid.parquet")
    diag = pl.read_parquet(results / "diagnostika.parquet")
    units = pl.read_parquet(results / "uhikud.parquet").with_row_index("ui")
    classes = pl.read_parquet(config.DERIVED / "klassid_kasutusel.parquet")
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    extra = results / "teenused_lisa.csv"
    layer_ids = sorted(set(paarid["layer_id"].unique().to_list()))
    cat = cat.filter(pl.col("id").is_in(layer_ids))
    order = {lid: i for i, lid in enumerate(cat.sort(["grupp", "nimi"])["id"].to_list())}
    layer_ids = sorted(layer_ids, key=lambda i: order[i])
    li = {lid: i for i, lid in enumerate(layer_ids)}
    unit_ix = {(r["unit_level"], r["unit_code"]): r["ui"] for r in units.iter_rows(named=True)}

    methods: dict[str, str] = {}
    notes: dict[str, str] = {}
    if extra.exists():
        ex = pl.read_csv(extra).unique("id", keep="first", maintain_order=True)  # segumudeli rida on lisarida
        methods = dict(ex.select("id", "meetod").iter_rows())
        notes = {k: v for k, v in ex.select("id", "markus").iter_rows() if v}

    teenused = []
    for lid in layer_ids:
        r = cat.filter(pl.col("id") == lid).row(0, named=True)
        d = diag.filter(pl.col("layer_id") == lid)
        eta = {
            str(row["eco_code"]): [_r(row["eta2_det"]), _r(row["eta2_alam"]), _r(row["eta2_state_in_alam"])]
            for row in d.iter_rows(named=True)
        }
        teenused.append(
            {
                "id": lid,
                "nimi": r["nimi"],
                "pealkiri": r["title"],
                "grupp": r["grupp"],
                "grupp_kood": r["grupp_kood"],
                "omadus": r["omadus"],
                "tuup": r["vaartuse_tuup"],
                "uhik": r["uhik"],
                "markus": r["markus"],
                "tabeli_markus": r["comments"],
                "res": r["spatial_resolution"],
                "allikas": r["data_origin"],
                "kirjeldus": r["abstract"],
                "eta2": eta,
                "meetod": methods.get(lid, "paaritatud"),
                "lahutus_markus": notes.get(lid, ""),
                "nodata_valja": lid in catalog.NODATA_EXCLUDED,
                "definitsiooniline": lid in catalog.DEFINITIONAL,
                "aasta": next((int(s) for s in lid.split("_") if s.isdigit() and len(s) == 4), None),
            }
        )

    uhikud = [
        {
            "tase": r["unit_level"],
            "kood": r["unit_code"],
            "nimi": r["nimi"],
            "eco": r["eco_code"],
            "pind": [_r(r[f"pind_{s}"]) for s in stats.STATES],
        }
        for r in units.iter_rows(named=True)
    ]
    cl = classes.select(
        "idx", "kood", "tuup", "seisund_algne", "seisund", "alam_kood", "okosusteem_kood"
    ).sort("idx")
    # metoodika v2: veebi andmetes on ainult mediaanipõhised hinnangud; keskmisepõhised hinnangud (delta_m, delta_u jt)
    # jäävad ainult ``paarid.parquet``-i. ``mean_a``/``mean_b`` on seisundi kirjeldav keskmine, mitte hinnang.
    cols_p = [
        "layer_id",
        "unit_level",
        "unit_code",
        "pair",
        "n_a",
        "n_b",
        "mean_a",
        "mean_b",
        "blocks_a",
        "blocks_b",
        "n_strata",
        "n_clusters_m",
        "enough_m",
        "enough_u",
        "median_a",
        "median_b",
        "delta_u_med",
        "rel_u_med",
        "ci_u_med_lo",
        "ci_u_med_hi",
        "p_u_med",
        "q_u_med",
        "oluline_u_med",
        "delta_m_med",
        "rel_m_med",
        "ci_m_med_lo",
        "ci_m_med_hi",
        "p_m_med",
        "q_m_med",
        "oluline_m_med",
        "kooskolas_med",
    ]
    cols_p = [c for c in cols_p if c in paarid.columns]
    pr = paarid.with_columns(
        pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64).alias("layer_id"),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unit_ix[(s["unit_level"], s["unit_code"])], return_dtype=pl.Int64)
        .alias("unit_code"),
        pl.col("pair")
        .replace_strict({n: i for i, n in enumerate(stats.PAIR_NAMES)}, return_dtype=pl.Int64)
        .alias("pair"),
    ).with_columns(pl.col("unit_level").replace_strict({"okosusteem": 0, "alam": 1}, return_dtype=pl.Int64))
    lr = lahtrid.with_columns(
        pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unit_ix[(s["unit_level"], s["unit_code"])], return_dtype=pl.Int64)
        .alias("unit_code"),
        pl.col("state").replace_strict({s: i for i, s in enumerate(stats.STATES)}, return_dtype=pl.Int64),
    )
    cols_l = [
        "layer_id",
        "unit_code",
        "state",
        "n",
        "mean",
        "sd",
        "blocks",
        "q05",
        "q25",
        "q50",
        "q75",
        "q95",
        "median",
        "n_nz",
        "median_nz",
        "blocks_med",
        *[f"mq{q}" for q in stats.QNAMES],
        "blocks_med_nz",
        *[f"mq{q}_nz" for q in stats.QNAMES],
    ]
    cols_l = [c for c in cols_l if c in lahtrid.columns]
    kr = klassid.with_columns(pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64)).join(
        cl.select("idx", "kood"), left_on="cls", right_on="idx"
    )
    cols_k = [c for c in ["layer_id", "kood", "n", "mean", "sd", "median", "median_nz"] if c in kr.columns]

    params = pl.read_csv(results / "parameetrid.csv").row(0, named=True)
    meta = {
        "koostatud": date.today().isoformat(),
        "parameetrid": params,
        "seisundid": list(stats.STATES),
        "paarid": list(stats.PAIR_NAMES),
        "teenused": teenused,
        "uhikud": uhikud,
        "klassid": [
            {
                "kood": r["kood"],
                "tuup": r["tuup"],
                "seisund_algne": r["seisund_algne"],
                "seisund": r["seisund"],
                "alam": r["alam_kood"],
                "eco": r["okosusteem_kood"],
            }
            for r in cl.iter_rows(named=True)
        ],
        "paarid_veerud": cols_p,
        "lahtrid_veerud": cols_l,
        "klassid_veerud": cols_k,
    }
    (out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (out / "paarid.json").write_text(json.dumps(_rows(pr, cols_p), separators=(",", ":")), encoding="utf-8")
    (out / "lahtrid.json").write_text(json.dumps(_rows(lr, cols_l), separators=(",", ":")), encoding="utf-8")
    (out / "klassid.json").write_text(json.dumps(_rows(kr, cols_k), separators=(",", ":")), encoding="utf-8")
    _write_distributions(results, out, li, unit_ix)
    _write_median_extras(results, out, li, unit_ix)
    _write_comparison(results, out)
    if sensitivity is not None and sensitivity.exists():
        (out / "tundlikkus.json").write_text(
            json.dumps(pl.read_csv(sensitivity).to_dicts(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    # allalaaditav täpse väärtustega CSV: ainult mediaanipõhised hinnangud, selgete veerunimedega (CSV_COLUMNS)
    names = {lid: t["nimi"] for lid, t in zip(layer_ids, teenused, strict=True)}
    unames = {(r["unit_level"], r["unit_code"]): r["nimi"] for r in units.iter_rows(named=True)}
    csv = paarid.with_columns(
        pl.col("layer_id").replace_strict(names, return_dtype=pl.String).alias("teenus"),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unames[(s["unit_level"], s["unit_code"])], return_dtype=pl.String)
        .alias("uhik_nimi"),
    )
    keep = [c for c in CSV_COLUMNS if c in csv.columns]
    csv.select(keep).rename({c: CSV_COLUMNS[c] for c in keep}).write_csv(out / "tulemused_paarid.csv")
    return meta


def _write_median_extras(
    results: Path, out: Path, li: dict[str, int], unit_ix: dict[tuple[str, int], int]
) -> None:
    """Kirjuta ``algklassid.json`` (mediaan algse seisundiklassi kaupa) ja ``segumudel.json`` (võrdlus, uuriv)."""
    state_ix = {s: i for i, s in enumerate(stats.STATES)}
    alg = results / "algklassid.parquet"
    if alg.exists():
        a = pl.read_parquet(alg).filter(pl.col("layer_id").is_in(list(li)))
        rows = [
            [
                li[r["layer_id"]],
                unit_ix[(r["unit_level"], int(r["unit_code"]))],
                r["seisund_algne"],
                state_ix[r["state"]],
                r["n"],
                _r(r["mean"]),
                _r(r["median"]),
                _r(r["median_nz"]),
            ]
            for r in a.iter_rows(named=True)
        ]
        (out / "algklassid.json").write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")
    seg = results / "paarid_segumudel.parquet"
    if seg.exists():
        m = pl.read_parquet(seg).filter(pl.col("layer_id").is_in(list(li)))
        pairs = {n: i for i, n in enumerate(stats.PAIR_NAMES)}
        rows = [
            [
                li[r["layer_id"]],
                unit_ix[(r["unit_level"], int(r["unit_code"]))],
                pairs[r["pair"]],
                _r(r["delta_m"]),
                _r(r["ci_m_lo"]),
                _r(r["ci_m_hi"]),
                _r(r.get("q_m")),
            ]
            for r in m.iter_rows(named=True)
        ]
        (out / "segumudel.json").write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")


def _write_comparison(results: Path, out: Path) -> None:
    """Kirjuta ``vordlus.json`` ja kopeeri võrdluse CSV-d (``scripts/vordle_metoodikad.py`` väljund)."""
    kf, pf = results / "vordlus_kihid.csv", results / "vordlus_paarid.csv"
    if not (kf.exists() and pf.exists()):
        return
    k = pl.read_csv(kf, infer_schema_length=None).filter(pl.col("nimi").is_not_null())
    p = pl.read_csv(pf, infer_schema_length=None)
    cols = [
        "nimi",
        "pohjus",
        "kate_v1",
        "kate_v2",
        "abs_rel_valim_mediaan",
        "abs_rel_statistik_mediaan",
        "osa_mediaan_null",
        "olulisi_v1",
        "olulisi_v2_keskmine",
        "olulisi_v2_mediaan",
        "suund_muutus",
        "hinnang_lisandus",
    ]
    muutus = {
        lvl: {
            part: dict(p.filter(pl.col("unit_level") == lvl).group_by(f"muutus_{part}").len().iter_rows())
            for part in ("valim", "statistik", "kokku")
        }
        for lvl in ("okosusteem", "alam")
    }
    c = (
        pl.read_csv(results / "vordlus_lahtrid.csv", infer_schema_length=None)
        .with_columns(pl.col("mean_v2", "median_v2").cast(pl.Float64))
        .filter(pl.col("mean_v2").is_not_null())
    )
    lahtrid = {
        "n": c.height,
        **{
            k: _r(v)
            for k, v in c.select(
                ((pl.col("median_v2") == 0) & (pl.col("mean_v2") > 0)).mean().alias("osa_mediaan_null"),
                (pl.col("median_v2") < pl.col("mean_v2")).mean().alias("osa_mediaan_vaiksem"),
            )
            .row(0, named=True)
            .items()
        },
    }
    data = {
        "pohjused": vordlus.CAUSES,
        "lahtrid": lahtrid,
        "klassid": list(vordlus.SIG_CLASSES),
        "kihid_veerud": cols,
        "kihid": _rows(k.sort("pohjus", "nimi"), cols),
        "muutus": muutus,
    }
    (out / "vordlus.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    for f in ("kihid", "lahtrid", "paarid"):
        src = results / f"vordlus_{f}.csv"
        if src.exists():
            shutil.copyfile(src, out / src.name)


def _write_distributions(
    results: Path, out: Path, li: dict[str, int], unit_ix: dict[tuple[str, int], int]
) -> None:
    """Kirjuta ``jaotused.json``: vahemikud kihi kaupa ja osakaalud (baaspunktides) üksuse × seisundi kaupa."""
    pq, js = results / "jaotused.parquet", results / "jaotuse_vahemikud.json"
    if not (pq.exists() and js.exists()):
        return
    specs_raw = json.loads(js.read_text(encoding="utf-8"))
    dist = pl.read_parquet(pq)
    state_ix = {s: i for i, s in enumerate(stats.STATES)}
    specs: dict[str, object] = {}
    rows: list[list[object]] = []
    for lid, spec in specs_raw.items():
        if lid not in li:
            continue
        nb = int(spec["n_bins"])
        specs[str(li[lid])] = {
            "kind": spec["kind"],
            "nbins": spec["nbins"],
            "n_bins": nb,
            "edges": [_r(float(v)) for v in spec["edges"]],
        }
        d = dist.filter(pl.col("layer_id") == lid)
        for (level, code, state), g in d.group_by(["unit_level", "unit_code", "state"]):
            counts = [0] * (nb + 1)
            for b, n in zip(g["bin"].to_list(), g["n"].to_list(), strict=True):
                counts[int(b)] = int(n)
            total = sum(counts[:nb])
            if total == 0:
                continue
            shares = [round(c / total * 10000) for c in counts[:nb]]
            rows.append(
                [
                    li[lid],
                    unit_ix[(level, int(code))],
                    state_ix[state],
                    shares,
                    round(counts[nb] / total * 10000),
                ]
            )
    (out / "jaotused.json").write_text(
        json.dumps({"spec": specs, "rows": rows}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
