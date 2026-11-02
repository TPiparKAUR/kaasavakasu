"""Metoodika v3 kontroll V-R1: v3 tulemuste ökosüsteemi ja alamökosüsteemi read võrreldes v2 tulemustega.

v2 tulemused loetakse git'ist (commit ``V2_COMMIT``, failid ``data/tulemused/*``), v3 tulemused töökataloogist.
v3 lisab ainult taseme ``ruhm`` (kuivad ja märjad metsad) ja paaritatud tasemete veerud (``level_*_m_med``,
``sum_w_m_med``); kõik v2 read ja veerud peavad olema samad. Kuna v3 jaoks arvutati ka plokitabelid arhiivist uuesti,
kontrollib see ühtlasi kogu ahela reprodutseeritavust.

Väljund: ``data/tulemused/validatsioon_v2_v3.json``; lõpetab koodiga 1, kui leidub erinevusi.

Käivitus: ``uv run python scripts/vordle_v2.py``
"""

from __future__ import annotations

import io
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "tulemused"
V2_COMMIT = "de7aca9"
#: Ujukomaarvude tolerants (lisaks loetakse, mitu väärtust on bitti-bitti samad).
ABS_TOL, REL_TOL = 1e-12, 1e-9

#: fail -> võtmeveerud
FILES: dict[str, list[str]] = {
    "paarid.parquet": ["layer_id", "unit_level", "unit_code", "pair"],
    "lahtrid.parquet": ["layer_id", "unit_level", "unit_code", "state"],
    "klassid.parquet": ["layer_id", "cls"],
    "algklassid.parquet": ["layer_id", "unit_level", "unit_code", "seisund_algne"],
    "jaotused.parquet": ["layer_id", "unit_level", "unit_code", "state", "bin"],
    "diagnostika.parquet": ["layer_id", "eco_code"],
    "uhikud.parquet": ["unit_level", "unit_code"],
    "paarid_segumudel.parquet": ["layer_id", "unit_level", "unit_code", "pair"],
    "lahtrid_segumudel.parquet": ["layer_id", "unit_level", "unit_code", "state"],
    "tundlikkus.csv": ["variant", "unit_level"],
    "parameetrid.csv": [],
    "teenused_lisa.csv": ["id", "meetod"],
}

log = logging.getLogger("vordle_v2")


def _read_v2(name: str) -> pl.DataFrame:
    raw = subprocess.run(
        ["git", "show", f"{V2_COMMIT}:data/tulemused/{name}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return pl.read_parquet(io.BytesIO(raw)) if name.endswith(".parquet") else pl.read_csv(io.BytesIO(raw))


def _read_v3(name: str) -> pl.DataFrame:
    p = RES / name
    return pl.read_parquet(p) if name.endswith(".parquet") else pl.read_csv(p)


def compare(name: str, keys: list[str]) -> dict[str, object]:
    """Võrdle ühte faili; tagasta kokkuvõte (puuduvad/lisaread, erinevad veerud)."""
    a = _read_v2(name)
    b = _read_v3(name)
    if "unit_level" in b.columns:
        b = b.filter(pl.col("unit_level") != "ruhm")
    out: dict[str, object] = {"v2_ridu": a.height, "v3_ridu_v2_tasemetel": b.height}
    missing_cols = [c for c in a.columns if c not in b.columns]
    out["puuduvad_veerud"] = missing_cols
    if not keys:
        ok = a.equals(b.select(a.columns)) if not missing_cols else False
        out["erinevusi"] = 0 if ok else 1
        return out
    a = a.with_row_index("_ra")
    b = b.with_row_index("_rb")
    j = a.join(b, on=keys, how="full", suffix="__v3", coalesce=True, nulls_equal=True)
    only_v2 = j.filter(pl.col("_rb").is_null()).height
    only_v3 = j.filter(pl.col("_ra").is_null()).height
    j = j.filter(pl.col("_ra").is_not_null() & pl.col("_rb").is_not_null())
    diffs: dict[str, dict[str, object]] = {}
    n_cells = n_bitwise = 0
    for c in a.columns:
        if c in keys or c == "_ra" or c in missing_cols:
            continue
        cv3 = f"{c}__v3"
        x, y = j[c], j[cv3]
        if x.dtype.is_numeric() and y.dtype.is_numeric():
            xv, yv = x.cast(pl.Float64).to_numpy(), y.cast(pl.Float64).to_numpy()
            both_nan = np.isnan(xv) & np.isnan(yv)
            same_bits = both_nan | (xv == yv)
            close = both_nan | (np.abs(xv - yv) <= ABS_TOL + REL_TOL * np.abs(xv))
            n_cells += xv.size
            n_bitwise += int(same_bits.sum())
            if (~close).any():
                d = np.abs(xv - yv)[~close]
                diffs[c] = {"ridu": int((~close).sum()), "max_abs": float(np.nanmax(d))}
        else:
            neq = ~(x.eq_missing(y.cast(x.dtype)))
            n_cells += x.len()
            n_bitwise += int((~neq).sum())
            if neq.any():
                diffs[c] = {"ridu": int(neq.sum())}
    out.update(
        {
            "ainult_v2": only_v2,
            "ainult_v3": only_v3,
            "vorreldud_vaartusi": n_cells,
            "bitti_bitti_samu": n_bitwise,
            "erinevad_veerud": diffs,
            "erinevusi": only_v2 + only_v3 + len(diffs) + len(missing_cols),
        }
    )
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    report: dict[str, object] = {
        "v2_commit": V2_COMMIT,
        "tolerants": {"abs": ABS_TOL, "rel": REL_TOL},
        "failid": {},
    }
    total = 0
    for name, keys in FILES.items():
        if not (RES / name).exists():
            log.warning("%s: v3 fail puudub", name)
            report["failid"][name] = {"erinevusi": 1, "markus": "v3 fail puudub"}  # type: ignore[index]
            total += 1
            continue
        r = compare(name, keys)
        report["failid"][name] = r  # type: ignore[index]
        total += int(r["erinevusi"])  # type: ignore[call-overload]
        log.info("%s: %s", name, json.dumps(r, ensure_ascii=False))
    report["erinevusi_kokku"] = total
    (RES / "validatsioon_v2_v3.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    log.info("KOKKU erinevusi: %d", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
