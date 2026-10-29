# Metoodika koodiväljavõte: paaritatud hinnang ja mediaan (metoodika v2)

| | |
|---|---|
| Analüüsitud kood | vaikeharu `claude/compassionate-babbage-mdfftn`, commit `b799458` (`b799458d61433b152becf2eeb2ee057de56b41cb`), metoodika v2 |
| Koostatud | 2026-10-29, töö harus `claude/practical-knuth-zzw4kt`. Analüüsi käigus koodi ei muudetud. Hiljem parandati tellija otsusel üks viga (`indikaatorid.strength`, vt „Vajab täiendavat kontrolli“, punkt 3). Andmeid ei muudetud. |
| Ulatus | Kirjeldatud on ainult kehtiv metoodika v2. v1 (`5aa4596`) ei ole kirjeldatud. |
| Andmete päritolu | Kõik väärtused on **tuletatud näitajad** (derived): ELME teenusekihid (KAUR) ja baaskaart 2022 (5 m). Tegemist ei ole vaatlusandmetega. |
| Püsilink | `https://github.com/TPiparKAUR/kaasavakasu/blob/b799458d61433b152becf2eeb2ee057de56b41cb/<fail>#L<rida>` |

**Kuidas lugeda.** Koodiplokid on projekti tegelik kood, mis on kopeeritud muutmata kujul. Iga ploki pealkirjas on toodud fail ja read. Selgituseks lisatud kommentaarid algavad märgiga `# ▸` (Python) või `// ▸` (JavaScript). Kõik teised kommentaarid on originaalkoodist. Välja jäetud read on tähistatud kujul `# … (välja jäetud: …)`. Välja on jäetud ainult logimine, vahemälu, failiteed ja kuvamise vormistus, mitte arvutus. Loetavuse huvides on mõne funktsiooni päisest eemaldatud tüübimärgendid ja docstring ning mõni pikk loend või sõnastik on lühendatud `…`-ga. Arvutavad read on sõna-sõnalt originaalist.

**Mõisted.**

* **Piksel**: teenusekihi rakk (5 m või 10 m). Mediaanis on iga piksel üks vaatlus.
* **Plokk**: 1 × 1 km ruut EPSG:3301 ruudustikus. Piksel kuulub plokki oma keskpunkti järgi.
* **Ühik**:
  * ökosüsteem: rohumaad, sood, metsad, põllumaad;
  * alamökosüsteem: baaskaardi detailne tüüp, mis on kaasatud ainult siis, kui tal on vähemalt kaks seisundit.
* **Seisund**: vilets, keskmine või hea. Väli `seisund_uldine` võtab väärtused 3, 2 ja 1, koodis kasutatakse indekseid 0, 1 ja 2.
* **Stratum**: üks plokk × üks alamökosüsteem. See on paaritatud hinnangu „paar“.
* **Klaster**: 10 × 10 km ala, mida kasutatakse ruumilises bootstrapis.

### Arvutusahel ühe pildiga

```
ELME teenuse raster / vektor ──┐
Baaskaart OS_det_seisund_det 5 m ─┴─► oks aggregate / oks fields   (pipeline.py, aggregate.py)
        │  data/derived/plokid/{id}.parquet          Σn, Σx, Σx² (plokk × klass)         → keskmisepõhised hinnangud
        │  data/derived/plokid/{id}__val/            kadudeta sagedustabel                → täpsed mediaanid
        │  data/derived/plokid/{id}__blkmed.parquet  täpsed plokimediaanid                 → paaritatud hinnang (v2)
        │  data/derived/plokid/{id}__cls.parquet     klassi loendused                      → tulemustabeli staatus
        ▼
oks analyse   (analysis.py, stats.py, median.py)   → data/tulemused/paarid.parquet, lahtrid.parquet, algklassid.parquet
oks kaasnev   (kaasnev.py, median.py)              → data/tulemused/kaasnev_tuup_seisund.parquet, kaasnev_suured.parquet
oks site      (sitebuild.py, export.py, kaasnev_export.py) → site/data/*.json (5 olulise numbrini), *.csv (täpsed)
        ▼
Veebileht /v2/   (site_src/app.js, site_src/sections/*.js)
```

---

# PAARITATUD METOODIKA

## Ülevaade

Paaritatud hinnang võrdleb kahte seisundit samas kohas ja samas ökosüsteemitüübis. v2-s on veebis kasutusel
**mediaanipõhine** variant, veerg `delta_m_med`. See arvutatakse kolmes etapis:

1. Iga stratumi (1 km plokk × alamökosüsteem) sees leitakse mõlema seisundi **täpne pikslimediaan**.
2. Stratumi erinevus on `d = mediaan_parem − mediaan_halvem`.
3. Ühiku hinnang on erinevuste **kaalutud keskmine** `Δ = Σ w·d / Σ w`, kus kaal on `w = n_a·n_b / (n_a + n_b)` ja `n` on stratumi pikslite arv kummaski seisundis.

Ebakindlus arvutatakse 10 km klastrite bootstrapiga (B = 4000). Olulisuseks rakendatakse Benjamini–Hochbergi FDR-parandust iga taseme (ökosüsteem, alamökosüsteem) jaoks eraldi.

v2 koodis on alles ka **keskmisepõhine** variant, veerg `delta_m` (`stats.analyse_layer`). Selles on stratumi erinevus keskmiste vahe, kaal ja bootstrap on samad. See arvutatakse igal jooksul ja jõuab:

* tabelisse `paarid.parquet`;
* allalaaditavasse faili `tulemused_paarid.csv`;
* faili `paarid.json`, kus veerud on olemas, kuid veebi hinnangud neid ei kasuta;
* v1 → v2 võrdlusse (`vordlus.py`), kus see on teadlikult vahesamm „v2 keskmine“.

Mediaanipõhine Δ on kasutusel kõigis kohtades, kus kasutaja näeb hinnangut:

* veebi kuumkaart, teenuse detail, tabelivaade ja profiil;
* kvalitatiivne tõendusbaas (`tendus.json`) ja Exceli fail;
* `docs/tulemused.md`;
* tundlikkusanalüüs.

Täpsem kirjeldus on peatükis „Vajab täiendavat kontrolli“, punkt 1.

## Andmete liikumine

**P1. Kust andmed tulevad.**

* Analüüsitavad kihid võetakse ametlikust kihitabelist, kus `eval = TRUE`, ja lisaks lähtekasu lisakihid.
* Iga raster laaditakse alla ja loetakse 1 km ploki-ridade kaupa.
* Rastrid, mille lahutusvõime on üle 10 m (930 m, 1 km), viiakse enne arvutust lähima naabriga 10 m ruudustikule.
* Baaskaardi kood (ökosüsteem + algne seisund) võetakse teenuse ruudustikule lähima naabriga. Teenuse väärtusi ei interpoleerita.
* Vektorkihid rasterdatakse 10 m ruudustikule. Polügoonist väljas on NoData, mis loetakse nulliks.

**P2. Millised andmed valitakse.**

* **Kehtivad pikslid.** GDAL-i mask, NaN välja.
* **NoData ja ruudustikust väljas olevad pikslid.** Rastri NoData on kehtiv null. Teenuse ruudustikust väljapoole jääv baaskaardi ala on samuti NoData ehk null.
  * Erand on viis kihti (`NODATA_EXCLUDED`), kus NoData jäetakse välja.
* **Klassid.** Kaasatakse ainult seisundiga klassid (`uld` 1–3).
* **Alamökosüsteemid.** Ühikuks loetakse alamökosüsteem, millel on baaskaardil vähemalt kaks seisundit.

**P3. Kuidas moodustatakse paarid.**

* Agregeerimisel arvutatakse iga ploki ja rühma `alam_kood·10 + uld` kohta täpne pikslimediaan ja pikslite arv.
* Need read pööratakse laiaks tabeliks. Igal real on üks stratum (plokk × alamökosüsteem) ja kolme seisundi `n` ning mediaan.
* Seisundipaar (vilets→keskmine, keskmine→hea, vilets→hea) loetakse stratumis kehtivaks, kui mõlemas seisundis on vähemalt 1 ha pikslit:
  * 5 m kihil vähemalt 400 pikslit;
  * 10 m kihil vähemalt 100 pikslit.

**P4. Milliste tunnuste järgi paare võrreldakse.**

* Sama 1 km plokk annab sama asukoha, mullastiku ja kliima.
* Sama alamökosüsteem annab sama tüübi.
* Erinev on ainult ühtlustatud seisund.
* Kaal sõltub mõlema seisundi pikslite arvust.

**P5. Kuidas arvutatakse erinevused.** Iga kehtiva stratumi kohta arvutatakse `d = mb − ma` (parema seisundi mediaan miinus halvema seisundi mediaan) ja kaal `w = n_a·n_b/(n_a+n_b)`.

**P6. Kuidas saadakse lõplik näitaja.**

* **Δ.** `Δ = Σw·d / Σw` üle kõigi ühiku stratumite. Ökosüsteemi Δ koondab kõigi tema (kahe- või enama seisundiga) alamökosüsteemide stratumid.
* **Suhteline muutus.** `rel = Δ / |Σw·ma / Σw|`.
* **Usaldusvahemik ja p.** 95 % usaldusvahemik ja kahepoolne p tulevad 10 km klastrite bootstrapist.
* **Piisavus.** Hinnang on „piisav“, kui stratumeid on ≥ 20 ja klastreid ≥ 5. Muidu on p tühi.
* **FDR.** q leitakse kõigi kihtide ja paaride p-väärtustest koos, iga taseme kohta eraldi.
* **Olulisus.** „Oluline“ tähendab, et q < 0,05.

**P7. Kuidas tulemus jõuab väljundisse.**

1. `paarid.parquet` kirjutatakse täpsete väärtustega.
2. `paarid.json` ümardatakse 5 olulise numbrini.
3. Brauseris valib funktsioon `estOf(r, 'm')` mediaanipõhised veerud.
4. Need väärtused kuvatakse kuumkaardil, teenuse detailis, tabelis ja profiilis vormindusega `fmt`/`pct`.
5. `tendus.json` (kvalitatiivne tõendusbaas, stsenaariumi kontrollveerg, Excel) kasutab sama paaritatud hinnangut. Kui stratumeid ei ole piisavalt, kasutatakse paaritamata hinnangut.

## Kommenteeritud kood

### P1. Kust andmed tulevad

**Kihtide valik ja NoData reegel**: `src/oks/pipeline.py:223-243`, `src/oks/catalog.py:104-112, 271-292`

```python
# ▸ Loeme ametliku kihitabeli ja arhiivi failinimekirja.
cat = catalog.build_catalogue(
    config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
    config.ROOT / "data/arhiiv_failid.csv",
)
# ▸ Analüüsime kihte, mille eval = TRUE (ja lähtekasu lisakihte); siin ainult rastrid.
ev = catalog.evaluated(cat).filter(pl.col("tyyp") == "raster")
jobs = []
for r in ev.iter_rows(named=True):
    # … (välja jäetud: --only ja juba valmis kihtide vahelejätmine)
    jobs.append(
        (
            r["id"],
            r["fail"],
            catalog.EXTRA_INVALID.get(r["id"], ()),
            # ▸ Väärtused, mis loetakse kehtivaks nulliks (sh kihitabelis deklareeritud NoData).
            catalog.zero_values(r["id"], r["nodata"]),
            False,
            # ▸ Üle 10 m lahutusvõimega rastrid viiakse enne arvutust 10 m ruudustikule.
            bool(r["spatial_resolution"] > MAX_RES_M),
        )
    )
```

```python
# ▸ Viis erandkihti: nendes tähendab NoData puuduvat hinnangut, mitte nulli.
NODATA_EXCLUDED: frozenset[str] = frozenset(
    {
        "mustikad_pohlad_saagikus_2020_10m",
        "mustikad_pohlad_hind_2022_10m",
        "pohlad_saagikus_2020_10m",
        "kasemahl_saagikus_2020_10m",
        "kasemahl_hind_2022_10m",
    }
)

def zero_values(layer_id: str, nodata: float | None) -> tuple[float, ...]:
    vals: list[float] = []
    # ▸ NoData loetakse nulliks, v.a erandkihtides (seal ainult siis, kui NoData ise on 0).
    if nodata is not None and (layer_id not in NODATA_EXCLUDED or float(nodata) == 0.0):
        vals.append(float(nodata))
    # ▸ Lisaväärtused, mis tähendavad „teenust ei ole“ (ohusaaste kihis 255).
    vals.extend(ZERO_EXTRA.get(layer_id, ()))
    return tuple(dict.fromkeys(vals))
```

**Madalama lahutusvõimega rastrid 10 m-le**: `src/oks/pipeline.py:139-176`

```python
def resample_to_10m(src: Path, out: Path) -> Path:
    # … (välja jäetud: kaustade loomine, CRS-kontroll, GTiff-i profiili vormistus)
    # ▸ Sihtruudustik on baaskaardiga joondatud 10 m ruudustik (fields.X0, Y0, RES).
    "transform": from_origin(fields.X0, fields.Y0, fields.RES, fields.RES),
    "nodata": s.nodata,
    # …
            # ▸ Lähim naaber: väärtust ei interpoleerita ega skaleerita (kihid on hektaripõhised).
            reproject(
                source=rasterio.band(s, 1),
                destination=rasterio.band(d, 1),
                resampling=Resampling.nearest,
                src_nodata=s.nodata,
                dst_nodata=s.nodata,
            )
```

**Raster loetakse ploki-ridade kaupa ja baaskaart võetakse samale ruudustikule**: `src/oks/aggregate.py:300-338`, `137-165`

```python
with rasterio.open(src) as ds, rasterio.open(baas_det) as baas:
    # ▸ Nõuame, et kiht oleks EPSG:3301 (L-EST97) ja põhjasuunalise ruudustikuga.
    if ds.crs is None or ds.crs.to_epsg() != 3301:
        raise ValueError(f"{spec.id}: CRS ei ole EPSG:3301 ({ds.crs})")
    if ds.transform.e >= 0 or ds.transform.b != 0 or ds.transform.d != 0:
        raise ValueError(f"{spec.id}: ootamatu (mitte põhja-suunaline) transform")
    # ▸ Teenuse ruudustikku laiendatakse baaskaardi ulatuseni; lisanduvad pikslid on NoData (→ 0).
    grid, c0, g0 = extended_grid(ds, tuple(baas.bounds))
    t = grid.transform
    # ▸ Iga veeru 1 km ploki number piksli keskpunkti järgi (e_km).
    cx = t.c + (np.arange(grid.width) + 0.5) * t.a
    bcol = np.floor(cx / config.BLOCK_M).astype(np.int64)
    col_vals, col_inv = np.unique(bcol, return_inverse=True)
    same_grid = grid.transform == baas.transform and (grid.height, grid.width) == baas.shape
    invalid = np.asarray(spec.invalid, dtype=np.float64)
    # … (välja jäetud: sagedustabeli kausta tühjendamine)
    # ▸ Loeme rastri 1 km ploki-ridade kaupa (n_km = ploki rida).
    for r0, r1, brow in _row_runs(grid):
        val, mask = _read_padded(ds, grid, c0, g0, r0, r1)
        # ▸ Kehtivad pikslid ja NoData → 0 (vt P2).
        ok, val = validity(val, mask, invalid, spec.zero_values)
        # ▸ Baaskaardi koodid samadele pikslitele (lähim naaber, kui ruudustik erineb).
        codes = _baas_chunk(baas, grid, r0, r1, same_grid)
        # … (välja jäetud: klassitabeli loendused, vt mediaani osa M1; sagedustabel, vt M1)
        if val_dir is not None or groupings:
            e_all = col_vals[np.broadcast_to(col_inv, val.shape)]
            # …
            # ▸ Iga rühmituse (alam, eco) kohta: plokimediaanid (vt P3).
            for gname, garr in (groupings or {}).items():
                gid = garr[codes]
                sel = ok & (gid >= 0)
                if blk_med is None or not sel.any():
                    continue
                m = segment_medians(e_all[sel], gid[sel], val[sel].astype(np.float64))
                blk_med.append(
                    pl.DataFrame(m).with_columns(
                        pl.lit(gname).alias("grouping"), pl.lit(brow, dtype=pl.Int64).alias("n_km")
                    )
                )
```

```python
def _row_runs(ds: Grid) -> list[tuple[int, int, int]]:
    """Jaga rastri read 1 km ploki-ridadeks: ``(r0, r1, ploki_rida_n_km)``."""
    t = ds.transform
    # ▸ Rea keskpunkti y-koordinaat → 1 km ploki rida (n_km).
    cy = t.f + (np.arange(ds.height) + 0.5) * t.e
    brow = np.floor(cy / config.BLOCK_M).astype(np.int64)
    edges = np.flatnonzero(np.diff(brow)) + 1
    starts = np.concatenate(([0], edges))
    ends = np.concatenate((edges, [ds.height]))
    return [(int(a), int(b), int(brow[a])) for a, b in zip(starts, ends, strict=True)]

def _baas_chunk(baas, ds, r0, r1, same_grid):
    win = Window(0, r0, ds.width, r1 - r0)
    # ▸ Sama ruudustik (5 m kiht): loeme baaskaardi otse.
    if same_grid:
        return baas.read(1, window=win)
    # ▸ Muu ruudustik (nt 10 m): baaskaardi 5 m kood viiakse teenuse ruudustikule lähima naabriga.
    dst = np.zeros((r1 - r0, ds.width), dtype=np.uint16)
    reproject(
        source=rasterio.band(baas, 1),
        destination=dst,
        dst_transform=ds.transform @ Affine.translation(0, r0),
        dst_crs=ds.crs,
        resampling=Resampling.nearest,
        src_nodata=0,
        dst_nodata=0,
    )
    return dst
```

### P2. Millised andmed valitakse

**Kehtivad pikslid**: `src/oks/aggregate.py:123-134`

```python
ok = mask.copy()
# ▸ Ujukomakihtides jäetakse välja NaN ja lõpmatus.
if val.dtype.kind == "f":
    ok &= np.isfinite(val)
# ▸ Lisaks välistatavad sentinel-väärtused (v2-s tühi nimekiri).
if invalid.size:
    ok &= ~np.isin(val, invalid.astype(val.dtype))
if zero_values:
    # ▸ NoData (ja muud „teenust ei ole“ väärtused) loetakse kehtivaks …
    zero = np.isin(val, np.asarray(zero_values, dtype=val.dtype))
    ok |= zero
    if val.dtype.kind == "f":
        ok &= np.isfinite(val) | zero
    # ▸ … ja nende väärtuseks pannakse 0.
    val = np.where(zero, np.zeros((), dtype=val.dtype), val)
return ok, val
```

**Paaritamise rühmitus (ainult seisundiga klassid)**: `src/oks/pipeline.py:61-72`

```python
def groupings(classes: pl.DataFrame) -> dict[str, NDArray[np.int64]]:
    # ▸ Ainult seisundiga klassid: uld 1 = hea, 2 = keskmine, 3 = vilets.
    st = classes.filter(pl.col("uld").is_in([1, 2, 3]))
    out: dict[str, NDArray[np.int64]] = {}
    for name, col in (("alam", "alam_kood"), ("eco", "okosusteem_kood")):
        arr = np.full(65536, -1, dtype=np.int64)
        # ▸ Rühm = alamökosüsteemi (või ökosüsteemi) kood · 10 + seisund; „alam“ on paaritatud hinnangu stratum.
        arr[st["kood"].to_numpy()] = st[col].to_numpy().astype(np.int64) * 10 + st["uld"].to_numpy()
        out[name] = arr
    return out
```

**Analüüsiühikud**: `src/oks/stats.py:84-107`

```python
def make_units(used: pl.DataFrame) -> Units:
    eco_codes = tuple(sorted(used["okosusteem_kood"].unique().to_list()))
    # ▸ Alamökosüsteem on ühik ainult siis, kui tal on baaskaardil vähemalt kaks seisundit.
    n_states = used.group_by("alam_kood").agg(pl.col("uld").n_unique().alias("k"))
    alam_codes = tuple(sorted(n_states.filter(pl.col("k") >= 2)["alam_kood"].to_list()))
    # … (välja jäetud: indeksite sõnastikud ja massiivide loomine)
    for r in used.iter_rows(named=True):
        i = r["idx"]
        cls_eco[i] = eco_ix[r["okosusteem_kood"]]
        # ▸ Seisundi indeks: uld 3 (vilets) → 0, 2 (keskmine) → 1, 1 (hea) → 2.
        cls_state[i] = 3 - int(r["uld"])
        if r["alam_kood"] in alam_ix:
            cls_alam[i] = alam_ix[r["alam_kood"]]
            # ▸ Iga alamökosüsteem kuulub ühte ökosüsteemi.
            alam_eco[alam_ix[r["alam_kood"]]] = cls_eco[i]
    return Units(eco_codes, alam_codes, cls_alam, cls_eco, cls_state, alam_eco)
```

### P3. Kuidas moodustatakse paarid

**Täpne mediaan iga ploki ja rühma kohta**: `src/oks/aggregate.py:221-244`

```python
def segment_medians(e_km, group, x):
    # ▸ Järjestame pikslid: plokk (e_km), rühm (alam·10+seisund), väärtus.
    o = np.lexsort((x, group, e_km))
    e, g, v = e_km[o], group[o], x[o]
    # ▸ Leiame iga (plokk, rühm) lõigu alguse ja pikslite arvu n.
    st = np.flatnonzero(np.concatenate(([True], (e[1:] != e[:-1]) | (g[1:] != g[:-1]))))
    n = np.diff(np.append(st, v.size))
    # ▸ Mediaan: paaritu n korral keskmine element, paarisarvu korral kahe keskmise keskmine.
    med = (v[st + (n - 1) // 2] + v[st + n // 2]) / 2
    # ▸ Sama ainult nullist erinevate pikslite kohta (lisanäitaja, paaritamisel ei kasutata).
    neg = np.add.reduceat((v < 0).astype(np.int64), st)
    zer = np.add.reduceat((v == 0).astype(np.int64), st)
    nnz = n - zer
    med_nz = np.full(n.size, np.nan)
    h = nnz > 0
    lo, hi = (nnz[h] - 1) // 2, nnz[h] // 2
    pick_lo = v[st[h] + lo + np.where(lo >= neg[h], zer[h], 0)]
    pick_hi = v[st[h] + hi + np.where(hi >= neg[h], zer[h], 0)]
    med_nz[h] = (pick_lo + pick_hi) / 2
    return {"e_km": e[st], "group": g[st], "n": n, "median": med, "n_nz": nnz, "median_nz": med_nz}
```

**Plokimediaanid ühiku ja seisundi indeksiga**: `src/oks/stats.py:447-458`

```python
eco_ix = {c: i for i, c in enumerate(u.eco_codes)}
alam_ix = {c: u.n_eco + j for j, c in enumerate(u.alam_codes)}
# ▸ Rühmast tagasi: kood = rühm // 10, seisund = 3 − (rühm % 10) → 0 vilets, 1 keskmine, 2 hea.
b = blk.with_columns(
    (pl.col("group") // 10).alias("code"), (3 - pl.col("group") % 10).cast(pl.Int64).alias("state")
)
parts = []
for name, ix in (("eco", eco_ix), ("alam", alam_ix)):
    # ▸ Jätame alles ainult analüüsiühikud (alamökosüsteem vähemalt kahe seisundiga).
    d = b.filter((pl.col("grouping") == name) & pl.col("code").is_in(list(ix)))
    parts.append(d.with_columns(pl.col("code").replace_strict(ix, return_dtype=pl.Int64).alias("unit")))
return pl.concat(parts).select(
    "grouping", "unit", "state", "e_km", "n_km", "n", "median", "n_nz", "median_nz"
)
```

**Stratumid ja seisundipaarid (mediaanipõhine, veebis kasutusel)**: `src/oks/stats.py:499-501, 558, 574-601`

```python
# ▸ Minimaalne pikslite arv stratumis: 1 ha (5 m → 400 pikslit, 10 m → 100 pikslit).
n_min = max(1, int(round(p.min_area_ha * 10_000 / res_m**2)))
# ▸ Klastrite koguarv ruudustikus (10 km: 38 × 26 = 988) ja bootstrapi kaalud.
ncl = cluster_index(np.array([E_MIN]), np.array([N_MIN]), p.cluster_blocks)[1]
W = weights if weights is not None else _boot_weights(ncl, p.n_boot, p.seed)
# …
bl = _block_medians(blk, u) if not blk.is_empty() else pl.DataFrame()
# … (välja jäetud: plokikvantiilid, vt mediaani osa)

# ---------- paaritatud: stratumi mediaanid ----------
M_wd, M_w, M_wa, M_cnt = (np.zeros((ncl, nu, 3)) for _ in range(4))
diffs: dict[tuple[int, int], list[NDArray[np.float64]]] = {}
# ▸ Stratum = plokk × ALAMökosüsteem (ka ökosüsteemi taseme hinnangu jaoks).
strata = bl.filter(pl.col("grouping") == "alam") if not bl.is_empty() else bl
if not strata.is_empty():
    # ▸ Üks rida stratumi kohta; veerud n_0..n_2 ja median_0..median_2 (vilets, keskmine, hea).
    wide = strata.pivot(on="state", index=["e_km", "n_km", "unit"], values=["n", "median"])
    for s in range(3):
        for col, fill in (("n", 0.0), ("median", np.nan)):
            nm = f"{col}_{s}"
            if nm not in wide.columns:
                wide = wide.with_columns(pl.lit(fill).alias(nm))
    unit = wide["unit"].to_numpy().astype(np.int64)
    # ▸ Alamökosüsteemi ökosüsteem: sama stratum läheb ka ökosüsteemi hinnangusse.
    eco = u.alam_eco[unit - ne].astype(np.int64)
    # ▸ Stratumi 10 km klaster.
    scl = cluster_index(
        wide["e_km"].to_numpy().astype(np.int64),
        wide["n_km"].to_numpy().astype(np.int64),
        p.cluster_blocks,
    )[0]
    nsa = np.stack([wide[f"n_{s}"].fill_null(0).to_numpy().astype(np.float64) for s in range(3)], 1)
    msa = np.stack([wide[f"median_{s}"].to_numpy().astype(np.float64) for s in range(3)], 1)
    # ▸ Paarid (halvem a, parem b): (0,1) vilets→keskmine, (1,2) keskmine→hea, (0,2) vilets→hea.
    for pi, (a, b) in enumerate(PAIRS):
        # ▸ Stratum kõlbab, kui mõlemas seisundis on vähemalt 1 ha.
        ok = (nsa[:, a] >= n_min) & (nsa[:, b] >= n_min)
        if not ok.any():
            continue
```

### P4–P5. Võrdlustunnused ja erinevuste arvutus

`src/oks/stats.py:598-611`

```python
        # ▸ Stratumi halvema ja parema seisundi täpne pikslimediaan.
        ma, mb = msa[ok, a], msa[ok, b]
        # ▸ Stratumi erinevus: parema seisundi mediaan − halvema seisundi mediaan.
        dd = mb - ma
        # ▸ Kaal pikslite arvust: w = n_a·n_b / (n_a + n_b).
        ww = nsa[ok, a] * nsa[ok, b] / (nsa[ok, a] + nsa[ok, b])
        c_ok, un_ok, ec_ok = scl[ok], unit[ok], eco[ok]
        # ▸ Sama stratum lisatakse nii ökosüsteemi kui alamökosüsteemi summadesse, klastri kaupa.
        for unit_ix in (ec_ok, un_ok):
            sh = (ncl, nu)
            M_wd[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * dd)   # ▸ Σ w·d
            M_w[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww)         # ▸ Σ w
            M_wa[:, :, pi] += _scatter(sh, (c_ok, unit_ix), ww * ma)   # ▸ Σ w·mediaan_halvem
            M_cnt[:, :, pi] += _scatter(sh, (c_ok, unit_ix), np.ones_like(ww))  # ▸ stratumite arv
        # ▸ Stratumite erinevused jäetakse alles kirjeldavaks statistikaks (mediaan, Wilcoxon).
        for uix in np.unique(ec_ok):
            diffs.setdefault((int(uix), pi), []).append(dd[ec_ok == uix])
        for uix in np.unique(un_ok):
            diffs.setdefault((int(uix), pi), []).append(dd[un_ok == uix])
```

### P6. Kuidas saadakse lõplik näitaja

**Kaalutud keskmine ja bootstrap**: `src/oks/stats.py:612-616`

```python
# ▸ Bootstrap: kordus b võtab klastri c summad W[b, c] korda; Δ_b = Σ W·(Σw·d) / Σ W·(Σw).
m_boot = _ratio(np.tensordot(W, M_wd, axes=(1, 0)), np.tensordot(W, M_w, axes=(1, 0)))
# ▸ HINNANG: Δ = Σ w·d / Σ w üle kõigi ühiku stratumite.
m_obs = _ratio(M_wd.sum(0), M_w.sum(0))
# ▸ Halvema seisundi stratumimediaanide kaalutud keskmine (suhtelise muutuse nimetaja).
ma_obs = _ratio(M_wa.sum(0), M_w.sum(0))
# ▸ Stratumite ja klastrite arv (piisavuse kontroll).
m_cnt = M_cnt.sum(0)
m_ncl = (M_cnt > 0).sum(0)
```

**Abifunktsioonid (klaster, kaalud, suhe, usaldusvahemik ja p)**: `src/oks/stats.py:44, 51-57, 127-133, 145-177`

```python
# ▸ Baaskaardi ulatus km-des (EPSG:3301); klastrid loetakse nurgast (369 km, 6377 km).
E_MIN, E_MAX, N_MIN, N_MAX = 369, 740, 6377, 6635

# ▸ Parameetrid (vaikimisi): 10 km klaster, 4000 kordust, 1 ha, ≥ 20 stratumit, ≥ 5 klastrit, seeme, α.
cluster_blocks: int = 10
n_boot: int = 4000
min_area_ha: float = 1.0
min_strata: int = 20
min_clusters: int = 5
seed: int = 20261019
alpha: float = 0.05

def cluster_index(e_km, n_km, cs):
    """Klastri indeks (``cs`` x ``cs`` km ruudud) ja klastrite koguarv."""
    ncn = -(-(N_MAX - N_MIN) // cs)
    nce = -(-(E_MAX - E_MIN) // cs)
    ce = np.clip((e_km - E_MIN) // cs, 0, nce - 1)
    cn = np.clip((n_km - N_MIN) // cs, 0, ncn - 1)
    return ce * ncn + cn, nce * ncn

def _boot_weights(n_clusters: int, n_boot: int, seed: int) -> NDArray[np.float64]:
    """Multinoomsed klastrite kaalud (``n_boot`` x ``n_clusters``); sama kõigi kihtide jaoks."""
    # ▸ Iga kordus: 988 klastrit tagasipanekuga (kaal = mitu korda klaster valiti); sama seeme kõigile kihtidele.
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_clusters, np.full(n_clusters, 1.0 / n_clusters), size=n_boot).astype(np.float64)

def _boot_summary(obs, boot):
    """95 % persentiilvahemik ja kahepoolne bootstrap-p (``NaN`` kui kehtivaid kordusi < 90 %)."""
    n_boot = boot.shape[0]
    valid = np.isfinite(boot)
    frac = valid.mean(axis=0)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # kõik-NaN veerud on lubatud (-> NaN)
        # ▸ 95 % usaldusvahemik = bootstrapi 2,5. ja 97,5. protsentiil.
        lo = np.nanpercentile(boot, 2.5, axis=0)
        hi = np.nanpercentile(boot, 97.5, axis=0)
        # ▸ p = 2 · väiksem osa kordustest, mis on ≤ 0 või ≥ 0.
        le = np.nansum(boot <= 0, axis=0)
        ge = np.nansum(boot >= 0, axis=0)
        nv = valid.sum(axis=0)
        p = 2 * np.minimum(le, ge) / np.maximum(nv, 1)
        # pehme alampiir 1/(B+1): p ei ole null
        p = np.maximum(p, 1.0 / (n_boot + 1))
    # ▸ Kui alla 90 % kordustest annab tulemuse, CI ja p jäetakse tühjaks.
    bad = frac < 0.9
    p = np.where(bad | ~np.isfinite(obs), np.nan, np.minimum(p, 1.0))
    lo = np.where(bad, np.nan, lo)
    hi = np.where(bad, np.nan, hi)
    return lo, hi, p

def _ratio(num, den):
    # ▸ Jagatis; kui nimetaja on 0, tulemus puudub (NaN).
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)
```

**Tulemusrida ühiku ja paari kohta**: `src/oks/stats.py:641-698` (ainult paaritatud veerud; paaritamata vt mediaani osa)

```python
for ui in range(nu):
    level = "okosusteem" if ui < ne else "alam"
    code = u.eco_codes[ui] if ui < ne else u.alam_codes[ui - ne]
    for pi, (a, b) in enumerate(PAIRS):
        # ▸ Rida tehakse ainult siis, kui ühikul on pikslid mõlemas seisundis.
        if (ui, a) not in cells or (ui, b) not in cells:
            continue
        # … (välja jäetud: paaritamata hinnang, vt mediaani osa M7)
        # ▸ Paaritatud Δ usaldusvahemik ja p bootstrapist.
        lo_m, hi_m, p_m = _boot_summary(np.array([m_obs[ui, pi]]), m_boot[:, ui, pi][:, None])
        # … (välja jäetud: Mann-Whitney plokimediaanidel, kirjeldav)
        dlist = diffs.get((ui, pi))
        wil_p = med_d = share_pos = np.nan
        if dlist:
            dv = np.concatenate(dlist)
            # ▸ Kirjeldav: stratumierinevuste mediaan ja positiivsete osa; Wilcoxon (kooskõla kontroll).
            med_d, share_pos = float(np.median(dv)), float((dv > 0).mean())
            if dv.size >= 10 and np.any(dv != 0):
                wil_p = float(sps.wilcoxon(dv, method="approx").pvalue)
        # ▸ Piisavus: vähemalt 20 stratumit ja 5 klastrit.
        enough = bool(m_cnt[ui, pi] >= p.min_strata and m_ncl[ui, pi] >= p.min_clusters)
        # …
        ma0 = ma_obs[ui, pi]
        pair_rows.append(
            {
                "unit_level": level,
                "unit_code": int(code),
                "pair": PAIR_NAMES[pi],
                # …
                # ▸ PAARITATUD HINNANG (v2): stratumimediaanide vahede kaalutud keskmine.
                "delta_m_med": m_obs[ui, pi],
                # ▸ Suhteline muutus: Δ / |halvema seisundi stratumimediaanide kaalutud keskmine|.
                "rel_m_med": m_obs[ui, pi] / abs(ma0)
                if np.isfinite(ma0) and abs(ma0) > 1e-12
                else np.nan,
                "ci_m_med_lo": lo_m[0],
                "ci_m_med_hi": hi_m[0],
                # ▸ p ainult siis, kui andmeid on piisavalt.
                "p_m_med": p_m[0] if enough else np.nan,
                "median_d_m_med": med_d,
                "share_pos_m_med": share_pos,
                "wilcoxon_p_med": wil_p,
            }
        )
```

**Kõigi kihtide koondamine, FDR ja olulisus**: `src/oks/analysis.py:358-359, 383-391, 462-463, 471-516`

```python
# ▸ Ühed ja samad bootstrapi kaalud kõigile kihtidele.
n_cl = stats.cluster_index(np.array([stats.E_MIN]), np.array([stats.N_MIN]), params.cluster_blocks)[1]
W = stats._boot_weights(n_cl, params.n_boot, params.seed)
# … (iga kihi kohta)
        tbl = pl.read_parquet(path)
        # ▸ Arvutuse lahutusvõime: ≤ 10 m kihid oma lahutusvõimel, muud (930 m, 1 km, vektorid) 10 m.
        res_m = res_effective(r["spatial_resolution"])
        # ▸ Keskmisepõhised veerud (sh enough_m, enough_u, n_strata).
        out = stats.analyse_layer(tbl, u, res_m, params, W)
        vdir, bpath = pipeline.val_path(r["id"]), pipeline.blkmed_path(r["id"])
        if vdir.is_dir() and bpath.exists() and not tbl.is_empty():
            # ▸ Mediaanipõhised veerud (v2), samade kaaludega W.
            med = stats.analyse_layer_median(
                pl.read_parquet(bpath), vdir, u, used, res_m, params, W, unpaired_median_boot
            )
            # ▸ Liidetakse samale reale võtmega (unit_level, unit_code, pair).
            out = _join_median(out, med)
# …
    if not res["paarid"].is_empty():
        # ▸ FDR ja olulisus kõigi kihtide peale korraga.
        res["paarid"] = add_fdr(res["paarid"], params.alpha)
```

```python
#: FDR-perekonnad: (p-väärtus, q-väärtus); ``_med`` = mediaanipõhine (metoodika v2).
_FDR = (
    ("p_m", "q_m"),
    ("p_u", "q_u"),
    ("wilcoxon_p", "q_wilcoxon"),
    ("p_m_med", "q_m_med"),
    ("p_u_med", "q_u_med"),
    ("wilcoxon_p_med", "q_wilcoxon_med"),
)

def add_fdr(paarid: pl.DataFrame, alpha: float) -> pl.DataFrame:
    # … (välja jäetud: puuduvate veergude lisamine)
    fam = [(pc, qc) for pc, qc in _FDR if pc in paarid.columns]
    # ▸ FDR-perekond = tase (ökosüsteem / alamökosüsteem); kõik kihid ja paarid koos.
    for level in ("okosusteem", "alam"):
        d = paarid.filter(pl.col("unit_level") == level)
        if d.is_empty():
            continue
        parts.append(
            d.with_columns(pl.Series(qc, stats.bh_fdr(d[pc].to_numpy().astype(np.float64))) for pc, qc in fam)
        )
    out = pl.concat(parts, how="diagonal_relaxed")
    # … (välja jäetud: keskmisepõhised lipud oluline_m, oluline_u, kooskolas)
    if "q_m_med" in out.columns:
        out = out.with_columns(
            # ▸ Oluline = q < 0,05 (puuduv q → ei ole oluline).
            (pl.col("q_m_med") < alpha).fill_null(False).alias("oluline_m_med"),
            (pl.col("q_u_med") < alpha).fill_null(False).alias("oluline_u_med"),
        ).with_columns(
            (
                # ▸ „Oluline mõlemal hinnangul“: paaritatud ja paaritamata olulised ja sama märgiga.
                pl.col("oluline_m_med")
                & pl.col("oluline_u_med")
                & (pl.col("delta_m_med").sign() == pl.col("delta_u_med").sign())
            ).alias("kooskolas_med")
        )
    return out
```

```python
def bh_fdr(p: NDArray[np.float64]) -> NDArray[np.float64]:
    """Benjamini-Hochbergi FDR-korrigeeritud p-väärtused (``NaN`` jäävad ``NaN``-iks)."""
    q = np.full_like(p, np.nan, dtype=np.float64)
    ok = np.isfinite(p)
    pv = p[ok]
    m = pv.size
    if m == 0:
        return q
    # ▸ q_(i) = min_{j ≥ i} p_(j)·m/j, ülemine piir 1.
    order = np.argsort(pv, kind="stable")
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q
```

**Võrdluseks: keskmisepõhine paaritatud variant (`delta_m`), veebi hinnangus ei kasutata**: `src/oks/stats.py:264-268, 285-310, 322-325`

```python
# ▸ Sisend on plokitabeli summad (n, Σx) ploki × alamökosüsteemi × seisundi kaupa.
blk = (
    d.filter(pl.col("alam") >= 0)
    .group_by(["e_km", "n_km", "alam", "state"])
    .agg(pl.col("n").sum(), pl.col("sum").sum(), pl.col("cluster").first(), pl.col("eco").first())
)
# …
wide = blk.pivot(
    on="state", index=["e_km", "n_km", "alam", "cluster", "eco"], values=["n", "sum"]
).fill_null(0)
# …
for pi, (a, b) in enumerate(PAIRS):
    ok = (nsa[:, a] >= n_min) & (nsa[:, b] >= n_min)
    # …
    # ▸ ERINEVUS: stratumi KESKMISED (Σx / n), mitte mediaanid.
    ma = ssa[ok, a] / nsa[ok, a]
    mb = ssa[ok, b] / nsa[ok, b]
    dd = mb - ma
    # ▸ Kaal, koondamine ja bootstrap on samad mis mediaanipõhisel variandil.
    ww = nsa[ok, a] * nsa[ok, b] / (nsa[ok, a] + nsa[ok, b])
    # …
m_boot = _ratio(Wdb, Wwb)  # (B, nu, 3)
m_obs = _ratio(M_wd.sum(0), M_w.sum(0))
```

Sellest funktsioonist võtavad ka mediaanipõhised väljundid kolm veergu:

* `enough_m`, stratumite ja klastrite piisavus;
* `enough_u`;
* `n_strata`, stratumite arv, mida veebis näidatakse kujul „N paari“.

Koodi järgi on need samad mis mediaanipõhises funktsioonis, sest pikslite valim, rühmitus ja `n_min` on samad. Kontroll on kirjas peatükis „Vastavuse kontroll“.

### P7. Kuidas tulemus jõuab väljundisse

**Liitmine ja JSON-i ümardamine**: `src/oks/analysis.py:297-303`, `src/oks/export.py:16-32, 160-177, 249, 263-269`

```python
def _join_median(out, med):
    # ▸ Mediaanipõhised veerud liidetakse keskmisepõhise tabeli ridadele (vasak liitmine).
    keys = {"paarid": ["unit_level", "unit_code", "pair"], "lahtrid": ["unit_level", "unit_code", "state"]}
    res = dict(out)
    for k, on in keys.items():
        if not out[k].is_empty() and not med[k].is_empty():
            res[k] = out[k].join(med[k], on=on, how="left")
    # …
```

```python
#: Ümardus (olulisi numbreid) JSON-is; täpsed väärtused on CSV-s.
SIG = 5

def _r(x: object) -> object:
    """Ümarda ujukomaarv ``SIG`` olulise numbrini; ``NaN``/``inf`` -> ``None``."""
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        # ▸ Puuduv väärtus (NaN) → null.
        if not math.isfinite(x):
            return None
        if x == 0:
            return 0
        # ▸ 5 olulist numbrit, nt 38.90397581 → 38.904.
        return round(x, SIG - 1 - int(math.floor(math.log10(abs(x)))))
    return x

# … veergude nimekiri cols_p (väljavõte):
        # metoodika v2: mediaanipõhised hinnangud (veebilehe põhihinnang)
        "median_a", "median_b", "delta_u_med", "rel_u_med", "ci_u_med_lo", "ci_u_med_hi", "p_u_med", "q_u_med",
        "oluline_u_med", "delta_m_med", "rel_m_med", "ci_m_med_lo", "ci_m_med_hi", "p_m_med", "q_m_med",
        "oluline_m_med", "kooskolas_med",
# ▸ Veebi andmefail (ümardatud).
(out / "paarid.json").write_text(json.dumps(_rows(pr, cols_p), separators=(",", ":")), encoding="utf-8")
# ▸ Allalaaditav CSV täpsete väärtustega (sisaldab ka keskmisepõhiseid veerge delta_m jt).
csv.write_csv(out / "tulemused_paarid.csv")
```

**Veeb: hinnangu valik, filtrid, kuvamine**: `site_src/app.js:17-30, 111-127, 305-313, 337-345, 910-924`

```javascript
/** Hinnang (metoodika v2: mediaanide põhjal); k = 'm' paaritatud, 'u' paaritamata. */
const has = (v) => v !== null && v !== undefined && Number.isFinite(v);
function estOf(r, k) {
  if (!r) return null;
  // ▸ 'm' = paaritatud: ainult *_med veerud; „ok“ nõuab piisavust (enough_m) ja olemasolevat Δ-d.
  return k === 'm'
    ? { d: r.delta_m_med, rel: r.rel_m_med, lo: r.ci_m_med_lo, hi: r.ci_m_med_hi, p: r.p_m_med, q: r.q_m_med, sig: !!r.oluline_m_med, ok: !!r.enough_m && has(r.delta_m_med) }
    : { d: r.delta_u_med, rel: r.rel_u_med, lo: r.ci_u_med_lo, hi: r.ci_u_med_hi, p: r.p_u_med, q: r.q_u_med, sig: !!r.oluline_u_med, ok: !!r.enough_u && has(r.delta_u_med) };
}
// ▸ Vaikimisi on valitud paaritatud hinnang (S.est = 'm').
const est = (r) => estOf(r, S.est);
function passes(r) {
  const e = est(r);
  if (!e || !e.ok) return false;
  // ▸ Filter „oluline“ / „oluline mõlemal hinnangul“ / „Min |muutus|“.
  if (S.sig === 'sig' && !e.sig) return false;
  if (S.sig === 'both' && !r.kooskolas_med) return false;
  if (S.minRel > 0 && !(e.rel !== null && Math.abs(e.rel) >= S.minRel / 100)) return false;
  return true;
}
```

```javascript
// ▸ Numbrite kuvamine (eesti vormingus): ≥1000 → 0 komakohta, ≥10 → 1, ≥1 → 2, ≥0,01 → 3, väiksem → 2 olulist numbrit.
function fmt(x, sig) {
  if (x === null || x === undefined || !Number.isFinite(x)) return '–';
  const a = Math.abs(x);
  if (a === 0) return '0';
  if (a >= 1000) return nf(0).format(x);
  if (a >= 100) return nf(1).format(x);
  if (a >= 10) return nf(sig ? 1 : 1).format(x);
  if (a >= 1) return nf(2).format(x);
  if (a >= 0.01) return nf(3).format(x);
  return x.toLocaleString('et-EE', { maximumSignificantDigits: 2, maximumFractionDigits: 8 });
}
// ▸ Suhteline muutus protsentides märgiga.
const pct = (r, d = 0) => (r === null || r === undefined || !Number.isFinite(r) ? '–' : `${r > 0 ? '+' : ''}${nf(d).format(r * 100)} %`);
```

```javascript
// ▸ Kuumkaardi lahter: värv suhtelise muutuse järgi; kui rel puudub (nimetaja 0), näidatakse ainult suunda „Δ“.
const e = est(c);
const ok = c && e.ok && passes(c);
if (ok) {
  const hasRel = has(e.rel), cr = hasRel ? e.rel : Math.sign(e.d) * 0.5;
  const d = divColor(cr, e.sig); fill = d.fill; op = d.op;
  txt = S.hval === 'abs' ? sgn(e.d) : hasRel ? pct(e.rel) : 'Δ';
  // …
}
// ▸ Kohtspikker: Δ, CI, p, q, ühiku mediaanid ja keskmised, stratumite (paaride) ja klastrite arv.
tl(t, 'v', `${pct(e.rel, 1)}  (${sgn(e.d)} ${T.uhik || ''})`);
tl(t, 'm', `95 % CI: ${sgn(e.lo)} … ${sgn(e.hi)}`);
tl(t, 'm', `${S.est === 'm' ? 'paaritatud' : 'paaritamata'} · p ${pfmt(e.p)} · q ${pfmt(e.q)} · ${e.sig ? 'oluline' : 'ei ole oluline'}`);
tl(t, 'm', `mediaan ${fmt(c.median_a)} → ${fmt(c.median_b)} · keskmine ${fmt(c.mean_a)} → ${fmt(c.mean_b)}`);
if (S.est === 'm') tl(t, 'm', `${nf(0).format(c.n_strata)} paari (plokk × alamökosüsteem), ${c.n_clusters_m} klastrit`);
```

**Kvalitatiivne tõendusbaas ja stsenaariumi kontrollveerg (`tendus.json`, Excel)**: `src/oks/kaasnev_export.py:232-266`

```python
for r in paarid.iter_rows(named=True):
    # … (ainult indikaatorite kihid)
    # metoodika v2: hinnang mediaanide põhjal (paaritatud; kui stratumeid ei piisa, paaritamata)
    d, rel = r.get("delta_m_med"), r.get("rel_m_med")
    if not r.get("enough_m") or d is None:
        # ▸ Paaritatud ei ole piisav → kasutatakse paaritamata mediaanide vahet.
        d, rel, est = r.get("delta_u_med"), r.get("rel_u_med"), "paaritamata"
        sig = bool(r.get("oluline_u_med")) if r.get("enough_u") else False
        ok = bool(r.get("enough_u")) and d is not None
    else:
        est = "paaritatud"
        sig = bool(r.get("oluline_m_med"))
        ok = True
    direction = "ebaselge"
    # ▸ Hüve suund: Δ märk korda indikaatori suund (kas suurem väärtus on parem).
    if ok and sig and d is not None and d != 0:
        direction = "positiivne" if d * sign[lid] > 0 else "negatiivne"
    # … rea väljad: "delta": _r(d), "rel": _r(rel, 4), "oluline": sig and ok, "q": …,
    # ▸ Tugevus |rel| järgi: < 10 % nõrk, < 50 % keskmine, muidu tugev.
    #   "tugevus": indikaatorid.strength(rel) if ok and sig else "",
    #   "paare": int(r["n_strata"]) if est == "paaritatud" and r.get("n_strata") else None,
```

**Näide tegelikust tulemusest** (illustratiivne; kiht `c_tonn_per_ha_final_2022_10m`, ökosüsteem Metsad, vilets → hea; väärtused failist `data/tulemused/paarid.parquet` seisuga `b799458`, ühiku sisulist kontrolli selles töös ei tehtud):

| Väli | `paarid.parquet` | `paarid.json` (5 olul. numbrit) | Veebis |
|---|---|---|---|
| `delta_m_med` | 38.90397581008217 | 38.904 | „+38,9“ |
| `rel_m_med` | 0.042599… | 0.042599 | „+4,3 %“ (detail), „+4 %“ (kuumkaart) |
| `ci_m_med_lo … hi` | 31.1851… … 47.0331… | 31.185 … 47.033 | „+31,2 … +47,0“ |
| `p_m_med` | 0.00024993751562109475 (= 1/4001, alampiir) | – | „< 0,001“ |
| `q_m_med` / `oluline_m_med` | 0.00063049 / True | 0.00063049 / true | „oluline“ |
| `n_strata` | 16406 | 16406 | „16 406 paari“ |
| `delta_m` (keskmisepõhine) | 39.608 | olemas, kuid kuvamata | – |
| `median_a → median_b` (ühiku mediaanid) | 688 → 934 | 688 → 934 | kohtspikris |

## Lihtne selgitus

Ökosüsteemi seisundi mõju hindamisel on oht võrrelda erinevaid kohti. Kui hea seisundiga mets asub teistsugusel mullal kui vilets mets, on erinevus osaliselt koha erinevus. Paaritatud hinnang väldib seda nii:

1. **Paarid samast kohast.** Eesti jagatakse 1 km ruutudeks. Iga ruudu sees võetakse eraldi iga ökosüsteemitüüp (nt palumets). Kui sama ruudu ja tüübi sees on nii viletsas kui heas seisundis ala, vähemalt 1 ha kummaski, moodustub üks võrdluspaar.
2. **Võrdlus paari sees.** Paari sees leitakse kummagi seisundi **mediaan**: väärtus, millest pooled pikslid on väiksemad ja pooled suuremad. Paari erinevus on hea seisundi mediaan miinus vileda seisundi mediaan.
3. **Paaride koondamine.** Kõigi paaride erinevustest arvutatakse **kaalutud keskmine**. Suurema pindalaga ja tasakaalukamad paarid (mõlemat seisundit palju) saavad suurema kaalu. See ongi tulemus Δ.
4. **Kindluse hindamine.** Arvutust korratakse 4000 korda, valides iga kord juhuslikult 10 × 10 km alasid (osa mitu korda, osa mitte kordagi). Nii saadakse usaldusvahemik ja p-väärtus, mis arvestavad, et lähestikused kohad on sarnased.
5. **Olulisuse parandus.** Kuna hinnanguid on tuhandeid, korrigeeritakse p-väärtusi (FDR). „Oluline“ tähendab q < 0,05. Lisaks peab olema vähemalt 20 paari ja 5 erinevat 10 km ala.

Veebileht näitab seda mediaanipõhist hinnangut. Keskmiste põhjal tehtud sama hinnang on andmetes alles, kuid veebis seda ei kasutata.

---

# MEDIAANI ARVUTUS

## Ülevaade

v2-s on kõik veebis kuvatavad mediaanid **täpsed pikslimediaanid**. Iga piksel on üks vaatlus. Kui pikslite arv on paarisarv, võetakse kahe keskmise väärtuse keskmine. Tühja valimi korral on tulemus puudu (NaN). Mediaan arvutatakse **kadudeta sagedustabelist**, kus iga erinev väärtus on eraldi rida koos täpse pikslite arvuga. Väärtusi ei rühmitata vahemikesse.

Mediaani arvutatakse samal põhimõttel neljas kohas:

| Kus | Rühm | Funktsioon | Väljund |
|---|---|---|---|
| Tulemustabel (lähtekas) | tüüp × seisund; suur ökosüsteem × seisund (+ kokku-read) | `kaasnev.median_table` | `kaasnev_tuup_seisund.parquet`, `kaasnev_suured.parquet` → `kaasnev.json` |
| Statistiline analüüs | ühik (ökosüsteem/alam) × seisund; algne seisundiklass; detailne klass | `stats.analyse_layer_median` | `lahtrid.parquet`, `algklassid.parquet`, `klassid.parquet` |
| Paaritamata Δ | ühiku mediaanide vahe + täpne klastribootstrap | `stats.analyse_layer_median`, `median.cluster_boot_medians*` | `paarid.parquet` (`delta_u_med`) |
| Plokitase | 1 km plokk × ühik × seisund | `aggregate.segment_medians` | paaritatud hinnang (P3) ja kastdiagrammide kvantiilid |

Lisaks on kõigil neil „ainult nullist erinevate pikslite“ mediaan, veerg `median_nz`. Märkus: veebi vaates „Kihtide ülevaade“ on ka **ligikaudne** histogrammipõhine mediaan („mediaan ≈“). See ei ole täpne mediaan ja on kirjeldatud peatükis „Vajab täiendavat kontrolli“, punkt 5.

## Andmete liikumine

**M1. Kust andmed tulevad.**

* Sama rastri lugemine ja NoData reegel mis P1–P2.
* Iga 1 km ploki-rea kohta kirjutatakse sagedustabel `(e_km, n_km, kood, value, n)` kõigi kehtivate pikslite kohta, mille all on baaskaardi klass. Klassi seisund siin rolli ei mängi: kaasa lähevad ka seisundita, ranniku ning asustuse ja muu klassid.
* Väärtuse tüüp on float32, kui see esitab kõik väärtused täpselt, muidu float64.

**M2. Millised andmed kaasatakse mediaani arvutusse.**

* Kaasatakse kõik rühma klasside kehtivad pikslid.
* Nullid on kaasa arvatud, sh NoData, mis on loetud nulliks.
* Erandkihtides jääb NoData välja.
* Nullist erinevate pikslite mediaanis jäetakse täpsed nullid välja.

**M3. Millised filtreeringud rakenduvad.**

* **Rühm** on klasside hulk. Ühiku ja seisundi rühm koosneb ühiku seisundiga klassidest, kus `cls_state` = s.
* **Tüüp × seisund** tähendab `(ökosüsteem, alam_kood, tüüp, uld)`.
* **Suured ökosüsteemid** on ökosüsteemid 1–5:
  * mets jaotatakse lisaks kuivadeks ja märgadeks metsadeks;
  * kokku-read on „hea + keskmine + vilets“ ja „kõik seisundid“;
  * „Asustus ja muu“ ei liideta.
* **Tulemustabelis peidetakse mediaan** staatuse järgi, mis arvutatakse klassitabeli loendustest:
  * „ei paku“, kui nullist erinevaid piksleid on alla 1 % kehtivatest;
  * „–“, kui kehtivaid piksleid on alla 5 % klassist.

**M4. Kuidas andmed järjestatakse.**

* Iga baaskaardi koodi väärtused summeeritakse üle kõigi plokkide ja sorteeritakse kasvavalt. Igale väärtusele lisatakse kumulatiivne pikslite arv.
* Ujukomaarvud teisendatakse täisarvvõtmeteks, mille järjestus on sama mis arvude järjestus. Selle abil saab teha poolitusotsingut.
* Plokimediaanides sorteeritakse pikslid otse.

**M5. Kuidas mediaan leitakse.**

* k-s järjestatud väärtus klasside ühendis on vähim andmetes esinev `t`, mille korral `Σ_klass #{x ≤ t} ≥ k + 1`.
* See leitakse poolitusotsinguga. Pikslimassiivi kokku ei panda.
* Tulemus on alati üks andmetes esinev väärtus või, paarisarvu korral, kahe sellise väärtuse keskmine.

**M6. Paaris- ja paaritu arv vaatlusi.**

* n vaatluse korral on `a` = (n−1)//2-s ja `b` = n//2-s väärtus (0-põhine indeks).
* Paaritu n korral `a = b`. Paarisarvu korral on mediaan `(a + b) / 2`.
* Sama reegel kehtib plokimediaanides ja igas bootstrapi korduses.
* `n = 0` korral on tulemus NaN.

**M7. Kuidas tulemus jõuab väljundisse.**

1. Mediaan kirjutatakse parquet-faili täpse väärtusena.
2. JSON-is ümardatakse see 5 olulise numbrini.
3. Veebis kuvatakse see vormindusega `fmt`, mis annab 0–3 komakohta sõltuvalt suurusest.

Kus mediaan veebis näha on:

* **Tulemustabel**: lahtri väärtus on mediaan, kohtspikris on keskmine ja `median_nz`.
* **Teenuse detail**:
  * „Teenuse tase seisundi kaupa“: punkt on täpne mediaan, kast näitab plokimediaanide kvantiile;
  * jaotusgraafiku kolmnurk;
  * „Algsel seisundiskaalal“.
* **Profiil.**
* **Stsenaarium**: kuvatakse „Mediaanide vahe hektari kohta“. Pindalaga korrutamiseks kasutatakse keskmiste vahet (otsuse järgi).
* **Paaritamata Δ** on `delta_u_med = median_b − median_a`.

## Kommenteeritud kood

### M1. Kust andmed tulevad: kadudeta sagedustabel

**Kirjutamine iga ploki-rea kohta**: `src/oks/aggregate.py:321-327`

```python
if val_dir is not None or groupings:
    # ▸ Kaasame kehtivad pikslid, mille all on MÕNI baaskaardi klass (ka seisundita klassid).
    base_ok = ok & ((lut_all if lut_all is not None else lut)[codes] >= 0)
    e_all = col_vals[np.broadcast_to(col_inv, val.shape)]
    if val_dir is not None and base_ok.any():
        # ▸ Üks fail ploki-rea kohta: n{n_km}.parquet, read (e_km, kood, value, n).
        value_counts(e_all[base_ok], codes[base_ok].astype(np.int64), val[base_ok]).with_columns(
            pl.lit(brow, dtype=pl.Int16).alias("n_km")
        ).write_parquet(val_dir / f"n{brow}.parquet", compression="zstd", row_group_size=65_536)
```

**Sagedustabel**: `src/oks/aggregate.py:195-218`

```python
def _value_dtype(dtype):
    """Sagedustabeli väärtuse tüüp: float32, kui see esitab kõik väärtused täpselt, muidu float64."""
    exact32 = dtype == np.float32 or (dtype.kind in "iu" and dtype.itemsize <= 2)
    return np.float32 if exact32 else np.float64

def value_counts(e_km, kood, x):
    """Kadudeta sagedustabel ``(e_km, kood, väärtus) -> n``: iga erinev väärtus on oma rida (mitte vahemik)."""
    # ▸ Järjestame: kood, väärtus, plokk.
    o = np.lexsort((e_km, x, kood))
    e, k, v = e_km[o], kood[o], x[o]
    # ▸ Uus rida algab, kui muutub kood, väärtus või plokk.
    change = (k[1:] != k[:-1]) | (v[1:] != v[:-1]) | (e[1:] != e[:-1])
    st = np.flatnonzero(np.concatenate(([True], change))) if v.size else np.empty(0, dtype=np.int64)
    # ▸ n = mitu pikslit on täpselt selle väärtusega (täpne loendus, mitte vahemik).
    n = np.diff(np.append(st, v.size))
    return pl.DataFrame(
        {
            "e_km": e[st].astype(np.int16),
            "kood": k[st].astype(np.int32),
            "value": v[st].astype(_value_dtype(x.dtype)),
            "n": n.astype(np.int32),
        }
    )
```

### M2–M4. Kaasamine ja järjestamine: `ValueTable`

`src/oks/median.py:36-108`

```python
def _to_key(x: float, dtype) -> int:
    """Ujukomaarv -> märgita täisarv, mille järjestus on sama mis arvu järjestus."""
    # ▸ Tehniline abivõte: võimaldab poolitusotsingut üle kõigi võimalike ujukomaväärtuste.
    ut, bits = _key_fns(dtype)
    u = int(np.array(x, dtype=dtype).view(ut))
    sign = 1 << (bits - 1)
    return (~u & ((1 << bits) - 1)) if u & sign else u | sign

class ValueTable:
    """Iga baaskaardi koodi sorteeritud erinevad väärtused ja kumulatiivsed pikslite arvud (kõik plokid kokku)."""

    @classmethod
    def load(cls, val_dir: Path) -> ValueTable:
        lf = scan(val_dir)
        koods = lf.select(pl.col("kood").unique()).collect()["kood"].to_list()
        data = {}
        for k in sorted(koods):
            d = (
                # ▸ Ühe koodi read kõigist plokkidest; sama väärtusega pikslid liidetakse.
                lf.filter(pl.col("kood") == k)
                .group_by("value")
                .agg(pl.col("n").sum())
                # ▸ Järjestame väärtused kasvavalt.
                .sort("value")
                .collect()
            )
            # ▸ Kumulatiivne arv: mitu pikslit on väärtusega ≤ see väärtus.
            data[int(k)] = (d["value"].to_numpy(), np.cumsum(d["n"].to_numpy().astype(np.int64)))
        return cls(data)

    def _arrays(self, koods):
        # ▸ Rühma klassid (koodid), millel on andmeid.
        return [self.data[k] for k in koods if k in self.data and self.data[k][1].size]

    def _zeros(self, arrs) -> int:
        # ▸ Täpsete nullide arv rühmas (nullist erinevate mediaani jaoks).
        z = 0
        for v, c in arrs:
            i = int(np.searchsorted(v, 0, side="left"))
            if i < v.size and v[i] == 0:
                z += int(c[i] - (c[i - 1] if i else 0))
        return z

    def total(self, koods) -> float:
        """Väärtuste summa (keskmise jaoks)."""
        s = 0.0
        for v, c in self._arrays(koods):
            s += float(np.dot(v.astype(np.float64), np.diff(c, prepend=0)))
        return s
```

### M5–M6. Mediaani leidmine, paaris- ja paaritu arv

`src/oks/median.py:110-139`

```python
    def _kth(self, arrs, k: int, zeros: int) -> float:
        """k-s (0-põhine) järjestatud väärtus; ``zeros > 0`` jätab nullid välja."""
        # ▸ Otsinguvahemik: rühma vähim ja suurim väärtus.
        lo = _to_key(min(float(v[0]) for v, _ in arrs), self.dtype)
        hi = _to_key(max(float(v[-1]) for v, _ in arrs), self.dtype)
        while lo < hi:
            mid = (lo + hi) // 2
            t = _from_key(mid, self.dtype)
            # ▸ Loeme, mitu pikslit kõigis rühma klassides on ≤ t.
            f = 0
            for v, c in arrs:
                j = int(np.searchsorted(v, t, side="right"))
                if j:
                    f += int(c[j - 1])
            # ▸ Nullist erinevate mediaanis ei loe nullid (t ≥ 0 korral lahutame nende arvu).
            if zeros and t >= 0:
                f -= zeros
            # ▸ Kui ≤ t piksleid on vähemalt k+1, on k-s väärtus ≤ t → otsime vasakult, muidu paremalt.
            if f >= k + 1:
                hi = mid
            else:
                lo = mid + 1
        return float(_from_key(lo, self.dtype))

    def median(self, koods, nonzero: bool = False) -> tuple[int, float]:
        """Täpne mediaan klasside ühendis: ``(pikslite arv, mediaan)``; tühja valimi korral ``(0, nan)``."""
        arrs = self._arrays(koods)
        zeros = self._zeros(arrs) if nonzero else 0
        # ▸ n = pikslite arv rühmas (nullist erinevate mediaanis ilma nullideta).
        n = sum(int(c[-1]) for _, c in arrs) - zeros
        # ▸ Tühi rühm → mediaan puudub.
        if n == 0:
            return 0, float("nan")
        # ▸ Paaritu n: üks keskmine väärtus (a = b). Paarisarv: kaks keskmist väärtust a ja b.
        a = self._kth(arrs, (n - 1) // 2, zeros)
        b = a if n % 2 else self._kth(arrs, n // 2, zeros)
        # ▸ Mediaan = (a + b) / 2.
        return n, (a + b) / 2
```

(Plokimediaanid kasutavad sama reeglit otse sorteeritud massiivil, vt P3 `segment_medians`: `(v[st + (n − 1)//2] + v[st + n//2]) / 2`.)

### M3. Rühmad, millele mediaan arvutatakse

**Ühik × seisund, detailne klass, algne seisundiklass**: `src/oks/stats.py:506-554`

```python
def koods_of(ui: int, s: int) -> list[int]:
    # ▸ Ühiku (ökosüsteem või alamökosüsteem) ja seisundi s kõik detailsed koodid.
    m = (u.cls_eco[idx] == ui) if ui < ne else (u.cls_alam[idx] == ui - ne)
    return [int(k) for k in kood[m & (u.cls_state[idx] == s)]]

# ---------- ühiku ja seisundi täpsed mediaanid ----------
vt = median.ValueTable.load(val_dir)
cells = {}
koods = {}
for ui in range(nu):
    for s in range(3):
        ks = koods_of(ui, s)
        # ▸ Mediaan klasside ÜHENDIS (kõik pikslid korraga, mitte klasside mediaanidest).
        n, m = vt.median(ks)
        if n == 0:
            continue
        # ▸ Talletame: n, mediaan, n nullist erinevaid, mediaan nullist erinevatel.
        cells[(ui, s)] = (n, m, *vt.median(ks, nonzero=True))
        koods[(ui, s)] = ks

# ▸ Iga detailse klassi mediaan (klassid.parquet).
cls_rows = []
for i, k in zip(idx, kood, strict=True):
    _n, m = vt.median([int(k)])
    nnz, mnz = vt.median([int(k)], nonzero=True)
    cls_rows.append({"cls": int(i), "median": m, "n_nz": nnz, "median_nz": mnz})

# ▸ Algse seisundiklassi (A, B, C, D1 …) mediaan ühiku sees (algklassid.parquet).
for ui in range(nu):
    # …
    for letter in sorted(set(letters[in_u].tolist())):
        m_l = in_u & (letters == letter)
        ks = [int(k) for k in kood[m_l]]
        n, m = vt.median(ks)
        if n == 0:
            continue
        nnz, mnz = vt.median(ks, nonzero=True)
        # ▸ Lisaks keskmine = Σx / n samast sagedustabelist.
        alg_rows.append({ … , "n": n, "mean": vt.total(ks) / n, "median": m, "n_nz": nnz, "median_nz": mnz})
```

**Tulemustabel (lähtekas): tüüp × seisund ja suured ökosüsteemid**: `src/oks/kaasnev.py:201-233, 261-286`

```python
def _big_groups(classes):
    """Suurte ökosüsteemide klassirühmad: seisundi kaupa ja kaks „kokku“ rida (kuivad/märjad metsad eraldi)."""
    # ▸ Ökosüsteemid 1–5 (rohumaad, sood, metsad, põllumaad, rannikud); 6 „Asustus ja muu“ ei liideta.
    base = classes.filter(pl.col("okosusteem_kood").is_in([1, 2, 3, 4, 5]))
    forest = base.filter(pl.col("okosusteem_kood") == 3)
    # ▸ Mets lisaks kuivadeks (31) ja märgadeks (32) metsadeks alam_kood järgi.
    split = [ … for code, (name, codes) in FOREST_SPLIT.items() ]
    base = pl.concat([base, *split])
    out = [base]
    # ▸ Kokku-read: hea+keskmine+vilets ning kõik seisundid (1–5).
    for label, ulds in (
        ("kokku (hea+keskmine+vilets)", [1, 2, 3]),
        ("kokku (kõik seisundid)", [1, 2, 3, 4, 5]),
    ):
        out.append(base.filter(pl.col("uld").is_in(ulds)).with_columns(pl.lit(label).alias("seisund_nimi")))
    return out

def median_table(vt, group, keys):
    """Täpne pikslimediaan iga rühma klasside ühendis (kõik pikslid ja nullist erinevad; metoodika v2).

    Valim on sama mis ``summarise`` keskväärtusel: kõik kehtivad pikslid, nullid kaasa arvatud.
    """
    rows = []
    # ▸ Iga rühma (nt palumets × hea) kõik detailsed koodid.
    for r in group.group_by(keys).agg(pl.col("kood")).iter_rows(named=True):
        ks = [int(k) for k in r["kood"]]
        _n, m = vt.median(ks)
        _nnz, mnz = vt.median(ks, nonzero=True)
        rows.append({**{k: r[k] for k in keys}, "median": m, "median_nz": mnz})
    return pl.DataFrame(rows, schema_overrides={k: group.schema[k] for k in keys})

def add_medians(res, classes, layer_ids, blocks=None):
    # …
    for lid in layer_ids:
        vdir = base / f"{lid}__val"
        # … (välja jäetud: hoiatus, kui sagedustabel puudub)
        # ▸ Kihi sagedustabel loetakse üks kord; arvutame tüüp × seisund ja suurte ökosüsteemide mediaanid.
        vt = median.ValueTable.load(vdir)
        parts_t.append(median_table(vt, classes, ts_keys).with_columns(pl.lit(lid).alias("layer_id")))
        parts_b.append(median_table(vt, big_groups, big_keys).with_columns(pl.lit(lid).alias("layer_id")))
        del vt
    # ▸ Mediaan liidetakse keskmise, katvuse ja staatuse tabelile (summarise) samade võtmetega.
    for name, parts, keys in (("tuup_seisund", parts_t, ts_keys), ("suured", parts_b, big_keys)):
        if parts:
            out[name] = res[name].join(pl.concat(parts), on=[*keys, "layer_id"], how="left")
```

**Staatus (millal mediaani ei näidata)**: `src/oks/kaasnev.py:133-150`, `src/oks/catalog.py:146`

```python
g = g.with_columns(
    # ▸ kate = kehtivate pikslite osa klassi pikslitest; esineb_osa = nullist erinevate osa kehtivatest.
    (pl.col("n_valid") / pl.col("n_total")).alias("kate"),
    pl.when(pl.col("n_valid") > 0).then(pl.col("n_nonzero") / pl.col("n_valid")).alias("esineb_osa"),
    pl.when(pl.col("n_valid") > 0).then(pl.col("sum") / pl.col("n_valid")).alias("mean"),
)
# …
return g.with_columns(
    # ▸ „ei hinnatud“: kehtivaid alla 5 %; „ei paku“: nullist erinevaid alla 1 % (POSITIVE_MIN = 0.01);
    #   „osaline kate“: kehtivaid alla 90 %; muidu „ok“.
    pl.when((pl.col("n_valid") == 0) | (pl.col("kate") < COVER_MIN))
    .then(pl.lit(STATUS_MISSING))
    .when(pl.col("esineb_osa") < catalog.POSITIVE_MIN)
    .then(pl.lit(STATUS_NONE))
    .when(pl.col("kate") < COVER_FULL)
    .then(pl.lit(STATUS_PARTIAL))
    .otherwise(pl.lit(STATUS_OK))
    .alias("staatus")
)
```

**Plokimediaanide kvantiilid kastdiagrammi jaoks**: `src/oks/stats.py:563-571, 700-716`

```python
for (ui, s), f in bl.partition_by(["unit", "state"], as_dict=True).items():
    key = (int(ui), int(s))
    # ▸ Ainult plokid, kus ühiku seisundit on vähemalt 1 ha.
    big = f.filter(pl.col("n") >= n_min)
    bm[key] = big["median"].to_numpy()
    bm_nz[key] = big.filter(pl.col("n_nz") > 0)["median_nz"].to_numpy()
    # … (klastrite arv paaritamata piisavuse jaoks)

for (ui, s), (_n, m, nnz, mnz) in sorted(cells.items()):
    # …
    row = {"unit_level": level, "unit_code": int(code), "state": STATES[s],
           # ▸ Ühiku × seisundi TÄPNE pikslimediaan ja nullist erinevate mediaan.
           "median": m, "n_nz": nnz, "median_nz": mnz}
    for suf, xs in (("", bm.get((ui, s), empty)), ("_nz", bm_nz.get((ui, s), empty))):
        # ▸ Plokimediaanide 5., 25., 50., 75., 95. protsentiil (np.quantile vaikimisi lineaarne interpolatsioon).
        q = np.quantile(xs, QUANTS) if xs.size else np.full(len(QUANTS), np.nan)
        row[f"blocks_med{suf}"] = int(xs.size)
        row.update({f"mq{qn}{suf}": float(v) for qn, v in zip(QNAMES, q, strict=True)})
    cell_rows.append(row)
```

### M7a. Paaritamata Δ: ühiku mediaanide vahe ja täpne bootstrap

`src/oks/stats.py:618-652`, `src/oks/median.py:142-209, 252-297`

```python
# ---------- paaritamata: täpne klastribootstrap ----------
if unpaired_boot:
    # … (välja jäetud: failide rühmitamine klastriridade kaupa, mälu säästmiseks)
    for key, ks in koods.items():
        # (klaster, väärtus) kaupa koondatud loendus annab sama täpse mediaani kui pikslite read
        seg = median.segments(
            pl.scan_parquet(fs)
            .filter(pl.col("kood").is_in(ks))
            .group_by(cluster_expr(p.cluster_blocks).alias("cl"), "value")
            .agg(pl.col("n").cast(pl.Int64).sum())
            .collect()
            for fs in crow.values()
        )
        # ▸ 4000 täpset korduse-mediaani (samad kaalud W kui paaritatud hinnangul).
        boots[key] = median.cluster_boot_medians_seg(seg, W)
# …
        # ▸ Ühiku halvema ja parema seisundi täpne mediaan (vt M5).
        med_a, med_b = cells[(ui, a)][1], cells[(ui, b)][1]
        # ▸ PAARITAMATA HINNANG: mediaanide vahe.
        du = med_b - med_a
        lo_u = hi_u = p_u = np.full(1, np.nan)
        if (ui, a) in boots and (ui, b) in boots:
            # ▸ Iga korduse mediaanide vahe → CI ja p.
            lo_u, hi_u, p_u = _boot_summary(np.array([du]), (boots[(ui, b)] - boots[(ui, a)])[:, None])
        # … väljad: "median_a": med_a, "median_b": med_b, "delta_u_med": du,
        #   "rel_u_med": du / abs(med_a) if abs(med_a) > 1e-12 else np.nan,
        #   "p_u_med": p_u[0] if enough_u else np.nan  (enough_u: ≥ 20 plokki ja ≥ 5 klastrit kummaski seisundis)
```

```python
def cluster_boot_medians(cluster, value, count, W):
    """Täpsed bootstrap-mediaanid: kordus ``b`` võtab klastri ``c`` piksleid ``W[b, c]`` korda."""
    B = W.shape[0]
    if value.size == 0:
        return np.full(B, np.nan)
    vals, vidx = np.unique(value, return_inverse=True)
    # …
    Wc = W[:, cl_u]  # (B, klastrid)
    # ▸ Pikslite arv igas korduses.
    tot = Wc @ np.bincount(cl_i, weights=count, minlength=cl_u.size)
    # ▸ Paaris/paaritu reegel igas korduses: järgud floor((N−1)/2) ja floor(N/2).
    rank_lo = np.floor((tot - 1) / 2)
    rank_hi = np.floor(tot / 2)
    out = np.full(B, np.nan)
    ok = tot > 0
    if B * K <= _DENSE_MAX and cl_u.size * K <= _DENSE_MAX:
        cnt = np.zeros((cl_u.size, K))
        np.add.at(cnt, (cl_i, vidx), count)
        # ▸ Korduse kumulatiivne jaotus üle sorteeritud väärtuste.
        cum = np.cumsum(Wc @ cnt, axis=1)  # (B, K)
        i_lo = (cum < (rank_lo + 1)[:, None]).sum(1)
        i_hi = (cum < (rank_hi + 1)[:, None]).sum(1)
    else:
        # … (välja jäetud: sama tulemus poolitusotsinguga suurte valimite jaoks)
    i_lo, i_hi = np.minimum(i_lo, K - 1), np.minimum(i_hi, K - 1)
    # ▸ Korduse mediaan = kahe keskmise väärtuse keskmine (paaritu N korral sama väärtus kaks korda).
    out[ok] = (vals[i_lo[ok]].astype(np.float64) + vals[i_hi[ok]].astype(np.float64)) / 2
    return out
```

(`cluster_boot_medians_seg`, `median.py:252-297`, annab sama täpse tulemuse. Väikese valimi korral kasutab see sama funktsiooni. Suure valimi korral otsib see k-ndat väärtust poolitusega üle ujukomaarvude järjestuse, samamoodi nagu `ValueTable._kth`.)

### M7b. Väljund ja kuvamine

**Tulemustabeli lahter (JSON)**: `src/oks/kaasnev_export.py:84-104`

```python
def _cells(df, keys, layers):
    """Rakk = ``[mediaan, keskmine, kate, esineb_osa, staatuse indeks, mediaan nullist erinevatel pikslitel]``."""
    # …
    for r in sub.iter_rows(named=True):
        key = tuple(r[k] for k in keys)
        cell = [
            # ▸ Põhiväärtus: mediaan (5 olulist numbrit); keskmine stsenaariumi pindalaarvutuseks.
            _r(r.get("median")),
            _r(r["mean"]),
            _r(r["kate"], 4),
            _r(r["esineb_osa"], 4),
            STATUSES.index(r["staatus"]),
            _r(r.get("median_nz")),
        ]
        by_layer.setdefault(r["layer_id"], {})[key] = cell
```

**Veeb: tulemustabel, taseme graafik, profiil, stsenaarium**: `site_src/sections/common.js:17-23`, `site_src/app.js:442-446, 826-835`, `site_src/sections/scenario.js:89-93`

```javascript
/** Rakk (mediaan, keskmine, kate, esineb_osa, staatus, mediaan > 0) → { v (mediaan), mean, st, cls } kuvamiseks. */
function cellView(c) {
  if (!c) return { v: null, mean: null, st: null, txt: '', cls: 'na' };
  const [med, mean, , , st] = c;
  // ▸ „ei paku“ ja „ei hinnatud“ korral mediaani ei näidata.
  if (st === ST.NONE) return { v: null, mean, st, txt: 'ei paku', cls: 'none' };
  if (st === ST.MISS || med === null) return { v: null, mean, st, txt: '–', cls: 'miss' };
  // ▸ Muidu lahtris on mediaan vormindatud kujul; osalise katte korral kaldkiri.
  return { v: med, mean, st, txt: fmt(med), cls: st === ST.PART ? 'part' : 'ok' };
}
```

```javascript
/** Täpne pikslimediaan (tulemustabelist); ilma nullideta vaates nullist erinevate pikslite mediaan. */
function exactMed(d) {
  if (!d || !d.cell) return null;
  const v = d.noZero ? d.cell.median_nz : d.cell.median;
  return has(v) ? v : null;
}
// ▸ „Teenuse tase seisundi kaupa“: punkt = täpne mediaan, kast = plokimediaanide Q1–Q3, vurr = 5.–95. protsentiil.
const med = c[`median${z}`], occ = c.n ? (c.n_nz || 0) / c.n : null;
// …
h('rect', { x: cx - w / 2, y: y(c[`mq75${z}`]), width: w, height: Math.max(2, y(c[`mq25${z}`]) - y(c[`mq75${z}`])), rx: 3, fill: stateColor(st) }, g);
h('line', { x1: cx - w / 2, x2: cx + w / 2, y1: y(c[`mq50${z}`]), y2: y(c[`mq50${z}`]), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
h('circle', { cx, cy: y(med), r: 5, fill: cssVar('--ink'), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
h('text', { x: cx + w / 2 + 8, y: y(med) + 4, class: 'strong' }, svg, fmt(med));
```

```javascript
// ▸ Stsenaarium: mediaanide vahe /ha (brauseris, ümardatud mediaanidest); pindalaga korrutatakse KESKMISTE vahe.
const dm = b.v - a.v; h('td', { class: 'num strong' }, tr, signed(dm));
const d = a.mean !== null && b.mean !== null ? b.mean - a.mean : null;
h('td', { class: 'num' }, tr, d === null ? '–' : signed(d));
const tu = additiveUnit(L);
h('td', { class: 'num strong' }, tr, tu && d !== null ? `${d > 0 ? '+' : d < 0 ? '−' : ''}${fmt(Math.abs(d) * c.ha)} ${tu}` : '–');
```

## Lihtne selgitus

Mediaan on väärtus, mis jagab pikslid kaheks võrdseks pooleks: pooled on sellest väiksemad, pooled suuremad. Projekt arvutab mediaani **täpselt**:

1. **Loendus.** Iga teenusekihi kohta loendatakse, mitu pikslit on igal täpsel väärtusel igas baaskaardi klassis ja igas 1 km plokis. Vahemikesse rühmitamist ei tehta.
2. **Rühm.** Mediaani jaoks võetakse rühma kõik klassid koos, nt „palumets, hea seisund“ või „metsad, vilets“. Nende pikslid pannakse järjekorda väikseimast suurimani. Tegelikult loetakse ainult kumulatiivseid arve, sest pikslite massiivi kokku panna ei ole vaja.
3. **Keskmine piksel.** Kui piksleid on paaritu arv, on mediaan täpselt keskmise piksli väärtus. Kui paarisarv, siis kahe keskmise piksli väärtuste keskmine.
4. **Nullid.** Nullid (sh puuduvad andmed, mis on loetud nulliks) on mediaanis sees. Seetõttu on mediaan paljudes klassides 0. Selleks on eraldi näitaja „mediaan kohtades, kus teenus esineb“, kus nullid on välja jäetud.
5. **Peitmine.** Tulemustabelis ei näidata mediaani, kui teenust peaaegu pole (alla 1 % pikslitest nullist erinevad, „ei paku“) või kui kihi andmed katavad alla 5 % klassist („–“).
6. **Ümardus.** Arvutus kasutab täpseid väärtusi. Veebi andmefailis on 5 olulist numbrit, ekraanil 0–3 komakohta.

---

# VASTAVUSE KONTROLL

## Kontrollitud failid

| Fail | Mida kontrolliti |
|---|---|
| `src/oks/config.py` | ploki ja klastri suurus |
| `src/oks/catalog.py` | kihtide valik, NoData → 0, erandkihid, `POSITIVE_MIN` |
| `src/oks/baas.py` | klassitabel, seisundi tuletamine, `class_lut`, `class_lut_all` |
| `src/oks/pipeline.py` | töövoog, 10 m ümberproovimine, rühmitused, väljundfailid |
| `src/oks/aggregate.py` | lugemine, kehtivus, sagedustabel, plokimediaanid, plokisummad |
| `src/oks/median.py` | täpne mediaan, täpne bootstrap |
| `src/oks/stats.py` | ühikud, paaritatud (mediaan ja keskmine), paaritamata, bootstrap, CI, p, FDR |
| `src/oks/analysis.py` | käivitus, liitmine, FDR, olulisus, tundlikkus |
| `src/oks/kaasnev.py` | tulemustabel: keskmine, staatus, mediaan, suured ökosüsteemid |
| `src/oks/export.py`, `kaasnev_export.py`, `andmetabel.py`, `sitebuild.py`, `report.py`, `vordlus.py` | väljundid, ümardus, kasutatavad veerud |
| `site_src/app.js`, `site_src/sections/*.js` | hinnangu valik, filtrid, kuvamine, vormindus |
| `tests/test_median.py`, `test_stats.py`, `test_aggregate.py`, `test_kaasnev.py` | olemasolevad testid |
| `docs/metoodika_v2_otsused.md`, `docs/metoodika_v2_lopparuanne.md` | kokkulepitud metoodika |

## Kasutusel olevad funktsioonid

| Funktsioon | Asukoht | Roll | Osa |
|---|---|---|---|
| `pipeline.run`, `process_layer`, `resample_to_10m`, `groupings` | `pipeline.py:218, 179, 139, 61` | kihid, 10 m, rühmad | P1–P2, M1 |
| `catalog.zero_values` | `catalog.py:271` | NoData → 0 | P2, M2 |
| `aggregate.aggregate_layer`, `validity`, `extended_grid`, `_row_runs`, `_baas_chunk` | `aggregate.py:247, 99, 57, 137, 148` | lugemine, kehtivus | P1–P2, M1 |
| `aggregate.value_counts` | `aggregate.py:201` | kadudeta sagedustabel | M1 |
| `aggregate.segment_medians` | `aggregate.py:221` | plokimediaanid | P3, M6 |
| `stats.make_units` | `stats.py:84` | ühikud | P2, M3 |
| `stats._block_medians`, `analyse_layer_median` | `stats.py:441, 461` | paaritatud Δ (v2), ühiku mediaanid, paaritamata Δ | P3–P6, M3–M7 |
| `stats.analyse_layer` | `stats.py:204` | keskmisepõhine (paralleelne), `enough_*`, `n_strata` | P6 (võrdlus) |
| `stats.cluster_index`, `_boot_weights`, `_boot_summary`, `_ratio`, `bh_fdr` | `stats.py:127, 145, 151, 175, 110` | bootstrap, CI, p, FDR | P6, M7 |
| `median.ValueTable` (`load`, `median`, `_kth`, `total`) | `median.py:57` | täpne mediaan | M2–M6 |
| `median.cluster_boot_medians`, `segments`, `cluster_boot_medians_seg` | `median.py:142, 231, 252` | täpne bootstrap | M7 |
| `analysis.run`, `_join_median`, `add_fdr` | `analysis.py:324, 297, 482` | koondamine, olulisus | P6–P7 |
| `kaasnev.summarise`, `median_table`, `add_medians`, `_big_groups` | `kaasnev.py:106, 222, 261, 201` | tulemustabel | M3, M7 |
| `export._r`, `build_data`; `kaasnev_export._cells`, `evidence` | `export.py:20, 39`; `kaasnev_export.py:84, 217` | ümardus, JSON | P7, M7 |
| `estOf`, `passes`, `fmt`, `pct`, `cellView`, `exactMed`, `levelsChart`, `pairTable` | `app.js:113, 120, 18, 29, 442, 805, 910`; `common.js:17` | kuvamine | P7, M7 |

## Tehtud kontrollid

| Kontroll | Tulemus |
|---|---|
| `uv run pytest` (sh brute-force testid: `test_median_estimates_match_brute_force`, `test_union_median_matches_numpy`, `test_cluster_bootstrap_medians_are_exact`, `test_segment_medians_match_numpy`) | 80 testi läbitud |
| Sait ehitati ajutisse kausta (`oks site --out <scratchpad>`) ja üks hinnang jälgiti `paarid.parquet` → `paarid.json` → vormindus | kooskõlas (vt P7 näidet) |
| `enough_m` (keskmisepõhisest funktsioonist) vs `p_m_med` olemasolu (mediaanipõhine piisavus) | 0 lahknevust 4180 real; sama `enough_u` ja `p_u_med` kohta |
| `median_a`/`median_b` liitmine (`_join_median`) | 0 puuduvat |
| `delta_m_med` puudub, kuigi `enough_m` on tõene | 0 rida |
| Polars `group_by` −0,0 ja 0,0 korral (`ValueTable.load`) | liidetakse üheks väärtuseks, nullide loendus on õige |
| Katvus v2-s (`vordlus_kihid.csv`, `kate_v2`) | kõigil mitte-erandkihtidel 1,0; erandkihtidel 0,41–0,94 |
| Repo enda sõltumatu mediaanikontroll V8 (`data/tulemused/validatsioon_keskmised.json`, uuesti ei käivitatud) | 0 lahknevust: 3527 ühiku mediaani, 4253 tüüp × seisundi mediaani, 3952 paaritatud Δ; 6 suurima sagedustabeliga kihil ühiku mediaanid kontrollimata |
| `git status` pärast kontrolle | projekti failid muutmata |

## Leitud eeldused

1. **Stratum on alati plokk × alamökosüsteem**, ka ökosüsteemi taseme paaritatud hinnangul. Ökosüsteemi Δ sisaldab ainult nende alamökosüsteemide stratumeid, millel on vähemalt kaks seisundit. Ökosüsteemi paaritamata mediaan (`median_a`, `median_b`) hõlmab aga ökosüsteemi kõiki seisundiga klasse.
2. **Kaal ja piisavus põhinevad pikslite arvul kihi enda lahutusvõimel.** 5 m kihil on 1 ha = 400 pikslit, 10 m kihil 100 pikslit. 930 m, 1 km ja vektorkihid arvutatakse 10 m ruudustikul.
3. **10 m kihtidel võetakse baaskaardi 5 m kood lähima naabriga.** Iga 10 m piksel saab ühe nelja 5 m piksli koodi. Veebi pindalad (`pind`, km²) tulevad aga baaskaardi 5 m täisresolutsioonist.
4. **Bootstrap valib igas korduses multinomiaalselt 988 klastrit kogu 10 km ruudustikust** (38 × 26, nurk 369 km / 6377 km, mitte ümmargused 10 km jooned). Valikus on ka andmeteta klastrid, seega varieerub andmetega klastrite arv kordustes. Sama seeme ja kaalud on kõigil kihtidel ja mõlemal hinnangul.
5. **p-väärtusel on alampiir 1/(B+1) = 1/4001.** Kui alla 90 % kordustest annab tulemuse, jäävad CI ja p tühjaks.
6. **FDR-perekond on tase.** Ökosüsteemi ja alamökosüsteemi tase on eraldi perekonnad, kumbki üle kõigi kihtide ja kõigi kolme seisundipaari. Segumudel on eraldi perekond.
7. **NoData → 0 kasutab kihitabelis deklareeritud NoData väärtust** (`zero_values`). Ruudustiku laiendus täidetakse aga rastri enda NoData väärtusega (`_read_padded`). Kui need erineksid, jääksid pikslid valimist välja. Andmetel kontrollitud: kõigil mitte-erandkihtidel on katvus 1,0, seega praegu mõju pole.
8. **Plokimediaanide kvantiilid** (`mq05…mq95`, kastdiagramm) arvutatakse `np.quantile` vaikemeetodiga, mis interpoleerib plokimediaanide vahel lineaarselt. Need on kirjeldavad ega mõjuta hinnanguid.
9. **Tulemustabeli staatus** („ei paku“, „–“, „osaline kate“) arvutatakse klassitabeli loendustest. Mediaan on sama valimi peal.

## Vajab täiendavat kontrolli

Staatus pärast tellija otsuseid (2026-10-29).

1. **Keskmisepõhine paaritatud hinnang on väljundis mediaanipõhise kõrval. Otsus: lubatud, kui see ei lähe mediaanipõhisega segi.**
   * Asukoht: `stats.analyse_layer` (`stats.py:204-434`), `analysis.add_fdr` (`analysis.py:497-504`), `export.py:145-159, 263-269`.
   * Keskmisepõhised veerud (`delta_m`, `rel_m`, `ci_m_*`, `p_m`, `q_m`, `oluline_m`, `kooskolas`) on ainult **samades ridades** mediaanipõhiste `*_med` veergude kõrval:
     * `paarid.parquet`;
     * `tulemused_paarid.csv`;
     * `paarid.json`, mida veeb ei kasuta.
   * Nimekokkulepe on kirjas failis `docs/metoodika.md:119-120` („veerud `*_med`; sama arvutus keskmistega veerud ilma `_med` järelliiteta“).
   * Eraldi kasutatakse keskmisepõhiseid tulemusi ainult kahes kohas ja mõlemad on selgelt märgistatud:
     * segumudel: veebis „Võrdluseks: segumudel … keskmisel põhinev, uuriv“, `docs/tulemused.md` alapeatükk 3b;
     * v1 → v2 võrdlus: „v2 keskmine → v2 mediaan“.
   * Veebi hinnangud, tõendusbaas, Excel ja tundlikkus kasutavad ainult `*_med` veerge.
   * Jääkrisk: `_m` tähendab „paaritatud“ (*matched*), mitte „mean“. Ilma veergude kirjelduseta võib CSV-i lugeja `oluline_m` ja `oluline_m_med` segi ajada. Leevendus oleks veergude legend README-s või CSV kõrval. Seda ei ole tehtud.
2. **Suhteline muutus (Δ %) paaritatud hinnangul.** Δ ise vastab kokkuleppele: stratumite mediaanide vahed, millest võetakse kaalutud keskmine. Küsimus puudutab ainult protsenti, mida veebis Δ kõrval näidatakse.
   * Kood (`stats.py:688`): `rel_m_med = Δ / |Σw·ma / Σw|`. Nimetaja on halvema seisundi **stratumimediaanide kaalutud keskmine**.
   * Veebi infotekst (`app.js:142`): „Δ jagatud halvema seisundi mediaaniga“. Lugeja tõlgendab seda ühiku mediaanina (`median_a`), mida kohtspikker kõrval näitab.
   * Näide: metsad, `c_tonn_per_ha_final_2022_10m`, vilets → hea. Δ = 38,9; veebis +4,3 %.
     * Nimetaja koodis on 38,904 / 0,042599 = 913,3.
     * Kohtspikri `median_a` on 688. Sellega jagades saaks lugeja +5,7 %.
   * Kontrollida, kas infoteksti tuleb täpsustada. Arvutust ei ole muudetud.
3. **`indikaatorid.strength(NaN)` andis „tugev“. PARANDATUD** harus `claude/practical-knuth-zzw4kt` (pärast `b799458`).
   * Puuduv või NaN suhteline muutus annab nüüd tühja tugevuse.
   * Lisatud on test `tests/test_kaasnev.py::test_strength_scale`.
   * Praegustes andmetes selliseid ridu polnud (0), seega tulemused ei muutu.
4. **Ligikaudsed (histogrammipõhised) kvantiilid veebis. Otsus: graafikutel lubatud, kui need on selgelt märgitud. Põhitabelites peab olema täpne mediaan.** Kontrollitud:
   * täpne mediaan on kõigis põhitabelites:
     * tulemustabel ja Excel (`kaasnev` → `median_table`);
     * tabelivaade (`median_a`, `median_b`);
     * teenuse detaili statistikaplokk;
     * „Jaotuste võrdlus“ (mediaanide vahe, `exactMed`);
     * profiil;
     * algne seisundiklass;
   * ligikaudseid väärtusi on ainult graafikutel ja need on märgitud:
     * „Kihtide ülevaade“: „mediaan ≈“, kohtspikris „ligikaudne“, `app.js:747-753`;
     * järjestus „viltuse järgi“, `app.js:778`;
     * jaotuskaardi „25–75 % (ligikaudne)“, `app.js:520-524`.
   * Avatud punkte ei ole.
5. **Tabelivaate CSV ja stsenaariumi mediaanide vahe kasutavad ümardatud (5 olulist numbrit) väärtusi. Otsus: lubatud.**
6. **Toorandmetest sõltumatut ümberarvutust selles töös ei tehtud.** Repos ei ole rastreid (`data/cache/`) ega plokitasandi faile (`data/derived/plokid/`). Mediaanide õigsus tugineb testidele (läbitud) ja repo enda kontrollile V8 (`scripts/valideeri_keskmised.py`, tulemus `validatsioon_keskmised.json`, uuesti ei käivitatud).
   * V8 kontrollis paaritatud `delta_m_med` sõltumatult **kõigil 34 kihil**: 3952 hinnangut, 0 lahknevust.
   * Ühik × seisundi (`lahtrid.median`, `median_nz`) ja tüüp × seisundi (`kaasnev_tuup_seisund.median`) mediaanid jäid kontrollimata kuuel kihil. Põhjus: nende sagedustabel ületas skripti piiri `--max-rows` (vaikimisi 60 000 000 rida).

     | Kiht | Nimi | Ühik | Sagedustabeli read |
     |---|---|---|---|
     | `puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m` | Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (ETS börsihind) | EUR/ha | 700 434 005 |
     | `okosusteemide_tugi_tolmeldajatele_2022_10m` | Ökosüsteemide tugi tolmeldajatele | indeks 0–1 | 392 762 219 |
     | `erosioon_c_kg_ha_a_2022_10m` | Orgaanilise süsiniku ärakanne | kg/ha/a | 236 498 290 |
     | `erosioon_p_kg_ha_a_2022_10m` | Fosfori ärakanne | kg/ha/a | 234 155 014 |
     | `erosioon_p_eur_ha_a_2022_10m` | Fosfori mullaerosiooniga ärakande hind | EUR/ha/a | 234 154 813 |
     | `puitne_biomass_c_t_ha_kogu_eesti_sum_2022_5m` | Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 76 152 073 |

   * V8 ei kontrolli üheski kihis suurte ökosüsteemide mediaane (`kaasnev_suured.median`) ega algse seisundiklassi mediaane (`algklassid`). Neid katavad ainult üksustestid.
   * Kontroll: käivitada masinas, kus on `data/derived/plokid/`, käsk `uv run python scripts/valideeri_keskmised.py --max-rows 800000000`. Mälu peab olema piisavalt.
7. **Avaldatud leht.** Peaaadressil on endiselt v1 sait (commit `5aa4596`). See dokument kirjeldab v2 lehte (`…/v2/`), mis ehitatakse failidest `site_src/` ja `data/tulemused/` seisuga `b799458`.
