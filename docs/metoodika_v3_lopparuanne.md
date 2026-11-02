# Metoodika v3: lõpparuanne

v3 lisab statistilisse analüüsi kuivad ja märjad metsad (tase `ruhm`, koodid 31 ja 32) samale tasemele suurte
ökosüsteemidega. Võrdlusalus on metoodika v2, commit `de7aca9`. Töö on harus `claude/confident-sagan-iituxn`.

Seotud dokumendid:
* otsused: [metoodika_v3_otsused.md](metoodika_v3_otsused.md);
* analüüs ja v4 spetsifikatsioon: [metoodika_v3_v4_ettepanek.md](metoodika_v3_v4_ettepanek.md).

Arvutus tehti 2026-11-01…02 nullist ja ajajoon oli järgmine:

| Samm | Aeg | Sisu |
|---|---|---|
| Plokitabelid | 16:41–20:20 | arhiivist v2 koodiga (`git worktree` commit'is `de7aca9`), 31 rastrit ja 4 vektorit |
| Analüüs | 20:20–23:07 | `oks analyse` |
| Tundlikkus | 23:07–03:51 | 5 varianti |

## 1. Muudetud failid

`git diff --stat de7aca9..HEAD` näitab 21 faili väljaspool kausta `data/`. Lisaks muutusid `data/tulemused` failid.

| Rühm | Failid |
|---|---|
| Kood | uus `src/oks/ruhmad.py`; `analysis.py`, `stats.py` (ainult lisaveerud), `kaasnev.py` (definitsioon `ruhmad`-ist), `export.py`, `report.py`, `config.py` (`METHOD_VERSION = "v3"`) |
| Testid | uus `tests/test_ruhmad.py` (19 testi, kokku 99) |
| Sait | `site_src/app.js`, `sections/quality.js`, `sections/scenario.js`, `styles.css` |
| Skriptid | uued `scripts/vordle_v2.py`, `scripts/valideeri_ruhmad.py`; `scripts/valideeri_veeb.py` (V11, V12) |
| Avaldamine | `.github/workflows/pages.yml`: `/v2/` ehitatakse commit'ist `de7aca9`, `/v3/` vaikeharust |
| Dokumendid | uued `metoodika_v3_otsused.md`, `metoodika_v3_v4_ettepanek.md`, see aruanne; `metoodika.md` (§ 5.5), `README.md`, genereeritud `tulemused.md` |
| Andmed | `data/tulemused/{paarid,lahtrid,algklassid,jaotused,uhikud,klassid,diagnostika}.parquet`, `tundlikkus.csv`, `validatsioon_*.json` |

Muutmata jäid:
* kood: `median.py`, `aggregate.py`, `pipeline.py`, `fields.py`, `catalog.py`, `andmetabel.py`, `vordlus.py`, `sitebuild.py`;
* tulemusfailid: `kaasnev_*.parquet`, `vordlus_*.csv`, segumudeli failid ja `parameetrid.csv`.

## 2. Kontrollid

| Kontroll | Tulemus |
|---|---|
| **V-R1** `vordle_v2.py`: v3 ökosüsteemi ja alamökosüsteemi read vs v2 (git `de7aca9`), 12 faili | **0 erinevust.** Mediaanipõhised hinnangud, CI-d, p- ja q-väärtused ning olulisuse lipud on bitti-bitti samad. Keskmisepõhine Δ (`delta_m`, CI; veebis ei kuvata) erineb ≤ 6·10⁻¹⁴ suhteliselt ja η² ≤ 1,3·10⁻⁹ suhteliselt (ujukomaarvude liitmisjärjekord). |
| V-R2 metsa Δ = kuiv, märg ja muu kooslus kaalutult | 102 / 102 kooskõlas |
| V-R3 paaride arv mets = kuiv + märg + muu | 102 / 102 |
| V-R4 rühma mediaan = tulemustabeli (`kaasnev_suured`) mediaan | 204 / 204 |
| V-R5 rühma jaotus = alamökosüsteemide summa | 5 582 / 5 582 |
| V-R6 `level_b − level_a = delta_m_med` | 4 156 / 4 156 |
| V-R7 rühmade FDR ainult rühmade p-väärtustest | 204 / 204 |
| Analüüsi sisekontroll: rühmajooksu alamökosüsteemi read = põhijooksu omad (iga kiht) | läbitud 34 kihil |
| Veeb V8–V12 (tulemustabel, stsenaarium, Excel, kuumkaardi rühmalahtrid, stsenaariumi rühmatõendus) | 0 lahknevust, JS-vigu 0; telefonilaiusel ilma horisontaalse kerimiseta |
| `pytest`, `ruff check`, `ruff format --check`, `mypy src` | 99 testi läbivad, kõik rohelised |
| Baaskaardi fail | MD5 kontrollsumma vastab serveri ETag-ile |

V-R1 näitab ka seda, et kogu ahel arhiivist tulemusteni on reprodutseeritav.

## 3. Kuivade ja märgade metsade hinnangud

v3 ei lisa uusi andmeid ega uut meetodit. See teeb sama v2 arvutuse kahe uue rühma kohta. Hinnanguid on
204 = 34 teenusekihti × 2 rühma (kuivad metsad, märjad metsad) × 3 seisundipaari (vilets → keskmine, keskmine → hea,
vilets → hea).

Iga hinnang on paaritatud Δ: kui palju erineb teenus parema ja halvema seisundi vahel samas 1 km plokis ja samas
alamökosüsteemis, koondatuna üle rühma alamökosüsteemide. Näiteks puitse biomassi süsinik kuivas metsas, vilets → hea:
Δ = +84,5 t C/ha (+366 %), 95 % CI 81,8…87,2.

Rühmad on metsa osad. Seetõttu ei ole nende hinnangud metsa hinnangust sõltumatud: metsa hinnang on kuiva metsa, märja
metsa ja „muu koosluse“ kaalutud koondhinnang. Sisuliselt uus info on rühmadevaheline erinevus. Seda erinevust formaalselt
ei testita (otsus K3).

| | Hinnanguid | Paaritatud: piisavalt andmeid | Olulisi (q < 0,05) | Paaritamata olulisi |
|---|---|---|---|---|
| Kuivad ja märjad metsad | 204 | 204 | 129 | 111 |

| Rühm | Seisundipaar | Kasvab (oluline) | Väheneb (oluline) |
|---|---|---|---|
| Kuivad metsad | vilets → keskmine | 19 | 5 |
| Kuivad metsad | keskmine → hea | 19 | 0 |
| Kuivad metsad | vilets → hea | 21 | 1 |
| Märjad metsad | vilets → keskmine | 17 | 8 |
| Märjad metsad | keskmine → hea | 20 | 2 |
| Märjad metsad | vilets → hea | 17 | 0 |

* **Vastupidise märgiga** (mõlemas rühmas olulised) on mustikate ja pohlade saagikus ja tulu paaris vilets → keskmine.
  * Kuivas metsas: +15,6 kg/ha ja +39,0 EUR/ha.
  * Märjas metsas: −0,30 kg/ha ja −0,76 EUR/ha.
  * Metsa ühine hinnang (+8,6 kg/ha) peidab selle erinevuse.
* Kokku on 9 hinnangut olulised ainult ühes rühmas. 2 juhul on rühm oluline, kuid kogu mets mitte.
* **Suurimad muutused vilets → hea:**
  * puitse biomassi süsinik kuivas metsas +366 %, märjas +212 %;
  * söögiseened +115 % ja +107 %;
  * elupaikade säilitamine +129 % ja +121 %.

  Täielik tabel on failis `docs/tulemused.md` § 2–3.
* **Tundlikkus:** 129 olulisest hinnangust jäi viies variandis oluliseks ja sama märgiga 125–129 (97–100 %). Variandid on
  5 ja 20 km klaster, 0,25 ja 4 ha miinimumpindala ning teine seeme. Δ astakkorrelatsioon põhijooksuga on ≥ 0,95. See
  kontrollib, kas tulemus sõltub analüüsi parameetritest; uusi andmeid see ei lisa. v2 tasemete read on samad mis v2-s.

## 4. Mõju olemasolevale süsteemile

| Osa | Mõju |
|---|---|
| v2 hinnangud ja olulisus | ei muutunud (V-R1) |
| `/` (v1) ja `/v2/` lehed | ei muutu; mõlemad ehitatakse oma commit'ist |
| `/v3/` | kuivad ja märjad metsad on kuumkaardil (metsa kõrval, lüliti „Kuivad ja märjad metsad“), teenuse detailis, profiilis, jaotustes ja tabelis; kvalitatiivses jaotises veerud „Kuivad metsad“ ja „Märjad metsad“; stsenaariumis kuivade ja märgade metsade paaritatud tõendus (v2-s puudus); päises „metoodika v3“ |
| `tulemused_paarid.csv` | lisandusid read `tase = ruhm` |
| Excel | kood muutmata; lehel „Tõendusbaas (Δ)“ lisandusid kuivade ja märgade metsade read |
| `paarid.parquet` | lisaveerud `level_a_m_med`, `level_b_m_med`, `sum_w_m_med` v4 jaoks (veebi ei ekspordita) |

## 5. Tagasipööramine

1. **Enne liitmist:** haru lihtsalt mitte liita.
2. **Pärast liitmist** („Squash and merge“): `git revert <v3 squash-commit>` ja push.
   * Kood, tulemusfailid ja dokumendid on siis täpselt v2 omad.
   * `/v3/` kaob järgmise Pages-ehitusega.
   * `/v2/` ja `/` ei muutu.
3. **Ühe faili v2 versioon:** `git checkout de7aca9 -- <tee>`.

## 6. Märkused

* **Arvutusaeg.** Analüüs võttis 2 h 47 min (v2 täisjooks 67 min). Põhjused:
  * rühmade läbikäik loeb sagedustabeli teist korda;
  * kontrolliks arvutatakse uuesti rühma alamökosüsteemide paaritamata bootstrap.
* **Rööpne allalaadimine.** Esimene plokitabelite jooks katkestati, sest kolm protsessi laadisid baaskaarti korraga samasse faili.
  Fail kontrolliti ETag-i vastu ja jooks käivitati uuesti nii, et baaskaart laaditakse enne. See on v2 `pipeline.run` omadus:
  baaskaart peab enne olemas olema. Koodi ei muudetud.
* **Vahekihid.** Plokitabelid (`data/derived/plokid`, 6,6 GB) on ainult selles konteineris ega ole git'is.
* **v4** on ainult spetsifikatsioon ([metoodika_v3_v4_ettepanek.md](metoodika_v3_v4_ettepanek.md) § 4.6). Vajalikud
  paaritatud tasemed on v3 tulemustes olemas, nii et v4 ei vaja uut arvutust.
