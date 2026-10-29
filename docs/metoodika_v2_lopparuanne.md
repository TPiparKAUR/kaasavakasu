# Metoodika v2: lõpparuanne

Töö haru `claude/nifty-bohr-4eqjct`, võrdlusalus (metoodika v1) commit `5aa4596`. Otsused: [metoodika_v2_otsused.md](metoodika_v2_otsused.md),
tööplaan ja seis: [metoodika_v2_tooplaan.md](metoodika_v2_tooplaan.md). Kõik arvud on täisjooksust (34 kihti, 2026-10-28).

## 1. Muudetud failid

`git diff --stat 5aa4596..HEAD`: 61 faili (koos selle aruandega).

| Rühm | Failid |
|---|---|
| Kood (`src/oks/`) | `aggregate.py`, `analysis.py`, `andmetabel.py`, `catalog.py`, `export.py`, `fields.py`, `kaasnev.py`, `kaasnev_export.py`, `pipeline.py`, `report.py`, `sitebuild.py`, `stats.py`; uued `median.py`, `vordlus.py` |
| Testid (`tests/`) | `test_aggregate.py`, `test_kaasnev.py`, `test_stats.py`; uued `test_fields.py`, `test_median.py`, `test_vordlus.py` |
| Sait (`site_src/`) | `app.js`, `sections/common.js`, `home.js`, `quality.js`, `results.js`, `scenario.js`; uus `sections/compare.js` |
| Skriptid | `valideeri_keskmised.py`, `valideeri_veeb.py` (v2 kontrollid); uus `vordle_metoodikad.py`; `naide_paaritatud.py`, `valideeri_baaskaart.py` ainult `ruff format` (CI vormingukontroll oli v1-s punane) |
| Dokumendid | `README.md`, `docs/metoodika.md`, `docs/keskmiste_arvutus.md` (v1 märge), `docs/tulemused.md`, `docs/andmekataloog.md` (genereeritud); uued `docs/metoodika_v2_otsused.md`, `metoodika_v2_tooplaan.md`, see aruanne |
| Andmed | `data/teenused.csv` (lammi ühik), `data/tulemused/*` (v2 tulemused, uued `algklassid`, `paarid_segumudel`, `lahtrid_segumudel`, `vordlus_*.csv`) |
| Avaldamine | `.github/workflows/pages.yml` (v1 peaaadressil muutmata, v2 `/v2/` ainult otselingiga, `noindex`) |

## 2. Koodimuudatused faili kaupa

* **`catalog.py`** – `NODATA_EXCLUDED` (viis erandkihti); `zero_values`: NoData loetakse nulliks, v.a erandkihid (seal ainult deklareeritud NoData 0); lammi ühik `EUR/ha/a`.
* **`aggregate.py`** – kadudeta sagedustabel `value_counts` (e_km, n_km, kood, väärtus, n) ploki-rea failidena; plokimediaanid `segment_medians` (kõik ja nullist erinevad); `extended_grid`/`_read_padded`: rastri ulatusest väljas olevad baaskaardi pikslid loetakse samas ruudustikus NoData-ks (→ 0). **Rasterite joondamise loogika (`_row_runs`, `_baas_chunk`, EPSG:3301 kontroll, lähim naaber) on muutmata.**
* **`fields.py`** – vektori rasterdamisel NaN/NULL ja −1 → 0; kattuvate polügoonide korral suurim väärtus (stabiilne sortimine, viimane kirjutab).
* **`pipeline.py`** – üle 10 m rastrid viiakse 10 m ruudustikule (`resample_to_10m`, lähim naaber, NoData säilib); lamm lisatud vektorkihtidesse; sagedustabeli ja plokimediaanide teed; `done()`.
* **`median.py`** (uus) – `ValueTable` (täpne mediaan klasside ühendis poolitusega üle ujukomaarvude järjestuse); täpne klastribootstrap (`cluster_boot_medians`, `segments`, `cluster_boot_medians_seg`; suurte valimite jaoks mälusäästlik täpne algoritm).
* **`stats.py`** – `analyse_layer_median`: ühiku/klassi mediaanid, plokikvantiilid, paaritatud mediaanipõhine Δ (stratum = 1 km plokk × alamökosüsteem, sama kaal ja bootstrap), paaritamata mediaanide vahe täpse bootstrapiga; `cluster_expr`. Keskmisepõhine `analyse_layer` on muutmata.
* **`analysis.py`** – mediaaniveergude liitmine, FDR mediaani p-väärtustele (eraldi perekonnad), segumudel eraldi failidesse (võrdluseks), madala lahutusvõime märkused, tundlikkus mediaani järgi, valikuline kihtide vahemälu (katkenud jooks jätkub).
* **`kaasnev.py`** – tüüp × seisund ja suurte ökosüsteemide mediaan klasside pikslite ühendist (`median_table`, `add_medians`).
* **`export.py`, `kaasnev_export.py`, `andmetabel.py`, `sitebuild.py`** – mediaaniveerud saidi JSON-is ja Excelis, märgid ‡ (madalam lahutusvõime) ja § (erandkiht), `algklassid.json`, `segumudel.json`, `vordlus.json`.
* **`report.py`** – `docs/tulemused.md` mediaanipõhine (Δ, CI, olulisus), segumudel võrdluseks.
* **`vordlus.py`** (uus) – v1 → v2 võrdlus kaheks osaks: valimireeglid (v1 keskmine → v2 keskmine) ja statistik (v2 keskmine → v2 mediaan).
* **Sait** – põhiväärtus mediaan; vaated „Kõik pikslid“ / „Ainult pikslid, kus teenus esineb (väärtus > 0)“; kuumkaardil suhteline muutus või muutus kihi ühikus; stsenaariumis mediaanide vahe /ha ja pindalaga korrutamine keskmiste vahe järgi; jaotis „Metoodika võrdlus“.

## 3. Mõju tabel

| Väli | Vana loogika (v1) | Uus loogika (v2) | Mõju (täisjooks) |
|---|---|---|---|
| Keskväärtus tulemustabelis | aritmeetiline keskmine | täpne pikslimediaan (keskmine jääb kõrvale) | 65 % tüüp × seisundi lahtritest on mediaan keskmisest väiksem; 26 % lahtritest on mediaan 0, kuigi keskmine > 0 |
| Paaritatud Δ (`delta_m_med`) | stratumi keskmiste vahe | stratumi mediaanide vahe, sama kaal ja bootstrap | olulisi ökosüsteemi tasandil 224 (keskmine, v2 valim) → 184 (mediaan) |
| Rastri NoData | välja jäetud (v.a NoData = 0) | 0; erandkihid välja | katvus 95–99 % → 100 % 13 kihil; keskmise tüüpiline muutus ≤ 2,5 % |
| Erandkihid (5) | NoData välja | NoData välja (muutmata) | valim identne (keskmine muutus 0 %) |
| Ruudustikust väljas baaskaart | välja | 0 (erandkihtides välja) | ≤ 0,15 % pindalast |
| Vektor (toiduteenus, biotõrje) | ainult polügoonid | polügoonist väljas/NULL/−1 = 0; kattumisel maksimum | katvus 16 % → 100 %; keskmine langeb ~100 % (sisuliselt teine suurus: teenus kogu pindala kohta) |
| 930 m ja 1 km kihid | ainult segumudel (ökosüsteemi tase) | 10 m lahutusvõimel põhianalüüs, segumudel võrdluseks | hinnangud ka alamökosüsteemi tasandil; lammi olulisi 10 → 0 |
| Lammi ühik | EUR | EUR/ha/a | silt |
| Pindalad | baaskaardi 5 m pikslid | muutmata | 152 tüüp × seisundit, 0 erinevust |

## 4. Oluliselt muutuvad tulemused

* **Vektorkihid `toiduteenus_2022`, `biotorje_2022`** – väärtus on nüüd kogu klassi pindala kohta (polügoonist väljas 0), mitte ainult põllumassiividel: keskmine väheneb tüüpiliselt ~99 %, mediaan on 68 % lahtritest 0. Olulisi ökosüsteemi hinnanguid 2–3 (v1) → 3 (v2), lisandus 9 hinnangut.
* **Nullirohked kihid** (marjad, seened, erosioon, madala lahutusvõimega kihid) – mediaan erineb keskmisest ~90–100 % ja on paljudes lahtrites 0 (mustikad/pohlad 88 %, seened 66 %, erosioon P 41 %). Tulemustabel näitab siis ka mediaani kohtades, kus teenus esineb.
* **Erosioon metsades** – kolmel paaril (C ärakanne vilets → hea, P ärakanne ja P hind keskmine → hea) muutus Δ märk: keskmine väheneb seisundi paranedes (üksikud suure ärakandega pikslid viletsas seisundis), mediaan suureneb veidi (tüüpiline piksel). Mõlemad on õiged eri küsimustele.
* **Madalama lahutusvõimega kihid** – v1 segumudel andis lammile 10 ja vee puhastamisele 9 olulist ökosüsteemi hinnangut; 10 m lahutusvõimel jääb olulisi 0 ja 2. Segumudeli eeldus (väärtus sõltub ainult klassist) andis tugevama, kuid mudelipõhise erinevuse.
* **Kasemahl** – mediaan on keskmisest ~57–66 % väiksem; olulisi 3–4 → 2.
* **Kokku ökosüsteemi tasandil** (v1 → v2): 168 hinnangut jäi oluliseks sama suunaga, 48 ei ole enam oluline, 12 muutus oluliseks, 3 muutis suunda, 27 lisandus (v1-s andmeid ei piisanud). Alamökosüsteemi tasandil vastavalt 902, 207, 63, 8 ja 535.

## 5. Vähe muutuvad tulemused

* **Valim muutumatu (11 kihti)**: loodusturism, õhusaaste, tolmeldajad, puidu biomassi süsinik (niit, soo, ETS), virgestus EUR, kliimaregulatsioon, seente hind – keskmine identne v1-ga; olulisus muutub ainult statistiku tõttu (nt loodusturism EUR 11 → 9).
* **Pidevad, vähe nulle sisaldavad kihid** – sidusus, elupaigahüve, virgestus, mulla süsinik, tolmeldajad: mediaan erineb keskmisest 2–10 %, olulisi hinnanguid sama arv (nt 12 → 12, 11 → 11).
* **Erandkihid** – valim identne v1-ga; olulisus muutub ainult statistiku tõttu (mustikad/pohlad 5 → 5).
* **Pindalad** ja seisundite vastavus – identsed.
* **Tundlikkus** (mediaanipõhine): olulistest säilis 90–100 % (ökosüsteem) ja 86–100 % (alam); klastri suurus ja seeme ei muuda peaaegu midagi (98–100 %).

## 6. Tagasipööramise juhend

v1 on commit `5aa4596` (sildi tegemine ei olnud sessioonis lubatud; SHA on püsiv).

1. **Enne liitmist**: haru lihtsalt mitte liita; vaikeharu ja peaaadressi sait jäävad v1-ks.
2. **Pärast squash-liitmist**: `git revert <squash-commit>` vaikeharus (üks commit, taastab kõik muudetud failid v1 seisu). Ühe faili taastamine: `git checkout 5aa4596 -- <tee>`.
3. **Sait**: `pages.yml` ehitab peaaadressile niikuinii v1 (commit `5aa4596`, muutmata); v2 on `/v2/`. Pärast `git revert`-i kaob `/v2/` järgmise Pages-ehitusega. Lõpliku vahetuse korral ehitada v2 otse `_site`-i ja eemaldada v1 sammud (kommentaar töövoos).
4. **Andmed**: v1 tulemustabelid (`data/tulemused`) on git'is commit'is `5aa4596`, seega v1 sait ehitub ilma ümberarvutuseta. Kohalikud plokitabelid (`data/derived/plokid`, ei ole git'is) on v2 reeglitega; v1 koodi täielikuks taasarvutuseks käivitada `oks aggregate --force` ja `oks fields --force` (~2 h).
5. **Analüüsi vahemälu** `data/cache/analyys` (ei ole git'is) tuleb koodi muutmisel kustutada.

## Kontrollnimekiri

| Kontroll | Tulemus |
|---|---|
| Testid | 80 läbivad; `ruff check .`, `ruff format --check .`, `mypy src` rohelised; GitHub CI ja Pages-töövoog rohelised |
| Mediaanid | täpsed (iga piksel üks vaatlus); sõltumatu ümberarvutus V8: 0 lahknevust (3 527 ühiku, 4 253 tüüp × seisundi mediaani, 3 952 paaritatud Δ; ühiku mediaanid kontrollimata 6 suurima sagedustabeliga kihil mälu tõttu) |
| Rasterreeglid | NoData = 0, erandkihid välja: testid `test_kaasnev.py::test_zero_values_policy`, `test_aggregate.py`; katvus 100 % (erandid muutmata) |
| Vektorreeglid | väljas/NULL/−1 = 0, kattumisel maksimum: `test_fields.py` |
| Paaritatud hinnangud | mediaanipõhine Δ; V2 (keskmine) ja V8 (mediaan) 0 lahknevust |
| EPSG:3301 ja joondus | joondamise kood muutmata; pindalad v1-ga identsed |
| Dokumentatsioon | `metoodika.md`, `README.md`, `keskmiste_arvutus.md` (v1 märge), genereeritud `tulemused.md`, `andmekataloog.md` |
| Veebileht | v2 ehitatud ja brauseris kontrollitud (JS-vigu 0, telefonilaius); veebikontroll V8–V10 0 lahknevust; v1/v2 avaldamine töövoos |

**Avatud:** haru on push'itud, PR-i ei ole loodud (luuakse soovi korral). Täisjooksu ajal katkes analüüs kaks korda (mälu, konteineri taaskäivitus); parandused (mälusäästlik täpne bootstrap, jätkatav vahemälu) on testitud ja tulemused nendega identsed.
