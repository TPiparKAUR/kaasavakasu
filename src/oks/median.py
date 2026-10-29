"""Täpsed pikslimediaanid kadudeta sagedustabelist (metoodika v2).

Sisend on ``aggregate.value_counts`` tabel (``e_km, n_km, kood, value, n``): iga erinev väärtus on oma rida koos
täpse pikslite arvuga, nii et iga piksel on üks vaatlus. Mediaan on sama, mis ``np.median`` kõigil valimi pikslitel
(paarisarvu korral kahe keskmise väärtuse keskmine); väärtusi ei rühmitata vahemikesse ega lähendata.

Klasside ühendi mediaan leitakse ilma pikslimassiivi kokku panemata: k-s järjestatud väärtus on vähim ``t``,
mille korral ``Σ_klass #{x <= t} >= k + 1``. Otsing käib poolitusega üle ujukomaarvude järjestuse (bittide
järjestus), mistõttu tulemus on alati üks andmetes esinev väärtus.

Ebakindlus: 10 km klastrite bootstrap samade multinomiaalsete kaaludega nagu ``stats`` (``cluster_boot_medians``).
Kaalud on täisarvud, seega on iga kordus tegelik klastrite tagasipanekuga valim ja selle mediaan leitakse täpselt.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import polars as pl
from numpy.typing import NDArray

#: Kordused x erinevad väärtused, millest alates kasutatakse poolitusotsingut tiheda maatriksi asemel.
_DENSE_MAX = 50_000_000
#: (Klaster, väärtus) ridade arv, millest alates ``cluster_boot_medians_seg`` ei pane ridu kokku (``np.unique``),
#: vaid otsib poolitusega üle ujukomaarvude järjestuse iga klastri sorteeritud väärtustel (väiksem mälu).
_UNIQUE_MAX = 5_000_000


def scan(val_dir: Path) -> pl.LazyFrame:
    """Sagedustabeli failid (üks ploki-rea kohta) ühe laisa tabelina."""
    return pl.scan_parquet(val_dir / "*.parquet")


def _key_fns(dtype: np.dtype[np.generic]) -> tuple[type[np.unsignedinteger], int]:
    if dtype == np.float32:
        return np.uint32, 32
    return np.uint64, 64


def _to_key(x: float, dtype: np.dtype[np.generic]) -> int:
    """Ujukomaarv -> märgita täisarv, mille järjestus on sama mis arvu järjestus."""
    ut, bits = _key_fns(dtype)
    u = int(np.array(x, dtype=dtype).view(ut))
    sign = 1 << (bits - 1)
    return (~u & ((1 << bits) - 1)) if u & sign else u | sign


def _from_key(k: int, dtype: np.dtype[np.generic]) -> np.floating:
    ut, bits = _key_fns(dtype)
    sign = 1 << (bits - 1)
    u = k & ~sign if k & sign else ~k & ((1 << bits) - 1)
    return np.asarray(u, dtype=ut).view(dtype).flat[0]


class ValueTable:
    """Iga baaskaardi koodi sorteeritud erinevad väärtused ja kumulatiivsed pikslite arvud (kõik plokid kokku)."""

    def __init__(self, data: dict[int, tuple[NDArray[np.floating], NDArray[np.int64]]]) -> None:
        self.data = data
        dts = {v.dtype for v, _ in data.values()}
        self.dtype: np.dtype[np.generic] = (
            np.dtype(np.float32) if dts == {np.dtype(np.float32)} else np.dtype(np.float64)
        )
        if self.dtype == np.float64:
            self.data = {k: (v.astype(np.float64), c) for k, (v, c) in data.items()}

    @classmethod
    def load(cls, val_dir: Path) -> ValueTable:
        """Loe sagedustabel koodi kaupa (Parqueti statistika jätab teiste koodide read lugemata)."""
        lf = scan(val_dir)
        koods = lf.select(pl.col("kood").unique()).collect()["kood"].to_list()
        data: dict[int, tuple[NDArray[np.floating], NDArray[np.int64]]] = {}
        for k in sorted(koods):
            d = (
                lf.filter(pl.col("kood") == k)
                .group_by("value")
                .agg(pl.col("n").sum())
                .sort("value")
                .collect()
            )
            data[int(k)] = (d["value"].to_numpy(), np.cumsum(d["n"].to_numpy().astype(np.int64)))
        return cls(data)

    def _arrays(self, koods: Iterable[int]) -> list[tuple[NDArray[np.floating], NDArray[np.int64]]]:
        return [self.data[k] for k in koods if k in self.data and self.data[k][1].size]

    def _zeros(self, arrs: list[tuple[NDArray[np.floating], NDArray[np.int64]]]) -> int:
        z = 0
        for v, c in arrs:
            i = int(np.searchsorted(v, 0, side="left"))
            if i < v.size and v[i] == 0:
                z += int(c[i] - (c[i - 1] if i else 0))
        return z

    def count(self, koods: Iterable[int], nonzero: bool = False) -> int:
        """Pikslite arv (``nonzero``: ainult nullist erinevad)."""
        arrs = self._arrays(koods)
        n = sum(int(c[-1]) for _, c in arrs)
        return n - self._zeros(arrs) if nonzero else n

    def total(self, koods: Iterable[int]) -> float:
        """Väärtuste summa (keskmise jaoks)."""
        s = 0.0
        for v, c in self._arrays(koods):
            s += float(np.dot(v.astype(np.float64), np.diff(c, prepend=0)))
        return s

    def _kth(self, arrs: list[tuple[NDArray[np.floating], NDArray[np.int64]]], k: int, zeros: int) -> float:
        """k-s (0-põhine) järjestatud väärtus; ``zeros > 0`` jätab nullid välja."""
        lo = _to_key(min(float(v[0]) for v, _ in arrs), self.dtype)
        hi = _to_key(max(float(v[-1]) for v, _ in arrs), self.dtype)
        while lo < hi:
            mid = (lo + hi) // 2
            t = _from_key(mid, self.dtype)
            f = 0
            for v, c in arrs:
                j = int(np.searchsorted(v, t, side="right"))
                if j:
                    f += int(c[j - 1])
            if zeros and t >= 0:
                f -= zeros
            if f >= k + 1:
                hi = mid
            else:
                lo = mid + 1
        return float(_from_key(lo, self.dtype))

    def median(self, koods: Iterable[int], nonzero: bool = False) -> tuple[int, float]:
        """Täpne mediaan klasside ühendis: ``(pikslite arv, mediaan)``; tühja valimi korral ``(0, nan)``."""
        arrs = self._arrays(koods)
        zeros = self._zeros(arrs) if nonzero else 0
        n = sum(int(c[-1]) for _, c in arrs) - zeros
        if n == 0:
            return 0, float("nan")
        a = self._kth(arrs, (n - 1) // 2, zeros)
        b = a if n % 2 else self._kth(arrs, n // 2, zeros)
        return n, (a + b) / 2


def cluster_boot_medians(
    cluster: NDArray[np.integer],
    value: NDArray[np.floating],
    count: NDArray[np.int64],
    W: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Täpsed bootstrap-mediaanid: kordus ``b`` võtab klastri ``c`` piksleid ``W[b, c]`` korda.

    Parameters
    ----------
    cluster, value, count
        Sagedustabeli read (klaster, väärtus, pikslite arv) ühe ühiku ja seisundi kohta.
    W
        Multinomiaalsed täisarvulised klastrite kaalud (``B`` x klastrite arv), sama mis ``stats``.

    Returns
    -------
    NDArray[np.float64]
        ``B`` mediaani (``nan``, kui kordusse ei satu ühtki pikslit).
    """
    B = W.shape[0]
    if value.size == 0:
        return np.full(B, np.nan)
    vals, vidx = np.unique(value, return_inverse=True)
    vidx = vidx.astype(np.int32)
    K = vals.size
    cl_u, cl_i = np.unique(cluster, return_inverse=True)
    cl_i = cl_i.astype(np.int32)
    Wc = W[:, cl_u]  # (B, klastrid)
    tot = Wc @ np.bincount(cl_i, weights=count, minlength=cl_u.size)
    rank_lo = np.floor((tot - 1) / 2)
    rank_hi = np.floor(tot / 2)
    out = np.full(B, np.nan)
    ok = tot > 0
    if B * K <= _DENSE_MAX and cl_u.size * K <= _DENSE_MAX:
        cnt = np.zeros((cl_u.size, K))
        np.add.at(cnt, (cl_i, vidx), count)
        cum = np.cumsum(Wc @ cnt, axis=1)  # (B, K)
        i_lo = (cum < (rank_lo + 1)[:, None]).sum(1)
        i_hi = (cum < (rank_hi + 1)[:, None]).sum(1)
    else:
        # poolitus väärtuste indeksil: iga klastri kohta sorteeritud indeksid ja kumulatiivne arv
        order = np.lexsort((vidx, cl_i))
        ci, vi, ct = cl_i[order], vidx[order], count[order]
        starts = np.searchsorted(ci, np.arange(cl_u.size + 1))
        per = [
            (c, vi[starts[c] : starts[c + 1]], np.cumsum(ct[starts[c] : starts[c + 1]]))
            for c in range(cl_u.size)
        ]

        def kth(rank: NDArray[np.float64]) -> NDArray[np.int64]:
            lo = np.zeros(B, dtype=np.int64)
            hi = np.full(B, K - 1, dtype=np.int64)
            while np.any(lo < hi):
                mid = (lo + hi) // 2
                f = np.zeros(B)
                for c, v, cs in per:
                    j = np.searchsorted(v, mid, side="right")
                    f += Wc[:, c] * np.where(j > 0, cs[np.maximum(j - 1, 0)], 0)
                hit = f >= rank + 1
                hi = np.where(hit, mid, hi)
                lo = np.where(hit, lo, mid + 1)
            return lo

        i_lo, i_hi = kth(rank_lo), kth(rank_hi)
    i_lo, i_hi = np.minimum(i_lo, K - 1), np.minimum(i_hi, K - 1)
    out[ok] = (vals[i_lo[ok]].astype(np.float64) + vals[i_hi[ok]].astype(np.float64)) / 2
    return out


def _keys(x: NDArray[np.floating]) -> NDArray[np.unsignedinteger]:
    """``_to_key`` massiivina: märgita täisarvud, mille järjestus on sama mis ujukomaarvude järjestus."""
    ut, bits = _key_fns(x.dtype)
    u = x.view(ut)
    sign = ut(1 << (bits - 1))
    return np.where(u & sign, ~u, u | sign).astype(ut)


def _values(k: NDArray[np.unsignedinteger], dtype: np.dtype[np.generic]) -> NDArray[np.floating]:
    """``_from_key`` massiivina."""
    ut, bits = _key_fns(dtype)
    k = k.astype(ut)
    sign = ut(1 << (bits - 1))
    return np.where(k & sign, k & ~sign, ~k).astype(ut).view(dtype)


Segments = list[tuple[int, NDArray[np.floating], NDArray[np.int64]]]


def segments(batches: Iterable[pl.DataFrame]) -> Segments:
    """(klaster, väärtus, ``n``) partiidest iga klastri sorteeritud väärtused ja kumulatiivsed pikslite arvud.

    Klaster ei tohi ulatuda üle partii piiri. Mälus on korraga üks partii ja kompaktne tulemus (väärtus +
    kumulatiivne arv rea kohta).
    """
    out: Segments = []
    for d in batches:
        if d.is_empty():
            continue
        d = d.sort("cl", "value")
        cl = d["cl"].to_numpy()
        v = d["value"].to_numpy()
        n = d["n"].to_numpy().astype(np.int64)
        del d
        cut = np.flatnonzero(cl[1:] != cl[:-1]) + 1
        for a, b in zip(np.r_[0, cut], np.r_[cut, cl.size], strict=True):
            out.append((int(cl[a]), v[a:b].copy(), np.cumsum(n[a:b])))
    return out


def cluster_boot_medians_seg(seg: Segments, W: NDArray[np.float64]) -> NDArray[np.float64]:
    """``cluster_boot_medians`` klastrite segmentidest (``segments``); sama täpne tulemus.

    Väikese valimi korral pannakse read kokku ja kasutatakse ``cluster_boot_medians``-i; suure valimi korral
    leitakse iga korduse k-s väärtus vähima ``t``-na, mille korral ``Σ_c W[b, c] · #{x_c <= t} >= k + 1``, poolitusega
    üle ujukomaarvude järjestuse (nagu ``ValueTable._kth``), ilma erinevate väärtuste ühise massiivita.
    """
    B = W.shape[0]
    rows = sum(v.size for _, v, _ in seg)
    if rows == 0:
        return np.full(B, np.nan)
    if rows <= _UNIQUE_MAX:
        cl = np.concatenate([np.full(v.size, c, dtype=np.int64) for c, v, _ in seg])
        val = np.concatenate([v for _, v, _ in seg])
        cnt = np.concatenate([np.diff(cs, prepend=0) for _, _, cs in seg])
        return cluster_boot_medians(cl, val, cnt, W)
    dts = {v.dtype for _, v, _ in seg}
    dtype = np.dtype(np.float32) if dts == {np.dtype(np.float32)} else np.dtype(np.float64)
    seg = [(c, v.astype(dtype, copy=False), cs) for c, v, cs in seg]
    ids = np.array([c for c, _, _ in seg])
    Wc = W[:, ids]
    tot = Wc @ np.array([float(cs[-1]) for _, _, cs in seg])
    lo0 = _keys(np.array([min(v[0] for _, v, _ in seg)], dtype=dtype))[0]
    hi0 = _keys(np.array([max(v[-1] for _, v, _ in seg)], dtype=dtype))[0]

    def kth(rank: NDArray[np.float64]) -> NDArray[np.floating]:
        lo = np.full(B, lo0, dtype=np.uint64)
        hi = np.full(B, hi0, dtype=np.uint64)
        while np.any(lo < hi):
            mid = lo + (hi - lo) // 2
            t = _values(mid, dtype)
            f = np.zeros(B)
            for i, (_c, v, cum) in enumerate(seg):
                j = np.searchsorted(v, t, side="right")
                f += Wc[:, i] * np.where(j > 0, cum[np.maximum(j - 1, 0)], 0)
            hit = f >= rank + 1
            hi = np.where(hit, mid, hi)
            lo = np.where(hit, lo, mid + 1)
        return _values(lo, dtype)

    out = np.full(B, np.nan)
    ok = tot > 0
    a = kth(np.floor((tot - 1) / 2)).astype(np.float64)
    b = kth(np.floor(tot / 2)).astype(np.float64)
    out[ok] = (a[ok] + b[ok]) / 2
    return out
