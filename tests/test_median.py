"""Täpsete mediaanide testid: sagedustabelist arvutatud mediaan == np.median toorpikslitel."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import pytest

from oks import aggregate, median


def _table(tmp_path: Path, x: np.ndarray, kood: np.ndarray, e_km: np.ndarray) -> median.ValueTable:
    d = tmp_path / "val"
    d.mkdir()
    for i, n_km in enumerate((6500, 6501)):
        sel = np.arange(x.size) % 2 == i
        aggregate.value_counts(e_km[sel], kood[sel], x[sel]).with_columns(
            pl.lit(n_km, dtype=pl.Int16).alias("n_km")
        ).write_parquet(d / f"n{n_km}.parquet")
    return median.ValueTable.load(d)


@pytest.mark.parametrize("dtype", [np.float32, np.uint16, np.int32, np.float64])
def test_union_median_matches_numpy(tmp_path: Path, dtype: type) -> None:
    rng = np.random.default_rng(11)
    n = 30_001
    if np.dtype(dtype).kind == "f":
        x = (rng.normal(2, 3, n)).astype(dtype)
    else:
        x = rng.integers(0, 50 if dtype == np.uint16 else 10**7, n).astype(dtype)
    x[rng.random(n) < 0.45] = 0
    kood = rng.choice([10110, 10120, 10141, 20200], n)
    vt = _table(tmp_path, x, kood, rng.integers(400, 403, n))
    for ks in ([10110], [10110, 10141], [10110, 10120, 10141, 20200], [99999]):
        sel = np.isin(kood, ks)
        n_all, m_all = vt.median(ks)
        assert n_all == sel.sum()
        if sel.any():
            assert m_all == np.median(x[sel].astype(np.float64))
            xs = x[sel][x[sel] != 0].astype(np.float64)
            n_nz, m_nz = vt.median(ks, nonzero=True)
            assert n_nz == xs.size and m_nz == np.median(xs)
            assert vt.total(ks) == pytest.approx(float(x[sel].astype(np.float64).sum()))
        else:
            assert np.isnan(m_all)


@pytest.mark.parametrize("dense", [True, False])
def test_cluster_bootstrap_medians_are_exact(dense: bool, monkeypatch: pytest.MonkeyPatch) -> None:
    if not dense:
        monkeypatch.setattr(median, "_DENSE_MAX", 0)
    rng = np.random.default_rng(5)
    n_cl, npx = 40, 6000
    cl = rng.integers(0, n_cl, npx)
    x = np.where(rng.random(npx) < 0.5, 0.0, np.round(rng.gamma(2, 3, npx), 1))
    W = rng.multinomial(n_cl, np.full(n_cl, 1 / n_cl), size=200).astype(np.float64)
    # sagedustabel (klaster, väärtus)
    key, cnt = np.unique(np.stack([cl, x]), axis=1, return_counts=True)
    got = median.cluster_boot_medians(key[0].astype(np.int64), key[1], cnt.astype(np.int64), W)
    want = np.array(
        [np.median(np.repeat(x, W[b][cl].astype(int))) if W[b][cl].sum() else np.nan for b in range(200)]
    )
    np.testing.assert_array_equal(got, want)
