# Metoodika v3 ja v4: analüüs ja tehniline ettepanek

**Seis:** ettepanek; otsused tehtud 2026-11-01 (§ 3). Ainus tehtud muudatus: `/v2/` leht ehitatakse kindlast
commit'ist `de7aca9` (§ 4.5). Analüüsikoodi ja tulemusfaile ei ole muudetud.
**Võrdlusalus:** metoodika v2, commit `de7aca9` (vaikeharu HEAD 2026-11-01). Metoodika v1 on commit `5aa4596`.
**Arvud:** kõik selle dokumendi arvud on arvutatud repo failidest `data/tulemused/paarid.parquet` ja `uhikud.parquet`
(v2 täisjooks, 34 kihti, 4 180 paari). Uued failide, funktsioonide ja veergude nimed on **ettepanekud**, mitte olemasolev kood.

| Versioon | Sisu | Staatus |
|---|---|---|
| v1 | keskmised, NoData välja | commit `5aa4596`, sait peaaadressil |
| v2 | täpsed pikslimediaanid, NoData = 0, paaritatud mediaanipõhine Δ | commit `de7aca9`, sait `/v2/` |
| v3 | kuivad ja märjad metsad statistilise analüüsi ühikuna (kuumkaart jt vaated) | spetsifikatsioon (§ 4.1–4.4), rakendamata |
| v4 | tulemustabeli paaritatud vaade | ainult spetsifikatsioon (§ 4.6) |

---

## 0. Lähteolukord koodis

**Kus kuivad ja märjad metsad on olemas.** `kaasnev.FOREST_SPLIT` (koodid 31 ja 32) jagab metsa alamökosüsteemi koodide järgi:
kuivad = 30100 salu-, 30500 palu-, 30600 laane-, 30700 loo-, 31000 nõmmemets; märjad = 30200 soovikumets,
30300 samblasoomets, 30400 rohusoomets, 30800 kõdusoomets, 30900 rabastuv mets. 31100 ja 31200 („Muu (metsa)kooslus“) on
ainult kogu metsas. Jaotust kasutavad tulemustabeli vaade „Suured ökosüsteemid“ (`kaasnev_suured.parquet`, paaritamata pikslimediaan),
avaleht ja stsenaariumi valikud.

**Kus need puuduvad.** Statistilise analüüsi ühikud tulevad funktsioonist `stats.make_units`. Seal on kaks taset: `okosusteem`
(4 ökosüsteemi) ja `alam` (39 alamökosüsteemi, millel on vähemalt kaks seisundit). Metsarühma taset ei ole. Seetõttu puuduvad
kuivad ja märjad metsad:

* kuumkaardil (paaritatud ja paaritamata), teenuse detailis, profiilis, jaotustes, kihtide ülevaates, statistilise analüüsi
  tabelis ja `tulemused_paarid.csv`-s;
* tõendusbaasis `tendus.json` (`kaasnev_export.evidence`). Kvalitatiivne jaotis ja stsenaarium otsivad sealt paaritatud
  tõendust taseme `okosusteem` järgi. Stsenaariumis saab valida „Kuivad metsad: kõik tüübid kokku“, kuid paaritatud tõendus
  selle rea kohta jääb tühjaks (`scenario.js`, rida 36);
* genereeritud dokumendis `docs/tulemused.md`.

**Tulemustabel** (`results.js`) näitab ainult paaritamata taset: täpset pikslimediaani tüübi või suure ökosüsteemi ja seisundi
kohta (`kaasnev.median_table`). Paaritatud hinnanguid (`paarid.json`) see ei kasuta.

---

## 1. Teaduslik hinnang

### 1.1 Kuivade ja märgade metsade lisamise mõju v2 metoodikale (v3)

**Hinnatav suurus.** Rühm *g* koosneb alamökosüsteemidest *A_g*. Paaritatud hinnang rühmale on

  Δ_g = Σ_{i ∈ S_g} w_i·d_i / Σ_{i ∈ S_g} w_i,  S_g = {stratum i = (1 km plokk, alam) : alam ∈ A_g, mõlemad seisundid ≥ 1 ha},

kus d_i on stratumi seisundite täpsete pikslimediaanide vahe ja w_i = n_a·n_b/(n_a+n_b). See on **sama hinnang mis v2
ökosüsteemi tasemel**, ainult stratumite hulk on kitsam. Stratumi definitsioon, d_i, kaal, miinimumpindala, `min_strata`,
`min_clusters`, 10 km klastrid, B = 4 000 ja seeme (bootstrap-kaalude maatriks W) ei muutu.

**Mis ei muutu:**

* ükski v2 hinnang. Rühm on uus agregatsioonitase olemasolevatest stratumitest, uusi stratumeid ei teki;
* tulemustabeli väärtused: `kaasnev_suured` read 31 ja 32 on juba olemas ja jäävad samaks.

**Kontrollitav seos (pesastatus).** Metsa stratumid on rühmade stratumite ühend:
S_mets = S_kuiv ∪ S_märg ∪ S_muu. Repo andmetes kehtib see täpselt (kihtide mediaan, paar vilets → keskmine:
93 424 = 48 539 + 44 259 + 626 stratumit). Seega

  Δ_mets = (W_kuiv·Δ_kuiv + W_märg·Δ_märg + W_muu·Δ_muu) / (W_kuiv + W_märg + W_muu),  W = Σw.

Sellest järeldub kolm asja.

1. Metsa hinnang on rühmade **täpsuskaaluga** keskmine. Kaal ei ole pindala.
2. „Muu (metsa)kooslus“ annab metsa hinnangusse ainult paaris vilets → keskmine (~0,7 % stratumitest; teistes paarides
   mediaan 8–9 stratumit kihi kohta). Seepärast ei ole metsa hinnang rangelt kuiva ja märja metsa kombinatsioon.
3. Kuiva ja märja metsa stratumeid on kõigis paarides sama suurusjärgu jagu (vilets → hea 8 667 / 7 730,
   keskmine → hea 12 345 / 13 425). Metsa hinnang on seega kahe rühma segu, ja kui rühmade Δ erinevad, peidab see
   heterogeensuse. See on ka lisamise sisuline põhjus: kaasneva kasu tabelis on juba näha, et mustikate seos seisundiga erineb kuivas ja märjas metsas
   (`docs/metoodika.md` § 5.4).

**Paaritamata hinnang rühma tasemel** on toorhinnang, samamoodi nagu ökosüsteemi tasemel (Simpsoni paradoks). Rühma sees
on seisundite koosseis tugevalt erinev. Märjas metsas on samblasoomets 31 % hea seisundi pindalast (486 / 1 551 km²), aga ainult
4 % viletsa seisundi pindalast (118 / 2 822 km²). Viletsa seisundi märjas metsas moodustavad peamiselt soovikumets ja
kõdusoomets. Paaritamata vilets → hea erinevus märjas metsas on seega suures osas alamökosüsteemide erinevus. Lehel peab
olema sama hoiatus mis ökosüsteemi tasemel.

**Mitmene testimine.** v2-s on FDR-perekond tase (`analysis.add_fdr`: `okosusteem`, `alam`). On kaks võimalust:

* (a) **eraldi perekond `ruhm`** (34 kihti × 2 rühma × 3 paari ≤ 204 testi). v2 q-väärtused jäävad muutumatuks;
* (b) rühmad ökosüsteemi perekonnas. Muudaks kõigi v2 ökosüsteemi taseme q-väärtusi ja võib muuta olulisuse lippe.

Rühmade ja metsa hinnangud on pesastatud ja positiivselt sõltuvad. BH kehtib ka positiivse regressioonisõltuvuse (PRDS) korral,
seega ei ole kumbki valik statistiliselt vale. (a) säilitab v2 tulemused bitti-bitti ja on soovitatav.
Puudus: kuumkaardil on ühes vaates kahe perekonna q-väärtused. Seda tuleb märgendada.

**Muud mõjud:**

* **Rühmade erinevuse test** (Δ_kuiv − Δ_märg) on uus hüpotees. Tehniliselt on see odav: samad bootstrap-kordused ja
  sama W annavad erinevuse jaotuse koos kovariatsiooniga. Ülesanne seda ei nõua; v3-s seda ei tehta (K3).
* **η² (mudelipõhisuse märk)** arvutatakse ökosüsteemi kaupa (`diagnostika.parquet`, `eco_code`). Rühmad kasutavad metsa
  (eco 3) väärtusi. See on konservatiivne lihtsustus ja seda tuleb märkida.
* **Segumudel** (930 m ja 1 km kihid) on ainult ökosüsteemi tasemel. Rühmadele seda ei hinnata (nagu alamökosüsteemile).
  ‡-kihtidel näidatakse 10 m hinnangut koos märgiga.
* **Tundlikkusanalüüs** (`analysis.sensitivity`) jääb v2 tasemetele. Rühmadele tehakse sama tundlikkusanalüüs (K5).
* **Klassifikatsiooni kriteerium.** Jaotus on alamökosüsteemi (kasvukohatüübi) järgi, mitte praeguse veerežiimi järgi.
  Kõdusoomets on kuivendatud turvasmullal mets, aga on märja metsa hulgas. Laane- ja loometsad on „kuivad“ ainult selles
  mõttes, et nad on mineraalmullal ja ei ole liigniisked. Tõlgendus „turvas- ja liigniisked kasvukohad vs mineraalmuld“ on
  täpsem kui „kuiv vs märg“. Koosseis on kinnitatud (K1); kriteerium kirjutatakse metoodikasse.
* **Kooskõla tulemustabeliga.** Rühma seisundi täpne mediaan statistilises analüüsis peab võrduma `kaasnev_suured`
  mediaaniga (31/32 × hea/keskmine/vilets). Mõlemad arvutatakse samast sagedustabelist samade klassikoodide ühendina.
  See on v3 valideerimise kontroll V-R4.

**Andmevajadus.** Rühma paaritatud hinnangut ei saa repo failidest tuletada. Selleks on vaja stratumi kaale ja mediaane
(`plokid/<kiht>__blkmed.parquet`) ning paaritamata hinnangu jaoks sagedustabelit (`plokid/<kiht>__val/`). Neid failid ei ole
git'is. Taastamine `oks aggregate` + `oks fields` võtab README järgi ~2–3 h ja laeb alla ~25 GB. Tuletada saab ainult
jaotusi (`jaotused.parquet` alamökosüsteemide loenduste summana) ja pikslikeskmisi (`lahtrid.parquet`: Σn·mean / Σn).

### 1.2 Paaritatud vaade tulemustabelis: põhiprobleem

Tulemustabel esitab **seisundi taset** (üks väärtus tüübi × seisundi kohta). Paaritatud hinnang on **seisundipaari
omadus**: hinnatakse stratumite erinevust ja stratumi kaal sõltub mõlemast seisundist. Seepärast ei ole „paaritatud
seisundi tase“ ühiku ja seisundi kohta üheselt määratud. Andmetes on see näha nii:

* Halvema seisundi paaritatud tase M_a = Σw·m_a/Σw on sama seisundi jaoks eri paarides erinev. Viletsa seisundi tase paaris
  vilets → keskmine ja paaris vilets → hea erineb mediaanis 8 %, 75. protsentiilis 19 % ja 90. protsentiilis 39 % (789
  kihi × ühiku kombinatsiooni, M_a ≠ 0).
* M_a erineb sama seisundi paaritamata pikslimediaanist mediaanis 14 %, 75. protsentiilis 33 % ja 90. protsentiilis 120 %.

Paaritatud vaates ei saa seega säilitada tabeli praegust kuju (rida = tüüp × seisund). Loomulik rida on **ühik × seisundipaar**.

### 1.3 Alternatiivide võrdlus

Tähistused: m_s = stratumi täpne mediaan seisundis s, w = n_a·n_b/(n_a+n_b), M_s = Σw·m_s/Σw üle paari (a, b) stratumite,
Δ = M_b − M_a (= `delta_m_med`), Δ % = Δ/|M_a| (= `rel_m_med`).

#### A. Plokimediaanide kaalutud keskmine (M_a ja M_b paari kaupa)

* **Statistiline korrektsus.** Kooskõlaline hinnang hästi määratletud suurusele: seisundi tüüpiline väärtus kohtades, kus
  mõlemad seisundid esinevad, kaalutuna täpsusega. M_b − M_a = Δ täpselt, seega on see sidus paaritatud Δ-ga. Tasemena on sellel
  kolm puudust.
  1. Kaal w on erinevuse täpsuse kaal (harmooniline pikslite arv). See ei ole pindalakaal, seega M_s ei esinda tüübi
     kogupindala.
  2. Valim on piiratud alaga, kus seisundid esinevad koos (väline kehtivus).
  3. M_s on mediaanide keskmine, mitte ühegi jaotuse mediaan. Nullirohketel kihtidel on paljud plokimediaanid 0 ja M_s
     sõltub tugevalt nende osast.

  Tasemete ebakindlust praegu ei arvutata. Bootstrap võimaldaks seda.
* **Tõlgendatavus.** Keskmine. „Tüüpiline väärtus samades kohtades“ on mõistetav, kuid tingimuslik ja paarist sõltuv.
* **Arusaadavus lõppkasutajale.** Madal. Sama seisundi väärtus on eri paarides erinev ja erineb kõrval olevast mediaanitabelist
  (mediaanis 14 %, mõnel juhul üle kahe korra). Kasutaja peab seda veaks.
* **Riskid.** Kasutaja arvutab ise M_hea(k→h) − M_vilets(v→k), mis ei ole ükski hinnang. Kasutaja korrutab M_s pindalaga.
  M_s satub lähtekasu tabelisse „keskväärtuse“ asemel. A sobib **lisainfoks** (kohtspikker: Δ alus ja kontekst), mitte
  põhiväärtuseks.

#### B. Senine paaritamata mediaan (seisundi täpne pikslimediaan)

* **Statistiline korrektsus.** Täpne ja robustne kirjeldav statistik kogu tüübi või ökosüsteemi pindala kohta (iga piksel üks
  vaatlus). Vastab lähtekasu nõudele „keskväärtus kogu klassi pindala kohta, nullid kaasa arvatud“. Tasemena on see õige.
  Paaritatud hinnang see **ei ole**. Veergude vahe on paaritamata Δ, mida segab asukoht. Suure ökosüsteemi ja rühma tasemel
  segab seda ka alamökosüsteemide koosseis (§ 1.1).
* **Tõlgendatavus.** Kõrge: „pooled pikslid on väiksemad, pooled suuremad“.
* **Arusaadavus lõppkasutajale.** Kõrgeim.
* **Riskid.** Kui seda nimetada paaritatud vaateks, on silt vale. Kasutaja loeb veergude vahet seisundi mõjuna. B peab jääma
  **tasemevaateks** praegusel kujul. Paaritatud vaate näitaja see ei ole.

#### C. Paaritatud hinnangu suhteline väärtus (Δ %, nagu statistilise analüüsi lehel)

* **Statistiline korrektsus.** Lugeja ja nimetaja tulevad samadest stratumitest sama kaaluga, seega paaritamata valim
  hinnangusse ei segune (`docs/metoodika.md` § 5). Olulisus on sama mis Δ-l: kui M_a > 0, on Δ % märk sama mis Δ märk. Piirangud:
  * Kui M_a ≈ 0, Δ %-i ei ole. See puudutab **631 / 3 434 (18 %)** hinnatavat paaritatud rida.
  * Kui M_a on väike, on Δ % ebastabiilne. |Δ %| > 500 % on 649 real (19 %). Olulistest hinnangutest (1 175) on selliseid
    ainult 6 ja ilma Δ %-ita 0, seega probleem puudutab peamiselt mitteolulisi hinnanguid.
  * Skaala on asümmeetriline (+100 % vs −50 %).
  * Δ % usaldusvahemikku ei arvutata: CI on Δ-l ja nimetaja ebakindlust ei arvestata.
  * Järjestus- ja indeksskaalal (`data_type = Järjestus`) ning negatiivsete väärtustega kihil (`pohlad_saagikus_2020_10m`)
    ei ole suhtel loomulikku nullpunkti.
* **Tõlgendatavus.** Kõrge, kui M_a on selgelt üle nulli. Ühikuvaba, seega kihid on võrreldavad. See on kuumkaardil
  oluline eelis.
* **Arusaadavus lõppkasutajale.** Kõrge („+25 %“). Lähtekasu ja stsenaariumi jaoks on vaja väärtust kihi ühikus. Tulemustabelis
  on iga veerg üks kiht, seega ühikuvabadus ei anna seal eelist.
* **Riskid.** Tühjad ja äärmuslikud lahtrid nullirohketel kihtidel. Kasutaja arvutab Δ % × keskmine. Oluline väike absoluutne
  muutus jätab suure mulje. C sobib **teiseseks näitajaks** (lüliti või kohtspikker), mitte põhiväärtuseks.

#### D. Paaritatud muutus kihi ühikus (Δ = `delta_m_med`) koos 95 % CI ja olulisusega (soovitatav)

* **Statistiline korrektsus.** See on v2 põhihinnang: sama suurus, mille järgi kuumkaart värvib olulisust. Usaldusvahemik
  (`ci_m_med_lo/hi`), p, FDR q ja piisavuse lipp (`enough_m`) on juba arvutatud, uut järeldusstatistikat ei ole vaja. Δ on
  defineeritud ka siis, kui M_a = 0. Õige silt: „plokimediaanide erinevuste kaalutud keskmine samas 1 km plokis ja
  alamökosüsteemis“, lühidalt „tüüpiline muutus samas kohas“.
* **Tõlgendatavus.** Kõrge. Väärtus on kihi ühikus (kg/ha, EUR/ha, indeks) ja võrreldav tasemevaate väärtustega samas veerus.
* **Arusaadavus lõppkasutajale.** Hea, kui vaate pealkiri ütleb selgelt „muutus“, mitte „väärtus“, ja märgid (+/−) ning olulisus on
  nähtavad.
* **Riskid.**
  * Mediaanide vahe korda pindala ei ole koguhulga muutus. Stsenaariumi koguhulk jääb keskmiste vahe põhiseks
    (`metoodika_v2_otsused.md`).
  * Kihid ei ole omavahel võrreldavad, kuid tabelis on iga veerg eraldi kiht.
  * Nullirohketel kihtidel on Δ sageli täpselt 0 (927 / 3 434 hinnatavast reast, 27 %). See on õige tulemus („tüüpilises
    kohas teenust ei ole kummaski seisundis“), aga vajab selgitust.

#### E. Muud kaalutud lahendused (mitte põhinäitajaks)

* **Stratumierinevuste mediaan** (`median_d_m_med`) ja **positiivsete stratumite osa** (`share_pos_m_med`) on robustne ja
  kommunikatiivne täiendus („64 % kohtadest oli heas seisundis suurem väärtus“). Puudused: kaaluta, ilma CI-ta, ja `share_pos`
  loeb võrdsed (d = 0, nullirohked kihid) mittepositiivseks. Ilma negatiivsete osata (`share_neg`) on see kallutatud. Sobib
  kohtspikrisse koos `share_neg`-iga (vajab uut veergu).
* **Kolmikpaaritatud tasemed** (stratumid, kus esinevad kõik kolm seisundit, ühine kaal) annaksid sidusa kolme veeruga tasemetabeli.
  See on aga uus hinnatav suurus: Δ ei võrduks kuumkaardi Δ-ga, stratumeid on vähem ja kaalu valik on uus metoodiline otsus.
  Ei soovita (v2-ga ei ole jälgitav).
* **Δ, kus alus on paaritamata mediaan ja muutus paaritatud** („B + D“). Segab kaht hinnatavat suurust (paaritamata taset ja
  paaritatud erinevust). **Keelatud**, ka kohtspikris.

#### Kokkuvõte

| Kriteerium | A: M_a, M_b | B: paaritamata mediaan | C: Δ % | **D: Δ ühikus + CI** |
|---|---|---|---|---|
| Kas on paaritatud hinnang | jah (tasemed, paari kaupa) | ei | jah | **jah (v2 põhihinnang)** |
| Üheselt määratud tabeli lahtris | ei (sõltub paarist) | jah | jah | **jah (ühik × paar)** |
| Määratud, kui M_a = 0 | jah | jah | ei (18 % ridadest) | **jah** |
| Ebakindlus olemas | ei (vajab bootstrapi) | ei (kirjeldav) | ei (ainult Δ-l) | **jah (CI, q)** |
| Kihi ühikus (lähtekas) | jah | jah | ei | **jah** |
| Segiajamise risk | kõrge | kõrge (kui nimetada paaritatuks) | keskmine | **madal (kui sildistatud „muutus“)** |
| Soovitatav roll | kohtspikker | tasemevaade (praegune) | lüliti / kohtspikker | **paaritatud vaate põhiväärtus** |

---

## 2. Soovituslik lahendus

**v3.** Statistilisse analüüsi tuleb kolmas ühikutase `ruhm`: 31 Kuivad metsad, 32 Märjad metsad, `eco_code = 3`. Rühmi
arvutatakse **täpselt v2 hinnangutega**: samad funktsioonid `stats.analyse_layer` ja `stats.analyse_layer_median`, sama W ja
samad parameetrid. Rühma definitsioon on ühes kohas ja seda kasutavad nii `kaasnev` kui ka `stats`. Mitmese testimise
parandus (FDR, § 3 K2) tehakse rühmadele eraldi. Kõik tasemed arvutatakse **ühe käsuga** `oks analyse` samadesse
tulemusfailidesse. v2 tulemused on alles git'is commit'is `de7aca9` ja v3 jooks kontrollib, et ökosüsteemi ja
alamökosüsteemi read on nendega identsed (§ 4.4). Veebis on rühmad ökosüsteemi tasemel kohe metsa järel kõigis vaadetes,
mis kasutavad statistilise analüüsi ühikuid, ning tõendusbaasis (kvalitatiivne jaotis, stsenaarium). Paaritamata
rühmahinnangul on toorhinnangu hoiatus.

**v4.** Tulemustabelisse tuleb näitaja lüliti **„Tase (mediaan)“ | „Muutus (paaritatud)“**. Tasemevaade jääb muutmata (B).
Paaritatud vaates on rida ühik × seisundipaar ja lahtri põhiväärtus on **D: paaritatud Δ kihi ühikus**. Olulisus on
kujunduses nähtav; CI, q, Δ % ja paaritatud tasemed M_a → M_b (A) on kohtspikris. Δ % on valikuline lüliti (C). Paaritatud
vaade ei toida stsenaariumi koguhulka. M_a ja M_b arvutatakse juba v3 jooksus (K9) ega tuletata Δ/Δ %-ist, sest siis jääks
M_a määramata kõigil ridadel, kus Δ = 0 (27 %).

**Põhjendus.** D on ainus näitaja, mis

1. on täpselt v2 paaritatud põhihinnang;
2. on igas lahtris üheselt määratud ja defineeritud ka siis, kui M_a = 0;
3. on juba olemas koos ebakindluse ja FDR-iga;
4. on kihi ühikus nagu tulemustabeli teised väärtused.

A ja C jäävad kontekstiks, sest A on paarist sõltuv tase ja C ei ole nullirohketel kihtidel määratud.

---

## 3. Otsused (2026-11-01)

| # | Küsimus | Otsus |
|---|---|---|
| K1 | Rühmade koosseis | **Kinnitatud:** kuivad = salumets, palumets, laanemets, loomets, nõmmemets; märjad = soovikumets, samblasoomets, rohusoomets, kõdusoomets, rabastuv mets. „Muu (metsa)kooslus“ ei kuulu kumbagi rühma (ainult kogu metsa). Sama mis `kaasnev.FOREST_SPLIT`. |
| K2 | Mitmese testimise parandus (FDR) | **Eraldi rühm „ruhm“.** Selgitus allpool. |
| K3 | Kuiva ja märja metsa erinevuse test | Mitte v3-s (võimalik hiljem). |
| K4 | Rühmade kuvamine kuumkaardil | Ökosüsteemi vaates vaikimisi nähtaval, metsa järel; lüliti „Kuivad ja märjad metsad“. |
| K5 | Tundlikkusanalüüs rühmadele | Jah. Tuleb automaatselt, kui `oks analyse --sensitivity` käivitatakse (§ 4.4). |
| K6 | Kas plokitabelid on alles? | **Ei ole.** Kontrollitud 2026-11-01: `data/derived` sisaldab ainult klassitabeleid, `plokid`, `__val`, `__blkmed` ja `__hist` puuduvad. Need taastatakse käskudega `oks aggregate` ja `oks fields` (~2–3 h). Arhiiv on kättesaadav (HTTP 200, baaskaardi failide muutmisaeg sama mis inventuuris, 2026-06-30). Konteineris on 4 protsessorit, 15 GB mälu ja ~30 GB vaba kettaruumi. |
| K7 | Avaldamine | v3 aadressil `/v3/` (`noindex`); v3 lehel link v2-le; peaaadress ei muutu. |
| K8 | v4 detailid | vilets → hea vaikimisi; Δ % lülitina; „ei paku“ eelistatud; Excelisse eraldi leht. |
| K9 | M_a, M_b v3 jooksus | **Jah.** |
| K10 | Versiooniveerg CSV-s | Ei. Versioon on näha lehe päises (§ 4.5). |
| K11 | Git-sildid | Valikuline; ei ole vajalik, sest versioonid on kindlad commit'id. |
| K12 | η² rühmadele | Metsa (eco 3) väärtus koos märkusega. |
| K13 | Stsenaariumi koguhulk | Väljaspool v3/v4 ulatust. |

**K2 selgitus: mis on FDR.** Analüüs teeb tuhandeid olulisuse teste (34 kihti × ühikud × 3 seisundipaari). Kui iga testi
lävi on 5 %, tuleb puhtalt juhuslikult „olulisi“ tulemusi sadu. Benjamini–Hochbergi parandus (FDR, *false discovery rate*)
teisendab iga p-väärtuse q-väärtuseks. Kui märgime oluliseks kõik tulemused, mille q < 0,05, on nende hulgas eeldatavalt
kuni 5 % juhuslikke. Parandus sõltub sellest, milliseid teste koos parandatakse. v2-s on kaks eraldi gruppi: ökosüsteemi
tase (408 testi) ja alamökosüsteemi tase (3 772 testi). Kuivad ja märjad metsad lisavad kuni 204 testi.

* **Eraldi grupp (valitud):** v2 ökosüsteemi ja alamökosüsteemi q-väärtused ning „oluline“ märked jäävad täpselt samaks.
* Ökosüsteemi grupiga koos: kõik v2 ökosüsteemi q-väärtused muutuksid veidi ja mõni piiripealne „oluline“ märge võiks muutuda.

Mõlemad on statistiliselt lubatud. Eraldi grupp hoiab v2 tulemused muutumatuna ja on lihtsam selgitada.

---

## 4. Tehniline disain

### 4.1 Põhimõtted

1. **Iga versioon on üks kindel commit.** v1 = `5aa4596`, v2 = `de7aca9`, v3 = tulevane commit. Kood ja tulemusfailid
   (`data/tulemused`) on git'is koos. Seega on iga versioon täielikult taastatav ja tema veebileht ehitatakse alati
   iseendast.
2. **Üks analüüsijooks.** Kõik tasemed (ökosüsteem, alamökosüsteem, metsarühm) arvutatakse sama käsuga `oks analyse` ja
   samast sisendist. See on teaduslikult kõige selgem: üks jooks, üks bootstrap-kaalude maatriks, üks parameetrifail.
   Arvutuslikult on see ka kõige tõhusam, sest iga kihi sisend loetakse üks kord.
3. **v2 hinnangud ei muutu.** Uus tase on lisandus. v2 statistilisi funktsioone ei muudeta, ainult laiendatakse
   (uued veerud M_a, M_b, Σw). Jooksu lõpus kontrollib võrdlusskript, et kõigi ökosüsteemi ja alamökosüsteemi ridade
   kõik v2 veerud on identsed v2 failidega (§ 4.4).
4. **Üks definitsioon.** Rühmade koosseis on ühes moodulis ja seda kasutavad `kaasnev` ning `stats`/`analysis`.

### 4.2 v3 andmevoog

```
arhiiv ──► oks aggregate / oks fields (muutmata, v2 kood) ──► data/derived/plokid/<kiht>{.parquet,__val/,__blkmed,__hist}
                                                                      │
oks analyse (üks jooks, kiht korraga):                                ▼
   1. v2 ühikud (ökosüsteem, alam):  stats.analyse_layer + analyse_layer_median          (nagu v2)
   2. rühmaühikud (31, 32):          samad funktsioonid, ühikud = ruhmad.make_group_units(used),
                                     plokimediaanid plokk × rühm × seisund = ruhmad.block_medians(__val)
   3. read liidetakse, unit_level ∈ {okosusteem, alam, ruhm}; FDR iga taseme kaupa
                                                                      ▼
data/tulemused/{paarid,lahtrid,algklassid,jaotused,uhikud,klassid,diagnostika}.parquet   (v3; sisaldavad ka ruhm-ridu)
                                                                      ▼
scripts/vordle_v2.py: ökosüsteemi ja alam-read vs git show de7aca9:data/tulemused/*   →  peab olema 0 erinevust
                                                                      ▼
export / kaasnev_export → site/data/*.json, tulemused_paarid.csv  →  sait /v3/
```

**Miks v2 funktsioonid sobivad muutmata kujul.** `analyse_layer*` käsitleb ökosüsteemi kui klasside rühma (`cls_eco`), mille
stratumid tulevad alamökosüsteemidest (`cls_alam`, `alam_eco`). Kui ühikute objektis on `eco_codes = (31, 32)`, `cls_eco`
kaardistab kuiva metsa alamökosüsteemide klassid 0-le, märja metsa omad 1-le ja ülejäänud −1-le, ning `alam_codes` on kümme
rühma alamökosüsteemi, annavad samad funktsioonid ökosüsteemi ridade asemel rühma read. Ainus puuduv sisend on plokimediaan
plokk × rühm × seisund: `__blkmed` sisaldab ainult rühmitusi `eco` ja `alam`. Selle saab täpselt arvutada sagedustabelist
`__val` (kaalutud mediaan, sama poolitusreegel mis `aggregate.segment_medians`).

### 4.3 v3 muutuvad failid ja komponendid

| Fail | Muudatus |
|---|---|
| `src/oks/ruhmad.py` (uus) | `GROUPS` (kood, nimi, `eco = 3`, alamkoodid; K1); `make_group_units(used) -> stats.Units`; `block_medians(val_dir, used) -> pl.DataFrame` (veerud nagu `__blkmed`, `grouping = "eco"`, `group = kood·10 + uld`) |
| `src/oks/kaasnev.py` | `DRY_FOREST`, `WET_FOREST`, `FOREST_SPLIT` võetakse `ruhmad`-ist (nimed jäävad alles); tulemused identsed |
| `src/oks/stats.py` | `analyse_layer_median` tagastab lisaks veerud `level_a_m_med`, `level_b_m_med`, `sum_w_m_med` (K9; seni arvutati M_a sisemiselt ja visati ära). Muud read ja veerud ei muutu |
| `src/oks/analysis.py` | `run`: iga kihi kohta teine kutse rühmaühikutega, read tasemega `ruhm`; `unit_table`, `distributions` ja `add_fdr` saavad taseme `ruhm` |
| `src/oks/export.py` | rühmad `meta.uhikud` lõppu (v2 ühikute järjekord ei muutu); `unit_level` kaardistus `{okosusteem: 0, alam: 1, ruhm: 2}`; CSV read `tase = "ruhm"`; `meta.metoodika = "v3"` |
| `src/oks/kaasnev_export.py` | `evidence` sisaldab rühmade ridu |
| `src/oks/report.py` | `docs/tulemused.md` uus jaotis „Kuivad ja märjad metsad“ |
| `site_src/app.js` | kuumkaart: rühmad ökosüsteemi vaates metsa järel, lüliti, päise märge (↳); kohtspikker: rühma koosseis, eraldi FDR-grupp, η² = metsa väärtus; ühikute valikutes märk `▸`; paaritamata hoiatus ka rühmadel; päises versioonimärk „Metoodika v3“ |
| `site_src/sections/scenario.js`, `quality.js` | eco 31/32 paaritatud tõendus tasemelt `ruhm`; kvalitatiivse tabeli veerud `[3, 31, 32, 2, 1, 4]` |
| `scripts/vordle_v2.py` (uus) | v3 ökosüsteemi ja alam-read vs v2 failid commit'ist `de7aca9` |
| `scripts/valideeri_ruhmad.py` (uus) | V-R2…V-R6 (§ 4.7) |
| `scripts/valideeri_veeb.py` | V11, V12 (§ 4.7) |
| `.github/workflows/pages.yml` | samm „Ehita v3 leht HEAD-ist aadressile `/v3/`“ (§ 4.5) |
| `docs/metoodika_v3_otsused.md` (uus), `docs/metoodika.md` (§ 5.5), `README.md` | otsused, hinnatav suurus, piirangud, versioonid |
| `data/tulemused/*` | uuesti arvutatud: v2 read identsed, lisandunud `ruhm` read ja veerud M_a, M_b, Σw |

Muutmata jäävad `median.py`, `aggregate.py`, `pipeline.py`, `fields.py`, `catalog.py`, `andmetabel.py` (Excel) ja
`vordlus.py`. Samuti jäävad muutmata `kaasnev_*.parquet` failid, sest kuivad ja märjad metsad on tulemustabelis juba olemas
ja `oks kaasnev` käsku ei käivitata. Ka v1 → v2 võrdluse failid (`vordlus_*.csv`) jäävad samaks.

### 4.4 v3 arvutused ja v2 kontroll

* **Paaritatud Δ_g** (§ 1.1), CI, p, `n_strata`, `n_clusters_m`, `enough_m`: v2 loogikaga, ühikuks rühm.
* **Paaritamata:** rühma × seisundi täpne pikslimediaan klasside ühendist; täpne klastribootstrap, sama W.
* **Lahtrid, algklassid, jaotused:** nagu ökosüsteemi tasemel.
* **FDR:** Benjamini–Hochberg eraldi tasemel `ruhm` (K2).
* **M_a, M_b, Σw (K9):** kõigil tasemetel; peab kehtima `level_b − level_a = delta_m_med`.
* **Tundlikkus (K5):** `oks analyse --sensitivity` kordab kõiki tasemeid, sh rühmi.
* **v2 kontroll:** `scripts/vordle_v2.py` loeb v2 failid käsuga `git show de7aca9:data/tulemused/<fail>` ja võrdleb v3
  failidega kõiki v2 veerge ökosüsteemi ja alamökosüsteemi ridadel (`paarid`, `lahtrid`, `klassid`, `algklassid`,
  `jaotused`, `diagnostika`, `uhikud`, `tundlikkus.csv`). Nõue: 0 erinevust (ujukomaarvudel abs. tolerants 1e-12).
  * See kontrollib ka seda, et kogu ahel on **reprodutseeritav**: plokitabelid taastatakse arhiivist nullist ja v2 tulemus peab
    tulema täpselt sama.
  * Kui tulemus erineb (nt arhiivi faile on vahepeal muudetud), töö peatatakse, erinevused raporteeritakse ja v3 tulemusi ei
    salvestata enne otsust.
* **Arvutuskulu:** aggregate + fields ~2–3 h (README). v2 analüüs võttis 67 min; rühmad lisavad hinnanguliselt 20–40 min.
  Tundlikkus võttis 60 min, rühmadega veidi rohkem. Rühmade aeg on hinnang, mitte mõõtmine; piloot mõõdab selle.

### 4.5 Versioonid ja tagasiminek v2-le

**Põhimõte:** iga versioon on üks commit vaikeharus (liidetakse „Squash and merge“ valikuga) ja iga avaldatud leht ehitatakse
oma kindlast commit'ist.

| Aadress | Ehitatakse | Seis |
|---|---|---|
| `/` | commit `5aa4596` (v1) | nagu praegu |
| `/v2/` | commit `de7aca9` (v2) | **tehtud** (harus `claude/confident-sagan-iituxn`, jõustub liitmisel) |
| `/v3/` | vaikeharu viimane commit | lisatakse v3 commit'iga |

* **v2 on v3-st sõltumatu.** Varem ehitati `/v2/` vaikeharu viimasest commit'ist, nii et iga uus muudatus oleks sinna jõudnud.
  Nüüd ehitatakse see alati commit'ist `de7aca9` ja vaikeharu muudatused seda lehte ei mõjuta. Kontrollitud kohaliku
  kuivjooksuga 2026-11-01: v1, v2 ja kontrollehitus õnnestusid; `/v2/` andmefailid (`paarid`, `lahtrid`, `kaasnev`,
  `tendus.json`) ja `app.js` on identsed seni avaldatud v2-ga.
* **Tagasiminek v2-le:** üks käsk `git revert <v3 commit>` ja push.
  * Vaikeharu kood ja tulemusfailid on siis täpselt v2 omad, sest tulemusfailid on git'is.
  * `/v3/` kaob järgmise Pages-ehitusega, sest selle ehitamise samm on v3 commit'i osa.
  * `/v2/` ja `/` ei muutu kordagi.
* **Versioonimärk:** v3 lehe päises on tekst „Metoodika v3“ ja metoodika jaotises link v2 lehele. v1 ja v2 lehti ei muudeta.
* **Peaaadressi vahetus** (hilisem otsus): töövoos muudetakse ühe sammu commit'i.

### 4.6 v4 disain (ainult spetsifikatsioon)

**Kasutajaliides (`site_src/sections/results.js`):**

* Uus segmentnupp „Näitaja“: **Tase (mediaan)** (vaikimisi, praegune vaade) | **Muutus (paaritatud)**.
* Paaritatud vaates:
  * Rida „Tüübid“ tähendab taset `alam` (39 alamökosüsteemi, millel on ≥ 2 seisundit). Rida „Suured ökosüsteemid“ tähendab
    tasemeid `okosusteem` 1–4 ja `ruhm` 31/32.
  * Rannikul ning asustusel ja muul paaritatud hinnangut ei ole. Selle kohta on märkus.
  * Filter „Seisund“ asendub filtriga „Seisundipaar“ (kiibid, vaikimisi vilets → hea, mitu korraga lubatud: rida = ühik × paar).
* **Lahter:** Δ kihi ühikus koos märgiga.
  * Oluline (q < 0,05): täisvärv suuna skaalal (oranž–sinine, `docs/disain.md`). Värv tähendab väärtuse suunda, mitte hüve
    suunda.
  * Mitteoluline: kahvatu tekst.
  * `enough_m = false`: „–“ ja kohtspikker „andmeid ei piisa (alla 20 paari või 5 klastri)“.
  * Hinnang puudub: tühi.
  * Mõlemas seisundis tasemevaate staatus „ei paku“: tekst „ei paku“.
* **Lüliti „Δ | Δ %“**. Δ % ei kuvata, kui M_a = 0 („alus 0“). Üle ±500 % märgitakse „ebastabiilne alus“.
* **Kohtspikker:**
  * Δ ja 95 % CI, p, q;
  * Δ % ja selle alus M_a;
  * paaritatud tasemed M_a → M_b („plokimediaanide kaalutud keskmine samades paarides“);
  * paaritamata mediaanid („kogu klassi mediaanid, vt tasemevaade“);
  * paaride ja klastrite arv;
  * †/‡/§ ja η² hoiatus.
* **Pealkiri:** „Paaritatud muutus: tüüpiline muutus samas 1 km plokis ja alamökosüsteemis“ ning hoiatus, et mediaanide
  muutust ei tohi korrutada pindalaga.
* **CSV (praegune vaade):** ühik, paar, kiht, Δ, CI, q, oluline, Δ %, M_a, M_b, paare, klastreid.
* **Excel:** uus leht „Paaritatud muutus“ (pikk tabel); olemasolevad lehed ei muutu.

**Andmed:** `paarid.json` saab veerud `level_a_m_med`, `level_b_m_med` (v3 jooksust). Uut analüüsijooksu v4 ei vaja.
Brauseris statistilisi arvutusi ei tehta.

**Mida v4 ei muuda:** tasemevaadet, `kaasnev.json`, stsenaariumi arvutust, kuumkaarti ega tulemusfaile.
**Versioon:** v4 on omaette commit; `/v3/` kinnitatakse siis v3 commit'ile ja `/v4/` ehitatakse vaikeharust (sama muster).

### 4.7 Testid

**Ühiktestid (sünteetilised, `tests/test_ruhmad.py`):**

| Test | Mida kontrollib |
|---|---|
| `test_group_definition_single_source` | `kaasnev.FOREST_SPLIT` ≡ `ruhmad.GROUPS`; rühmad ei kattu; Muu (31100, 31200) ei kuulu rühma |
| `test_group_of_one_alam_equals_alam` | rühm ühest alamökosüsteemist → paaritatud ja paaritamata read = alam-read |
| `test_group_of_all_alams_equals_eco` | rühm = kõik ökosüsteemi alamökosüsteemid → read = ökosüsteemi read |
| `test_forest_decomposition` | Δ_mets = Σ W_g·Δ_g / Σ W_g (rühmad + Muu), W = `sum_w_m_med` |
| `test_group_block_medians_exact` | `ruhmad.block_medians` sagedustabelist = `numpy.median` toorpikslitel |
| `test_fdr_groups_separate` | `ruhm` read ei muuda ökosüsteemi ja alam-tasemete q-väärtusi |
| `test_levels_consistent` | `level_b − level_a = delta_m_med`; `rel_m_med = delta_m_med / |level_a|` |
| `test_new_columns_do_not_change_old` | `analyse_layer_median` vanad veerud on enne ja pärast laiendust identsed |
| `test_group_cells_match_big_classes` | rühma seisundi mediaan = `kaasnev.median_table` 31/32 mediaan |
| `test_distribution_group_is_sum_of_alams` | rühma jaotus = alamökosüsteemide jaotuste summa |
| `test_export_units_appended` | `meta.uhikud`: v2 ühikud samadel kohtadel, rühmad lõpus |
| `test_kaasnev_unchanged_after_refactor` | `kaasnev.big_classes` väljund identne |

**Andmekontroll täisandmetel:**

* V-R1 `scripts/vordle_v2.py`: v2 read identsed (§ 4.4).
* `scripts/valideeri_ruhmad.py`:
  * V-R2: Δ_mets pesastatus;
  * V-R3: `n_strata` mets = kuiv + märg + Muu;
  * V-R4: rühma mediaanid = `kaasnev_suured`;
  * V-R5: rühma jaotus = alamökosüsteemide summa;
  * V-R6: `level_b − level_a = delta_m_med`.

Kõigil on nõue 0 erinevust.

**Veebikontroll** (`valideeri_veeb.py`):

* V11: kuumkaardi rühmalahtrid = `paarid.parquet`;
* V12: stsenaariumi tõendus 31/32 kohta;
* pärast v4: V13 (paaritatud vaate lahtrid) ja V14 (paaritatud vaate CSV).

---

## 5. Mõju olemasolevale süsteemile

| Osa | v3 | v4 |
|---|---|---|
| v2 hinnangud ja olulisusmärked | samad (kontroll V-R1) | samad |
| v2 veebileht `/v2/` | ei muutu (ehitatakse `de7aca9`-st) | ei muutu |
| Tulemustabel (tasemevaade), Excel | ei muutu | lisandub lüliti ja Exceli leht |
| Kuumkaart ja teised statistilise analüüsi vaated | lisanduvad kuivad ja märjad metsad | — |
| Kvalitatiivne jaotis, stsenaarium | rühmade paaritatud tõendus täidab praeguse tühimiku | — |
| `tulemused_paarid.csv` | lisanduvad read `tase = ruhm` | — |
| `docs/tulemused.md` | lisandub jaotis | — |
| Arvutus | plokitabelite taastamine (~2–3 h) ja täisanalüüs | uut jooksu ei vaja |

---

## 6. Riskid

| Risk | Tõenäosus / mõju | Leevendus |
|---|---|---|
| Arhiivist taastatud plokitabelid ei reprodutseeri v2 tulemust | madal / kõrge | V-R1; erinevuse korral peatus ja otsus enne salvestamist |
| Konteiner taaskäivitub pika jooksu ajal | keskmine / madal | aggregate jätkab valmis kihtidest, analüüsil on kihtide vahemälu |
| Kettaruum (~30 GB) ei piisa | madal / keskmine | aggregate kustutab toorfailid; jälgida jooksu ajal |
| Kasutaja keskmistab kuiva ja märja metsa või loeb metsa hinnangut pindalakaalutud keskmisena | keskmine / keskmine | kohtspikker ja metoodika: täpsuskaal, Muu osa, pesastatus |
| Paaritamata rühmahinnangut loetakse seisundi mõjuna (koosseis) | kõrge / keskmine | hoiatus, paaritatud vaikimisi |
| v4: paaritatud Δ korrutatakse pindalaga või aetakse segi tasemetega | keskmine / kõrge | eraldi vaade, „muutus“ pealkirjas, hoiatus, ei toida stsenaariumi |
| v4: Δ % tühjad ja äärmuslikud lahtrid | kõrge (18 % / 19 % ridadest) / madal | Δ vaikimisi, Δ % lülitina koos märgistusega |
| Rühmade arvutusaja hinnang on vale | keskmine / madal | piloot ühe kihiga |

---

## 7. Claude Code'i muudatuste plaan

Iga samm on eraldi commit ja märgitakse tehtuks alles pärast kontrolli. V4 sammud on ainult spetsifikatsioon.

| # | Samm | Valmis, kui | Kontroll |
|---|---|---|---|
| V3-1 | `pages.yml`: `/v2/` commit'ist `de7aca9` | **tehtud** | kohalik kuivjooks, `/v2/` = senine v2 |
| V3-2 | `docs/metoodika_v3_otsused.md` (§ 3) | kirjas | — |
| V3-3 | `ruhmad.py`; `kaasnev` võtab definitsiooni sealt | testid § 4.7 (definitsioon, plokimediaanid, kaasnev) | pytest, ruff, mypy |
| V3-4 | `stats.analyse_layer_median` lisaveerud; `analysis.run` rühmatase, FDR, jaotused, ühikute tabel | kõik § 4.7 ühiktestid | pytest, ruff, mypy |
| V3-5 | `scripts/vordle_v2.py`, `scripts/valideeri_ruhmad.py` | skriptid töötavad v2 failidel | — |
| V3-6 | Plokitabelite taastamine: `oks aggregate`, `oks fields` | kõik 35 kihti valmis (`pipeline.done()`) | logi |
| V3-7 | Piloot: `oks analyse` kahe kihiga (üks nullirohke, üks pidev) | aeg mõõdetud, V-R1…V-R6 0 erinevust | skriptid |
| V3-8 | Täisjooks `oks analyse --sensitivity` | 34 kihti; V-R1…V-R6 0 erinevust | skriptid |
| V3-9 | `export.py`, `kaasnev_export.py` | rühmad JSON-is, CSV-s, tõendusbaasis | pytest |
| V3-10 | Sait (`app.js`, `scenario.js`, `quality.js`); `pages.yml` `/v3/` | JS-vigu 0, telefonilaius, hele/tume teema | `valideeri_veeb.py` V8–V12 |
| V3-11 | `report.py`, `docs/metoodika.md`, README | dokumendid vastavad koodile | läbivaatus |
| V3-12 | Lõpparuanne `docs/metoodika_v3_lopparuanne.md` | kõik testid, kontrollid, CI rohelised | `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src` |
| V4-1 | (spetsifikatsioon) `results.js` paaritatud vaade § 4.6 | tasemevaade muutumatu | V13, V14 |
| V4-2 | (spetsifikatsioon) `export.py`: M_a, M_b `paarid.json`-i | v4 testid | pytest |
| V4-3 | (spetsifikatsioon) Exceli leht „Paaritatud muutus“ | olemasolevad lehed identsed | V10 |
| V4-4 | (spetsifikatsioon) `pages.yml`: `/v3/` kinnitatakse commit'ile, `/v4/` vaikeharust | — | — |

**Käsud (V3-6…V3-8):**

```bash
uv run python -m oks aggregate
uv run python -m oks fields
uv run python -m oks analyse --sensitivity
uv run python scripts/vordle_v2.py
uv run python scripts/valideeri_ruhmad.py
uv run python -m oks report && uv run python -m oks site --out site
```
