"""Seisundiklasside (vilets -> keskmine -> hea) võrdlus ökosüsteemi ja alamökosüsteemi sees.

Sisend on ühe teenuse plokitabel ``(e_km, n_km, cls, n, sum, sumsq)`` (vt ``aggregate``) ja
klassitabel (``baas.class_lut`` teine tulemus). Kõik hinnangud tuletatakse summadest, nii et
toorpikslid pole enam vajalikud.

Põhimõtted (täpne põhjendus: ``docs/metoodika.md``):

* **Paaritatud hinnang** (peamine): stratum = (1 km plokk, alamökosüsteem). Kui stratumis on
  mõlemad võrreldavad seisundid vähemalt ``min_area_ha`` ulatuses, on stratumi erinevus
  ``d = keskmine_parem - keskmine_halvem``; kaal ``w = n_a n_b / (n_a + n_b)``. See kontrollib
  asukoha ja alamökosüsteemi koosseisu mõju.
* **Paaritamata hinnang** (täiendav): pindalakaalutud keskmiste vahe kõigil pikslitel.
  Ökosüsteemi tasemel on see toorhinnang (koosseisu mõju sees).
* **Olulisus**: ``cluster_blocks`` x ``cluster_blocks`` km klastrite bootstrap (arvestab ruumilist
  autokorrelatsiooni); mitmese testimise parandus Benjamini-Hochberg (FDR).
* **Kontroll**: plokitasandi Mann-Whitney (+ Cliffi delta) ja stratumite Wilcoxon, mis on
  ruumilise sõltuvuse tõttu optimistlikud ja mõeldud ainult kooskõla kontrolliks.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl
from numpy.typing import NDArray
from scipy import stats as sps

from . import median

log = logging.getLogger(__name__)

#: Seisundi indeks kasvab kvaliteediga: 0 = vilets, 1 = keskmine, 2 = hea.
STATES = ("vilets", "keskmine", "hea")
#: Võrdlused kujul (halvem, parem); Δ = parem - halvem.
PAIRS: tuple[tuple[int, int], ...] = ((0, 1), (1, 2), (0, 2))
PAIR_NAMES = ("vilets→keskmine", "keskmine→hea", "vilets→hea")

#: Baaskaardi ulatus km-des (EPSG:3301), kasutatakse klastrite ruudustikuks.
E_MIN, E_MAX, N_MIN, N_MAX = 369, 740, 6377, 6635


@dataclass(frozen=True)
class Params:
    """Analüüsi parameetrid."""

    cluster_blocks: int = 10
    n_boot: int = 4000
    min_area_ha: float = 1.0
    min_strata: int = 20
    min_clusters: int = 5
    seed: int = 20261019
    alpha: float = 0.05


@dataclass(frozen=True)
class Units:
    """Analüüsiühikud: ökosüsteemid ``0..n_eco-1`` ja seejärel alamökosüsteemid."""

    eco_codes: tuple[int, ...]
    alam_codes: tuple[int, ...]
    cls_alam: NDArray[np.int32]  # klassiindeks -> alam-ühiku indeks (0..n_alam-1)
    cls_eco: NDArray[np.int32]  # klassiindeks -> ökosüsteemi indeks
    cls_state: NDArray[np.int8]  # klassiindeks -> 0 vilets, 1 keskmine, 2 hea
    alam_eco: NDArray[np.int32]  # alam-ühiku indeks -> ökosüsteemi indeks

    @property
    def n_eco(self) -> int:
        return len(self.eco_codes)

    @property
    def n_alam(self) -> int:
        return len(self.alam_codes)

    @property
    def n_units(self) -> int:
        return self.n_eco + self.n_alam


def make_units(used: pl.DataFrame) -> Units:
    """Koosta ühikute tabelid ``baas.class_lut`` klassitabelist.

    Alamökosüsteem on kaasatud ainult siis, kui tal on baaskaardil vähemalt kaks seisundit.
    Klassid, mille alamökosüsteem sellest nimekirjast välja jääb, saavad alam-indeksiks ``-1``.
    """
    eco_codes = tuple(sorted(used["okosusteem_kood"].unique().to_list()))
    n_states = used.group_by("alam_kood").agg(pl.col("uld").n_unique().alias("k"))
    alam_codes = tuple(sorted(n_states.filter(pl.col("k") >= 2)["alam_kood"].to_list()))
    alam_ix = {c: i for i, c in enumerate(alam_codes)}
    eco_ix = {c: i for i, c in enumerate(eco_codes)}
    n = int(used["idx"].to_numpy().max()) + 1
    cls_alam = np.full(n, -1, dtype=np.int32)
    cls_eco = np.full(n, -1, dtype=np.int32)
    cls_state = np.full(n, -1, dtype=np.int8)
    alam_eco = np.full(len(alam_codes), -1, dtype=np.int32)
    for r in used.iter_rows(named=True):
        i = r["idx"]
        cls_eco[i] = eco_ix[r["okosusteem_kood"]]
        cls_state[i] = 3 - int(r["uld"])
        if r["alam_kood"] in alam_ix:
            cls_alam[i] = alam_ix[r["alam_kood"]]
            alam_eco[alam_ix[r["alam_kood"]]] = cls_eco[i]
    return Units(eco_codes, alam_codes, cls_alam, cls_eco, cls_state, alam_eco)


def bh_fdr(p: NDArray[np.float64]) -> NDArray[np.float64]:
    """Benjamini-Hochbergi FDR-korrigeeritud p-väärtused (``NaN`` jäävad ``NaN``-iks)."""
    q = np.full_like(p, np.nan, dtype=np.float64)
    ok = np.isfinite(p)
    pv = p[ok]
    m = pv.size
    if m == 0:
        return q
    order = np.argsort(pv, kind="stable")
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def cluster_index(e_km: NDArray[np.int64], n_km: NDArray[np.int64], cs: int) -> tuple[NDArray[np.int64], int]:
    """Klastri indeks (``cs`` x ``cs`` km ruudud) ja klastrite koguarv."""
    ncn = -(-(N_MAX - N_MIN) // cs)
    nce = -(-(E_MAX - E_MIN) // cs)
    ce = np.clip((e_km - E_MIN) // cs, 0, nce - 1)
    cn = np.clip((n_km - N_MIN) // cs, 0, ncn - 1)
    return ce * ncn + cn, nce * ncn


def cluster_expr(cs: int) -> pl.Expr:
    """``cluster_index`` Polarsi avaldisena (veerud ``e_km``, ``n_km``); sama täisarvjagamine ja piirid."""
    ncn = -(-(N_MAX - N_MIN) // cs)
    nce = -(-(E_MAX - E_MIN) // cs)
    ce = ((pl.col("e_km").cast(pl.Int64) - E_MIN) // cs).clip(0, nce - 1)
    cn = ((pl.col("n_km").cast(pl.Int64) - N_MIN) // cs).clip(0, ncn - 1)
    return ce * ncn + cn


def _boot_weights(n_clusters: int, n_boot: int, seed: int) -> NDArray[np.float64]:
    """Multinoomsed klastrite kaalud (``n_boot`` x ``n_clusters``); sama kõigi kihtide jaoks."""
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_clusters, np.full(n_clusters, 1.0 / n_clusters), size=n_boot).astype(np.float64)


def _boot_summary(
    obs: NDArray[np.float64], boot: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """95 % persentiilvahemik ja kahepoolne bootstrap-p (``NaN`` kui kehtivaid kordusi < 90 %)."""
    n_boot = boot.shape[0]
    valid = np.isfinite(boot)
    frac = valid.mean(axis=0)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # kõik-NaN veerud on lubatud (-> NaN)
        lo = np.nanpercentile(boot, 2.5, axis=0)
        hi = np.nanpercentile(boot, 97.5, axis=0)
        le = np.nansum(boot <= 0, axis=0)
        ge = np.nansum(boot >= 0, axis=0)
        nv = valid.sum(axis=0)
        p = 2 * np.minimum(le, ge) / np.maximum(nv, 1)
        # pehme alampiir 1/(B+1): p ei ole null
        p = np.maximum(p, 1.0 / (n_boot + 1))
    bad = frac < 0.9
    p = np.where(bad | ~np.isfinite(obs), np.nan, np.minimum(p, 1.0))
    lo = np.where(bad, np.nan, lo)
    hi = np.where(bad, np.nan, hi)
    return lo, hi, p


def _ratio(num: NDArray[np.float64], den: NDArray[np.float64]) -> NDArray[np.float64]:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def _scatter(
    shape: tuple[int, ...], idx: tuple[NDArray[np.int64], ...], vals: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Summa ``vals`` indeksite ``idx`` järgi tensorisse kujuga ``shape`` (kiirem kui ``np.add.at``)."""
    flat = np.ravel_multi_index(idx, shape)
    return np.bincount(flat, weights=vals, minlength=int(np.prod(shape))).reshape(shape)


def _unit_sums(df: pl.DataFrame, u: Units, cs: int) -> tuple[pl.DataFrame, int]:
    """Lisa klastri, alam- ja ökosüsteemi/seisundi veerud; tagasta ka klastrite arv."""
    cl, ncl = cluster_index(
        df["e_km"].to_numpy().astype(np.int64), df["n_km"].to_numpy().astype(np.int64), cs
    )
    cls = df["cls"].to_numpy().astype(np.int64)
    out = df.with_columns(
        pl.Series("cluster", cl),
        pl.Series("alam", u.cls_alam[cls]),
        pl.Series("eco", u.cls_eco[cls]),
        pl.Series("state", u.cls_state[cls].astype(np.int64)),
        pl.col("n").cast(pl.Int64),
    )
    return out, ncl


def analyse_layer(
    tbl: pl.DataFrame, u: Units, res_m: float, p: Params, weights: NDArray[np.float64] | None = None
) -> dict[str, pl.DataFrame]:
    """Analüüsi üks teenus.

    Parameters
    ----------
    tbl
        Plokitabel (``e_km, n_km, cls, n, sum, sumsq``).
    u
        Ühikute tabelid (``make_units``).
    res_m
        Rastri piksli külg meetrites (määrab minimaalse piksliarvu ``min_area_ha`` järgi).
    p
        Parameetrid.
    weights
        Eelarvutatud bootstrap-kaalud (vaikimisi genereeritakse ``p.seed`` järgi).

    Returns
    -------
    dict[str, pl.DataFrame]
        ``paarid`` (ühik x võrdlus), ``lahtrid`` (ühik x seisund) ja ``klassid`` (detailne kood).
    """
    if tbl.is_empty():
        return {k: pl.DataFrame() for k in ("paarid", "lahtrid", "klassid")}
    n_min = max(1, int(round(p.min_area_ha * 10_000 / res_m**2)))
    df, ncl = _unit_sums(tbl, u, p.cluster_blocks)
    W = weights if weights is not None else _boot_weights(ncl, p.n_boot, p.seed)
    nu = u.n_units
    ne = u.n_eco

    # ---------- paaritamata: (klaster, ühik, seisund) summad ----------
    d = df.filter(pl.col("eco") >= 0)
    cl = d["cluster"].to_numpy()
    st = d["state"].to_numpy()
    nn = d["n"].to_numpy().astype(np.float64)
    ss = d["sum"].to_numpy()
    s2 = d["sumsq"].to_numpy()
    eco = d["eco"].to_numpy()
    alam = d["alam"].to_numpy()
    m_al = alam >= 0
    shape = (ncl, nu, 3)
    N, S, S2 = (
        _scatter(shape, (cl, eco, st), v) + _scatter(shape, (cl[m_al], ne + alam[m_al], st[m_al]), v[m_al])
        for v in (nn, ss, s2)
    )

    tot_n, tot_s, tot_s2 = N.sum(0), S.sum(0), S2.sum(0)  # (nu, 3)
    mean = _ratio(tot_s, tot_n)
    with np.errstate(invalid="ignore", divide="ignore"):
        var = (tot_s2 - tot_s**2 / np.where(tot_n > 0, tot_n, np.nan)) / (tot_n - 1)
    sd = np.sqrt(np.maximum(var, 0))

    cl_a = (N > 0).sum(0)  # klastreid iga (ühik, seisund) kohta
    # bootstrap: keskmised seisundi kaupa (B, nu, 3)
    Nb = np.tensordot(W, N, axes=(1, 0))
    Sb = np.tensordot(W, S, axes=(1, 0))
    meanb = _ratio(Sb, Nb)

    # ---------- plokitasand: paaritamata (Mann-Whitney) ja paaritatud strata ----------
    blk = (
        d.filter(pl.col("alam") >= 0)
        .group_by(["e_km", "n_km", "alam", "state"])
        .agg(pl.col("n").sum(), pl.col("sum").sum(), pl.col("cluster").first(), pl.col("eco").first())
    )
    blk_eco = d.group_by(["e_km", "n_km", "eco", "state"]).agg(pl.col("n").sum(), pl.col("sum").sum())

    bm_eco = {
        k: (f["sum"] / f["n"]).to_numpy()
        for k, f in blk_eco.filter(pl.col("n") >= n_min).partition_by(["eco", "state"], as_dict=True).items()
    }
    bm_alam = {
        k: (f["sum"] / f["n"]).to_numpy()
        for k, f in blk.filter(pl.col("n") >= n_min).partition_by(["alam", "state"], as_dict=True).items()
    }
    empty = np.empty(0)

    def block_means(level: str, unit: int, state: int) -> NDArray[np.float64]:
        return (bm_eco if level == "okosusteem" else bm_alam).get((unit, state), empty)

    # strata: (plokk, alam) x seisund -> n, sum
    wide = blk.pivot(
        on="state", index=["e_km", "n_km", "alam", "cluster", "eco"], values=["n", "sum"]
    ).fill_null(0)
    for s in range(3):
        for col in ("n", "sum"):
            nm = f"{col}_{s}"
            if nm not in wide.columns:
                wide = wide.with_columns(pl.lit(0.0).alias(nm))
    wide = wide.with_columns([pl.col(f"n_{s}").cast(pl.Float64) for s in range(3)])
    stratum_alam = wide["alam"].to_numpy()
    stratum_eco = wide["eco"].to_numpy()
    stratum_cl = wide["cluster"].to_numpy()
    nsa = np.stack([wide[f"n_{s}"].to_numpy() for s in range(3)], 1)
    ssa = np.stack([wide[f"sum_{s}"].to_numpy().astype(np.float64) for s in range(3)], 1)

    # paaritatud tensor: (ncl, nu, pair) -> Σw·d, Σw, Σw·mean_a, nstrata
    M_wd, M_w, M_wa, M_cnt = (np.zeros((ncl, nu, 3)) for _ in range(4))
    diffs: dict[tuple[int, int], list[NDArray[np.float64]]] = {}
    for pi, (a, b) in enumerate(PAIRS):
        ok = (nsa[:, a] >= n_min) & (nsa[:, b] >= n_min)
        if not ok.any():
            continue
        ma = ssa[ok, a] / nsa[ok, a]
        mb = ssa[ok, b] / nsa[ok, b]
        dd = mb - ma
        ww = nsa[ok, a] * nsa[ok, b] / (nsa[ok, a] + nsa[ok, b])
        c_ok, al_ok, ec_ok = stratum_cl[ok], stratum_alam[ok], stratum_eco[ok]
        for unit_ix in (ec_ok, ne + al_ok):
            sh = (ncl, nu)
            M_wd[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * dd)
            M_w[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww)
            M_wa[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * ma)
            M_cnt[:, :, pi] += _scatter(sh, (c_ok, unit_ix), np.ones_like(ww))
        for uix in np.unique(ec_ok):
            diffs.setdefault((int(uix), pi), []).append(dd[ec_ok == uix])
        for uix in np.unique(al_ok):
            diffs.setdefault((ne + int(uix), pi), []).append(dd[al_ok == uix])
    Wdb = np.tensordot(W, M_wd, axes=(1, 0))
    Wwb = np.tensordot(W, M_w, axes=(1, 0))
    m_boot = _ratio(Wdb, Wwb)  # (B, nu, 3)
    m_obs = _ratio(M_wd.sum(0), M_w.sum(0))
    ma_obs = _ratio(M_wa.sum(0), M_w.sum(0))
    m_cnt = M_cnt.sum(0)
    m_ncl = (M_cnt > 0).sum(0)

    pair_rows: list[dict[str, object]] = []
    for ui in range(nu):
        level = "okosusteem" if ui < ne else "alam"
        code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
        for pi, (a, b) in enumerate(PAIRS):
            na, nb = tot_n[ui, a], tot_n[ui, b]
            if na == 0 or nb == 0:
                continue
            du = mean[ui, b] - mean[ui, a]
            boot_u = meanb[:, ui, b] - meanb[:, ui, a]
            lo_u, hi_u, p_u = _boot_summary(np.array([du]), boot_u[:, None])
            lo_m, hi_m, p_m = _boot_summary(np.array([m_obs[ui, pi]]), m_boot[:, ui, pi][:, None])
            uk = ui if level == "okosusteem" else ui - ne
            xa, xb = block_means(level, uk, a), block_means(level, uk, b)
            cliff = mw_p = np.nan
            if xa.size >= 5 and xb.size >= 5:
                r = sps.mannwhitneyu(xb, xa, alternative="two-sided", method="asymptotic")
                cliff = 2 * r.statistic / (xa.size * xb.size) - 1
                mw_p = float(r.pvalue)
            dlist = diffs.get((ui, pi))
            wil_p = med_d = share_pos = np.nan
            if dlist:
                dv = np.concatenate(dlist)
                med_d, share_pos = float(np.median(dv)), float((dv > 0).mean())
                if dv.size >= 10 and np.any(dv != 0):
                    wil_p = float(sps.wilcoxon(dv, method="approx").pvalue)
            enough = bool(m_cnt[ui, pi] >= p.min_strata and m_ncl[ui, pi] >= p.min_clusters)
            enough_u = bool(
                min(xa.size, xb.size) >= p.min_strata and min(cl_a[ui, a], cl_a[ui, b]) >= p.min_clusters
            )
            ma0 = ma_obs[ui, pi]
            pair_rows.append(
                {
                    "unit_level": level,
                    "unit_code": int(code),
                    "pair": PAIR_NAMES[pi],
                    "n_a": int(na),
                    "n_b": int(nb),
                    "mean_a": mean[ui, a],
                    "mean_b": mean[ui, b],
                    "sd_a": sd[ui, a],
                    "sd_b": sd[ui, b],
                    "delta_u": du,
                    "rel_u": du / abs(mean[ui, a]) if abs(mean[ui, a]) > 1e-12 else np.nan,
                    "ci_u_lo": lo_u[0],
                    "ci_u_hi": hi_u[0],
                    "p_u": p_u[0] if enough_u else np.nan,
                    "cliff_u": cliff,
                    "mw_p": mw_p,
                    "blocks_a": int(xa.size),
                    "blocks_b": int(xb.size),
                    "n_strata": int(m_cnt[ui, pi]),
                    "n_clusters_m": int(m_ncl[ui, pi]),
                    "delta_m": m_obs[ui, pi],
                    "rel_m": m_obs[ui, pi] / abs(ma0) if np.isfinite(ma0) and abs(ma0) > 1e-12 else np.nan,
                    "ci_m_lo": lo_m[0],
                    "ci_m_hi": hi_m[0],
                    "p_m": p_m[0] if enough else np.nan,
                    "median_d_m": med_d,
                    "share_pos_m": share_pos,
                    "wilcoxon_p": wil_p,
                    "enough_m": enough,
                    "enough_u": enough_u,
                }
            )

    cell_rows: list[dict[str, object]] = []
    for ui in range(nu):
        level = "okosusteem" if ui < ne else "alam"
        code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
        for s in range(3):
            if tot_n[ui, s] == 0:
                continue
            xs = block_means(level, ui if level == "okosusteem" else ui - ne, s)
            q = np.quantile(xs, [0.05, 0.25, 0.5, 0.75, 0.95]) if xs.size else np.full(5, np.nan)
            cell_rows.append(
                {
                    "unit_level": level,
                    "unit_code": int(code),
                    "state": STATES[s],
                    "n": int(tot_n[ui, s]),
                    "mean": mean[ui, s],
                    "sd": sd[ui, s],
                    "blocks": int(xs.size),
                    "q05": q[0],
                    "q25": q[1],
                    "q50": q[2],
                    "q75": q[3],
                    "q95": q[4],
                }
            )

    # ---------- detailsete klasside keskmised (annus-vastus algsel skaalal) ----------
    g = tbl.group_by("cls").agg(
        pl.col("n").cast(pl.Int64).sum().alias("n"), pl.col("sum").sum(), pl.col("sumsq").sum()
    )
    g = g.with_columns(
        (pl.col("sum") / pl.col("n")).alias("mean"),
        (
            ((pl.col("sumsq") - pl.col("sum") ** 2 / pl.col("n")) / (pl.col("n") - 1))
            .clip(lower_bound=0)
            .sqrt()
        ).alias("sd"),
    ).select("cls", "n", "mean", "sd")
    return {"paarid": pl.DataFrame(pair_rows), "lahtrid": pl.DataFrame(cell_rows), "klassid": g}


QUANTS = (0.05, 0.25, 0.5, 0.75, 0.95)
QNAMES = ("05", "25", "50", "75", "95")


def _block_medians(blk: pl.DataFrame, u: Units) -> pl.DataFrame:
    """Plokimediaanid (``aggregate.segment_medians``) ühiku indeksi ja seisundi indeksiga.

    ``eco`` rühmitus annab ökosüsteemi ühikud, ``alam`` rühmitus alamökosüsteemi ühikud (``ne + j``; ainult
    ``u.alam_codes``). Seisund: ``uld`` 1/2/3 -> 2/1/0 (hea/keskmine/vilets).
    """
    eco_ix = {c: i for i, c in enumerate(u.eco_codes)}
    alam_ix = {c: u.n_eco + j for j, c in enumerate(u.alam_codes)}
    b = blk.with_columns(
        (pl.col("group") // 10).alias("code"), (3 - pl.col("group") % 10).cast(pl.Int64).alias("state")
    )
    parts = []
    for name, ix in (("eco", eco_ix), ("alam", alam_ix)):
        d = b.filter((pl.col("grouping") == name) & pl.col("code").is_in(list(ix)))
        parts.append(d.with_columns(pl.col("code").replace_strict(ix, return_dtype=pl.Int64).alias("unit")))
    return pl.concat(parts).select(
        "grouping", "unit", "state", "e_km", "n_km", "n", "median", "n_nz", "median_nz"
    )


def analyse_layer_median(
    blk: pl.DataFrame,
    val_dir: Path,
    u: Units,
    used: pl.DataFrame,
    res_m: float,
    p: Params,
    weights: NDArray[np.float64] | None = None,
    unpaired_boot: bool = True,
) -> dict[str, pl.DataFrame]:
    """Mediaanipõhised hinnangud (metoodika v2), keskmisepõhiste (``analyse_layer``) kõrvale.

    * Paaritamata: ühiku ja seisundi täpne pikslimediaan (``vt``); Δ = mediaanide vahe; ebakindlus sama 10 km
      klastrite bootstrapiga (täpne kordusemediaan, ``median.cluster_boot_medians``).
    * Paaritatud: stratumi (1 km plokk x alamökosüsteem) erinevus ``d = mediaan_parem - mediaan_halvem``;
      stratumite koondamine ja bootstrap nagu ``analyse_layer`` (kaal ``w = n_a n_b / (n_a + n_b)``).
    * Plokitasand: Mann-Whitney ja kvantiilid plokimediaanidest (kõik pikslid ja nullist erinevad).

    Parameters
    ----------
    blk
        Plokimediaanid (``pipeline.blkmed_path``).
    val_dir
        Sagedustabeli kaust (``pipeline.val_path``). ``median.ValueTable`` loetakse siin ja vabastatakse enne
        bootstrapi (suurte kihtide mälu); bootstrap loeb ühiku ja seisundi read eraldi.
    u, used
        Ühikud ja ``baas.class_lut`` klassitabel (``idx, kood, seisund_algne``).
    res_m, p, weights
        Nagu ``analyse_layer``.
    unpaired_boot
        Kas arvutada paaritamata mediaanide vahe bootstrap (tundlikkuse variantides ei ole vaja).

    Returns
    -------
    dict[str, pl.DataFrame]
        ``paarid``, ``lahtrid``, ``klassid`` (liidetakse ``analyse_layer`` tulemustele võtmete järgi) ja
        ``algklassid`` (ühik x algne seisundiklass).
    """
    n_min = max(1, int(round(p.min_area_ha * 10_000 / res_m**2)))
    ncl = cluster_index(np.array([E_MIN]), np.array([N_MIN]), p.cluster_blocks)[1]
    W = weights if weights is not None else _boot_weights(ncl, p.n_boot, p.seed)
    ne, nu = u.n_eco, u.n_units
    idx = used["idx"].to_numpy()
    kood = used["kood"].to_numpy()

    def koods_of(ui: int, s: int) -> list[int]:
        m = (u.cls_eco[idx] == ui) if ui < ne else (u.cls_alam[idx] == ui - ne)
        return [int(k) for k in kood[m & (u.cls_state[idx] == s)]]

    # ---------- ühiku ja seisundi täpsed mediaanid ----------
    vt = median.ValueTable.load(val_dir)
    cells: dict[tuple[int, int], tuple[int, float, int, float]] = {}
    koods: dict[tuple[int, int], list[int]] = {}
    for ui in range(nu):
        for s in range(3):
            ks = koods_of(ui, s)
            n, m = vt.median(ks)
            if n == 0:
                continue
            cells[(ui, s)] = (n, m, *vt.median(ks, nonzero=True))
            koods[(ui, s)] = ks

    cls_rows = []
    for i, k in zip(idx, kood, strict=True):
        _n, m = vt.median([int(k)])
        nnz, mnz = vt.median([int(k)], nonzero=True)
        cls_rows.append({"cls": int(i), "median": m, "n_nz": nnz, "median_nz": mnz})

    alg_rows: list[dict[str, object]] = []
    letters = used["seisund_algne"].to_numpy()
    for ui in range(nu):
        level = "okosusteem" if ui < ne else "alam"
        code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
        in_u = (u.cls_eco[idx] == ui) if ui < ne else (u.cls_alam[idx] == ui - ne)
        for letter in sorted(set(letters[in_u].tolist())):
            m_l = in_u & (letters == letter)
            ks = [int(k) for k in kood[m_l]]
            n, m = vt.median(ks)
            if n == 0:
                continue
            nnz, mnz = vt.median(ks, nonzero=True)
            alg_rows.append(
                {
                    "unit_level": level,
                    "unit_code": int(code),
                    "seisund_algne": str(letter),
                    "state": STATES[int(u.cls_state[idx[m_l][0]])],
                    "n": n,
                    "mean": vt.total(ks) / n,
                    "median": m,
                    "n_nz": nnz,
                    "median_nz": mnz,
                }
            )
    del vt

    # ---------- plokimediaanid ----------
    bl = _block_medians(blk, u) if not blk.is_empty() else pl.DataFrame()
    bm: dict[tuple[int, int], NDArray[np.float64]] = {}
    bm_nz: dict[tuple[int, int], NDArray[np.float64]] = {}
    cl_a: dict[tuple[int, int], int] = {}
    if not bl.is_empty():
        for (ui, s), f in bl.partition_by(["unit", "state"], as_dict=True).items():
            key = (int(ui), int(s))
            big = f.filter(pl.col("n") >= n_min)
            bm[key] = big["median"].to_numpy()
            bm_nz[key] = big.filter(pl.col("n_nz") > 0)["median_nz"].to_numpy()
            cl = cluster_index(
                f["e_km"].to_numpy().astype(np.int64), f["n_km"].to_numpy().astype(np.int64), p.cluster_blocks
            )[0]
            cl_a[key] = int(np.unique(cl).size)
    empty = np.empty(0)

    # ---------- paaritatud: stratumi mediaanid ----------
    M_wd, M_w, M_wa, M_cnt = (np.zeros((ncl, nu, 3)) for _ in range(4))
    diffs: dict[tuple[int, int], list[NDArray[np.float64]]] = {}
    strata = bl.filter(pl.col("grouping") == "alam") if not bl.is_empty() else bl
    if not strata.is_empty():
        wide = strata.pivot(on="state", index=["e_km", "n_km", "unit"], values=["n", "median"])
        for s in range(3):
            for col, fill in (("n", 0.0), ("median", np.nan)):
                nm = f"{col}_{s}"
                if nm not in wide.columns:
                    wide = wide.with_columns(pl.lit(fill).alias(nm))
        unit = wide["unit"].to_numpy().astype(np.int64)
        eco = u.alam_eco[unit - ne].astype(np.int64)
        scl = cluster_index(
            wide["e_km"].to_numpy().astype(np.int64),
            wide["n_km"].to_numpy().astype(np.int64),
            p.cluster_blocks,
        )[0]
        nsa = np.stack([wide[f"n_{s}"].fill_null(0).to_numpy().astype(np.float64) for s in range(3)], 1)
        msa = np.stack([wide[f"median_{s}"].to_numpy().astype(np.float64) for s in range(3)], 1)
        for pi, (a, b) in enumerate(PAIRS):
            ok = (nsa[:, a] >= n_min) & (nsa[:, b] >= n_min)
            if not ok.any():
                continue
            ma, mb = msa[ok, a], msa[ok, b]
            dd = mb - ma
            ww = nsa[ok, a] * nsa[ok, b] / (nsa[ok, a] + nsa[ok, b])
            c_ok, un_ok, ec_ok = scl[ok], unit[ok], eco[ok]
            for unit_ix in (ec_ok, un_ok):
                sh = (ncl, nu)
                M_wd[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * dd)
                M_w[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww)
                M_wa[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * ma)
                M_cnt[:, :, pi] += _scatter(sh, (c_ok, unit_ix), np.ones_like(ww))
            for uix in np.unique(ec_ok):
                diffs.setdefault((int(uix), pi), []).append(dd[ec_ok == uix])
            for uix in np.unique(un_ok):
                diffs.setdefault((int(uix), pi), []).append(dd[un_ok == uix])
    m_boot = _ratio(np.tensordot(W, M_wd, axes=(1, 0)), np.tensordot(W, M_w, axes=(1, 0)))
    m_obs = _ratio(M_wd.sum(0), M_w.sum(0))
    ma_obs = _ratio(M_wa.sum(0), M_w.sum(0))
    m_cnt = M_cnt.sum(0)
    m_ncl = (M_cnt > 0).sum(0)

    # ---------- paaritamata: täpne klastribootstrap ----------
    boots: dict[tuple[int, int], NDArray[np.float64]] = {}
    if unpaired_boot:
        lf = median.scan(val_dir)
        for key, ks in koods.items():
            # (klaster, väärtus) kaupa koondatud loendus annab sama täpse mediaani kui pikslite read;
            # voogkoondamine hoiab mälu väikesena ka sadade miljonite sagedustabeli ridade korral
            rows = (
                lf.filter(pl.col("kood").is_in(ks))
                .group_by(cluster_expr(p.cluster_blocks).alias("cl"), "value")
                .agg(pl.col("n").cast(pl.Int64).sum())
                .collect(engine="streaming")
            )
            boots[key] = median.cluster_boot_medians(
                rows["cl"].to_numpy().astype(np.int32), rows["value"].to_numpy(), rows["n"].to_numpy(), W
            )
            del rows

    pair_rows: list[dict[str, object]] = []
    for ui in range(nu):
        level = "okosusteem" if ui < ne else "alam"
        code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
        for pi, (a, b) in enumerate(PAIRS):
            if (ui, a) not in cells or (ui, b) not in cells:
                continue
            med_a, med_b = cells[(ui, a)][1], cells[(ui, b)][1]
            du = med_b - med_a
            lo_u = hi_u = p_u = np.full(1, np.nan)
            if (ui, a) in boots and (ui, b) in boots:
                lo_u, hi_u, p_u = _boot_summary(np.array([du]), (boots[(ui, b)] - boots[(ui, a)])[:, None])
            lo_m, hi_m, p_m = _boot_summary(np.array([m_obs[ui, pi]]), m_boot[:, ui, pi][:, None])
            xa, xb = bm.get((ui, a), empty), bm.get((ui, b), empty)
            cliff = mw_p = np.nan
            if xa.size >= 5 and xb.size >= 5 and np.ptp(np.concatenate([xa, xb])) > 0:
                r = sps.mannwhitneyu(xb, xa, alternative="two-sided", method="asymptotic")
                cliff = 2 * r.statistic / (xa.size * xb.size) - 1
                mw_p = float(r.pvalue)
            dlist = diffs.get((ui, pi))
            wil_p = med_d = share_pos = np.nan
            if dlist:
                dv = np.concatenate(dlist)
                med_d, share_pos = float(np.median(dv)), float((dv > 0).mean())
                if dv.size >= 10 and np.any(dv != 0):
                    wil_p = float(sps.wilcoxon(dv, method="approx").pvalue)
            enough = bool(m_cnt[ui, pi] >= p.min_strata and m_ncl[ui, pi] >= p.min_clusters)
            enough_u = bool(
                min(xa.size, xb.size) >= p.min_strata
                and min(cl_a.get((ui, a), 0), cl_a.get((ui, b), 0)) >= p.min_clusters
            )
            ma0 = ma_obs[ui, pi]
            pair_rows.append(
                {
                    "unit_level": level,
                    "unit_code": int(code),
                    "pair": PAIR_NAMES[pi],
                    "median_a": med_a,
                    "median_b": med_b,
                    "delta_u_med": du,
                    "rel_u_med": du / abs(med_a) if abs(med_a) > 1e-12 else np.nan,
                    "ci_u_med_lo": lo_u[0],
                    "ci_u_med_hi": hi_u[0],
                    "p_u_med": p_u[0] if enough_u else np.nan,
                    "cliff_u_med": cliff,
                    "mw_p_med": mw_p,
                    "delta_m_med": m_obs[ui, pi],
                    "rel_m_med": m_obs[ui, pi] / abs(ma0)
                    if np.isfinite(ma0) and abs(ma0) > 1e-12
                    else np.nan,
                    "ci_m_med_lo": lo_m[0],
                    "ci_m_med_hi": hi_m[0],
                    "p_m_med": p_m[0] if enough else np.nan,
                    "median_d_m_med": med_d,
                    "share_pos_m_med": share_pos,
                    "wilcoxon_p_med": wil_p,
                }
            )

    cell_rows: list[dict[str, object]] = []
    for (ui, s), (_n, m, nnz, mnz) in sorted(cells.items()):
        level = "okosusteem" if ui < ne else "alam"
        code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
        row: dict[str, object] = {
            "unit_level": level,
            "unit_code": int(code),
            "state": STATES[s],
            "median": m,
            "n_nz": nnz,
            "median_nz": mnz,
        }
        for suf, xs in (("", bm.get((ui, s), empty)), ("_nz", bm_nz.get((ui, s), empty))):
            q = np.quantile(xs, QUANTS) if xs.size else np.full(len(QUANTS), np.nan)
            row[f"blocks_med{suf}"] = int(xs.size)
            row.update({f"mq{qn}{suf}": float(v) for qn, v in zip(QNAMES, q, strict=True)})
        cell_rows.append(row)

    return {
        "paarid": pl.DataFrame(pair_rows),
        "lahtrid": pl.DataFrame(cell_rows),
        "klassid": pl.DataFrame(cls_rows),
        "algklassid": pl.DataFrame(alg_rows),
    }


def eta_squared(
    tbl: pl.DataFrame, group: NDArray[np.int64], within: NDArray[np.int64] | None = None
) -> float:
    """Piksli-tasandi η²: osa dispersioonist, mida seletab ``group`` ``within``-kihtide sees.

    ``group`` ja ``within`` on kaardistused klassiindeksist rühma (``-1`` = välja jäetud).
    Kirjeldav näitaja, mitte olulisuse test (piksliandmed on ruumiliselt sõltuvad).
    """
    cls = tbl["cls"].to_numpy().astype(np.int64)
    g = group[cls]
    w = within[cls] if within is not None else np.zeros_like(g)
    ok = (g >= 0) & (w >= 0)
    d = pl.DataFrame(
        {
            "w": w[ok],
            "g": g[ok],
            "n": tbl["n"].to_numpy().astype(np.float64)[ok],
            "s": tbl["sum"].to_numpy()[ok],
            "s2": tbl["sumsq"].to_numpy()[ok],
        }
    )
    cells = d.group_by(["w", "g"]).agg(pl.col("n").sum(), pl.col("s").sum(), pl.col("s2").sum())
    strata = d.group_by("w").agg(pl.col("n").sum(), pl.col("s").sum(), pl.col("s2").sum())
    sn, ss, ss2 = (strata[c].to_numpy() for c in ("n", "s", "s2"))
    cn, cs = cells["n"].to_numpy(), cells["s"].to_numpy()
    ss_tot = float(np.sum(ss2 - ss**2 / sn))
    between = float(np.sum(cs**2 / cn) - np.sum(ss**2 / sn))
    return between / ss_tot if ss_tot > 0 else float("nan")
