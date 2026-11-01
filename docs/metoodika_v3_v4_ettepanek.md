# Metoodika v3 ja v4: analüüs ja tehniline ettepanek

**Seis:** ettepanek, ülevaatamiseks. Koodi, tulemusfaile ega saiti ei ole muudetud.
**Võrdlusalus:** metoodika v2, commit `de7aca9` (vaikeharu HEAD 2026-11-01). Metoodika v1 on commit `5aa4596`.
**Arvud:** kõik selle dokumendi arvud on arvutatud repo failidest `data/tulemused/paarid.parquet` ja `uhikud.parquet`
(v2 täisjooks, 34 kihti, 4 180 paari). Uued failide, funktsioonide ja veergude nimed on **ettepanekud**, mitte olemasolev kood.

| Versioon | Sisu | Staatus |
|---|---|---|
| v1 | keskmised, NoData välja | commit `5aa4596`, sait peaaadressil |
| v2 | täpsed pikslimediaanid, NoData = 0, paaritatud mediaanipõhine Δ | commit `de7aca9`, sait `/v2/` |
| v3 | kuivad ja märjad metsad statistilise analüüsi ühikuna (kuumkaart jt vaated) | selle dokumendi spetsifikatsioon (§ 4.2–4.4) |
| v4 | tulemustabeli paaritatud vaade | ainult spetsifikatsioon (§ 4.5) |

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
  sama W annavad erinevuse jaotuse koos kovariatsiooniga. Ülesanne seda ei nõua, seepärast on see lahtine küsimus (K3).
* **η² (mudelipõhisuse märk)** arvutatakse ökosüsteemi kaupa (`diagnostika.parquet`, `eco_code`). Rühmad kasutavad metsa
  (eco 3) väärtusi. See on konservatiivne lihtsustus ja seda tuleb märkida.
* **Segumudel** (930 m ja 1 km kihid) on ainult ökosüsteemi tasemel. Rühmadele seda ei hinnata (nagu alamökosüsteemile).
  ‡-kihtidel näidatakse 10 m hinnangut koos märgiga.
* **Tundlikkusanalüüs** (`analysis.sensitivity`) jääb v2 tasemetele. Rühmade tundlikkus on lahtine küsimus (K5).
* **Klassifikatsiooni kriteerium.** Jaotus on alamökosüsteemi (kasvukohatüübi) järgi, mitte praeguse veerežiimi järgi.
  Kõdusoomets on kuivendatud turvasmullal mets, aga on märja metsa hulgas. Laane- ja loometsad on „kuivad“ ainult selles
  mõttes, et nad on mineraalmullal ja ei ole liigniisked. Tõlgendus „turvas- ja liigniisked kasvukohad vs mineraalmuld“ on
  täpsem kui „kuiv vs märg“. Nimetus ja kriteerium tuleb kinnitada (K1). Kood ei sõltu nimest.
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

**v3.** Lisada statistilisse analüüsi kolmas ühikutase `ruhm` (koodid 31 Kuivad metsad, 32 Märjad metsad, `eco_code = 3`).
Seda arvutatakse **täpselt v2 hinnangutega**: samad funktsioonid `stats.analyse_layer` ja `stats.analyse_layer_median`,
sama W ja samad parameetrid. Rühma definitsioon tuleb ühest allikast, mida jagavad `kaasnev` ja `stats`. FDR-perekond on eraldi
(`ruhm`). Tulemused kirjutatakse **eraldi failidesse** (`*_ruhmad.parquet`), et v2 failid jääksid bitti-bitti samaks. Veebis
on rühmad ökosüsteemi tasemel kohe metsa järel kõigis vaadetes, mis kasutavad statistilise analüüsi ühikuid, ning tõendusbaasis
(kvalitatiivne, stsenaarium). Paaritamata rühmahinnangul on toorhinnangu hoiatus.

**v4.** Tulemustabelisse tuleb näitaja lüliti **„Tase (mediaan)“ | „Muutus (paaritatud)“**. Tasemevaade jääb muutmata (B).
Paaritatud vaates on rida ühik × seisundipaar ja lahtri põhiväärtus on **D: paaritatud Δ kihi ühikus**. Olulisus on kujunduses
nähtav, CI, q, Δ % ja paaritatud tasemed M_a → M_b (A) on kohtspikris. Δ % on valikuline lüliti (C). Paaritatud vaade ei toida
stsenaariumi koguhulka. M_a ja M_b kirjutatakse analüüsist otse lisafaili. Neid ei tuletata Δ/Δ %-ist, sest siis jääks M_a
määramata kõigil ridadel, kus Δ = 0 (27 %).

**Põhjendus.** D on ainus näitaja, mis

1. on täpselt v2 paaritatud põhihinnang;
2. on igas lahtris üheselt määratud ja defineeritud ka siis, kui M_a = 0;
3. on juba olemas koos ebakindluse ja FDR-iga;
4. on kihi ühikus nagu tulemustabeli teised väärtused.

A ja C jäävad kontekstiks, sest A on paarist sõltuv tase ja C ei ole nullirohketel kihtidel määratud.

---

## 3. Lahtised küsimused

Iga küsimuse juures on vaikimisi ettepanek, mida plaan (§ 7) eeldab, kui teisiti ei otsustata.

| # | Küsimus | Vaikimisi ettepanek |
|---|---|---|
| K1 | Kas kriteerium „alamökosüsteem (kasvukohatüüp)“ ja nimetused „kuivad/märjad metsad“ on õiged? Kas kõdusoomets (kuivendatud turvasmuld) kuulub märgade hulka? Kas „Muu (metsa)kooslus“ jääb rühmadest välja? | Jaotus nagu `kaasnev.FOREST_SPLIT` (lähtekasu kommentaar), Muu välja; kriteerium kirjas metoodikas |
| K2 | FDR: eraldi perekond `ruhm` või ökosüsteemi perekonnas? | Eraldi (v2 q muutumatud) |
| K3 | Kas lisada kuiva ja märja metsa erinevuse test (Δ_kuiv − Δ_märg, sama bootstrap)? | Mitte v3-s; võimalik v3.1 |
| K4 | Kas kuumkaardil on rühmad vaikimisi nähtaval ja kas need peaks olema ka alamökosüsteemi vaates (rühmitus/värv)? | Ökosüsteemi vaates vaikimisi sees, lüliti „Kuivad ja märjad metsad“; alamökosüsteemi vaates ainult rühma märk päises |
| K5 | Kas rühmadele teha tundlikkusanalüüs? | Jah, samad 5 varianti (+~1 h arvutust); võib jätta v3.1-sse |
| K6 | Kus ja millal arvutatakse? Kas v2 täisjooksu `data/derived/plokid` (`__val`, `__blkmed`, `__hist`) on alles? | Kui ei ole, siis `oks aggregate` + `oks fields` (~2–3 h, ~25 GB arhiivist) |
| K7 | Avaldamine: kas v3 tuleb aadressile `/v3/` (`noindex`, ainult otselink) ja kas v3 lehel võib olla link v2-le? Millal vahetatakse peaaadressi sisu? | `/v3/`, `noindex`, link v2-le metoodika jaotises; peaaadress ei muutu |
| K8 | v4: vaikimisi seisundipaar; kas Δ % lüliti; kas näidata „ei paku“, kui mõlemas seisundis on staatus „ei paku“; kas paaritatud vaade läheb ka Excelisse? | vilets → hea; Δ % lülitina; „ei paku“ eelistatud; Excelisse eraldi leht |
| K9 | Kas paaritatud tasemed M_a, M_b (ja Σw) arvutada juba v3 jooksu ajal lisafaili, et v4 ei vajaks teist jooksu? Kas tasemetele on vaja bootstrap-CI-d? | Jah, M_a, M_b, Σw lisafaili; CI-d mitte |
| K10 | Kas allalaaditavatesse CSV-desse lisada veerg `metoodika_versioon`? | Jah, viimase veeruna (v3 sait); v2 CSV muutumatu |
| K11 | Kas kasutaja loob git-sildid `metoodika-v1` (`5aa4596`) ja `metoodika-v2` (`de7aca9`)? Varem ei olnud siltide loomine sessioonis lubatud. | Jah, käsitsi |
| K12 | η² rühmadele: metsa (eco 3) väärtus või rühmapõhine η²? | Metsa väärtus koos märkusega |
| K13 | Stsenaariumi koguhulk: kas tulevikus kasutada paaritatud **keskmiste** vahet (`delta_m`) praeguse paaritamata keskmiste vahe asemel? | Väljaspool v3/v4 ulatust; eraldi otsus |

---

## 4. Tehniline disain

### 4.1 Põhimõtted

1. **Täiendav, mitte muutev.** v2 koodirajad (`stats.analyse_layer`, `stats.analyse_layer_median`, `kaasnev.*`,
   `analysis.run`) jäävad muutmata. v3 kutsub neid välja uue ühikute objektiga ja kirjutab tulemused uutesse failidesse.
2. **v2 andmed on külmutatud.** `data/tulemused` v2 failid (sh `paarid.parquet`, `lahtrid.parquet`, `uhikud.parquet`,
   `jaotused.parquet`, `algklassid.parquet`, `kaasnev_*.parquet`, `parameetrid.csv`, `tundlikkus.csv`) jäävad bitti-bitti
   samaks. Seda kontrollib SHA-256 manifest ja test (§ 4.7).
3. **Üks allikas.** Rühmade definitsioon on ühes moodulis ja seda kasutavad nii `kaasnev` kui ka `stats`/`analysis`.
4. **Versioon on nähtav.** Iga sait ja andmekomplekt teab oma metoodika versiooni.

### 4.2 v3 andmevoog

```
data/derived/plokid/<kiht>.parquet ─┐
<kiht>__blkmed.parquet (alam-read) ─┤
<kiht>__val/  ──► ruhmad.block_medians (plokk × rühm × seisund) ─┤
<kiht>__hist.parquet ───────────────┤
                                    ▼
          analysis.run_groups(): ruhmad.make_group_units(used)  →  Units(eco = rühmad, alam = rühma alamid)
               stats.analyse_layer(...)          (muutmata, sama W)
               stats.analyse_layer_median(...)   (muutmata, sama W)
               → read tasemel "okosusteem" ümber nimetatud tasemeks "ruhm" (31/32)
               → read tasemel "alam" = kontroll: peavad võrduma v2 alam-ridadega
               add_fdr(perekond "ruhm")
                                    ▼
data/tulemused/{paarid,lahtrid,algklassid,jaotused,uhikud}_ruhmad.parquet   (UUED; v2 failid puutumata)
data/tulemused/paarid_tasemed.parquet  (M_a, M_b, Σw kõigil tasemetel; v4 jaoks, K9)
                                    ▼
export.build_data / kaasnev_export.evidence (loevad *_ruhmad olemasolul) → site/data/*.json, tulemused_paarid.csv
```

**Miks v2 funktsioonid töötavad muutmata.** `analyse_layer*` käsitlevad ökosüsteemi kui klasside rühma (`cls_eco`), mille
stratumid tulevad alamökosüsteemidest (`cls_alam`, `alam_eco`). Kui `Units.eco_codes = (31, 32)`, `cls_eco` kaardistab kuiva
metsa alamökosüsteemide klassid 0-le, märja metsa omad 1-le ja ülejäänud −1-le, ning `alam_codes` on kümme rühma alamökosüsteemi,
annavad funktsioonid ökosüsteemi ridade asemel rühma read. Ainus puuduv sisend on plokimediaan plokk × rühm × seisund
(`__blkmed` sisaldab ainult rühmitusi `eco` ja `alam`). Selle saab täpselt arvutada sagedustabelist `__val` (kaalutud
mediaan, sama poolitusreegel mis `aggregate.segment_medians`). Rastreid uuesti lugeda ei ole vaja.

### 4.3 v3 muutuvad failid ja komponendid

| Fail | Muudatus | Mõju v2-le |
|---|---|---|
| `src/oks/ruhmad.py` (uus) | `GROUPS: dict[int, Group]` (kood, nimi, `eco = 3`, alamkoodid); `make_group_units(used) -> stats.Units`; `block_medians(val_dir, used) -> pl.DataFrame` (veerud nagu `__blkmed`: `grouping="eco"`, `group = kood·10 + uld`) | puudub |
| `src/oks/kaasnev.py` | `DRY_FOREST`, `WET_FOREST`, `FOREST_SPLIT` imporditakse `ruhmad`-ist (nimed jäävad samaks, aliasena) | tulemused identsed (test) |
| `src/oks/analysis.py` | uus `run_groups(params, out_dir, cache_dir)`; `add_fdr` saab parameetri `levels` (vaikimisi `("okosusteem", "alam")` nagu praegu); `distributions` saab valikulise rühmade kaardistuse; `_layer_cache` võtmesse lisatakse `config.METHOD_VERSION` | `run()` käitumine muutmata |
| `src/oks/__main__.py` | uus käsk `oks analyse-groups` (ei kirjuta v2 faile) | puudub |
| `src/oks/config.py` | `METHOD_VERSION = "v3"` | puudub |
| `src/oks/export.py` | loeb `*_ruhmad.parquet` olemasolul ja lisab rühmad `meta.uhikud` lõppu (v2 ühikute indeksid ei muutu); `unit_level` kaardistus `{okosusteem: 0, alam: 1, ruhm: 2}`; CSV read `tase = "ruhm"`; `meta.metoodika = METHOD_VERSION` | v2 ridade väärtused samad |
| `src/oks/kaasnev_export.py` | `evidence` liidab rühmade read (`tase = "ruhm"`) | v2 read samad |
| `src/oks/report.py` | `docs/tulemused.md` uus jaotis „Kuivad ja märjad metsad“ | genereeritud dokument muutub (ainult lisandub) |
| `site_src/app.js` | `visUnits`: ökosüsteemi tasemel rühmad metsa järel (järjekord `kaasnev.DISPLAY_ORDER`); lüliti „Kuivad ja märjad metsad“; päise märge (↳, eraldusjoon); kohtspikker: rühma definitsioon, FDR-perekond, η² = metsa väärtus; ühikute valikutes märk `▸`; paaritamata hoiatus ka rühmal; „Tase“ info tekst | v2 sait ehitatakse eraldi commit'ist |
| `site_src/sections/scenario.js`, `quality.js` | tõendus eco 31/32 korral tasemelt `ruhm`; kvalitatiivse tabeli veerud `[3, 31, 32, 2, 1, 4]` | — |
| `scripts/valideeri_ruhmad.py` (uus) | V-R1…V-R6 (§ 4.8) täisandmetel | — |
| `scripts/valideeri_veeb.py` | V11: kuumkaardi rühmalahtrid vs `paarid_ruhmad.parquet` | — |
| `.github/workflows/pages.yml` | `/v2/` ehitatakse kinnitatud commit'ist `V2_COMMIT=de7aca9`, `/v3/` HEAD-ist; kontrollid kõigile kolmele | v1 ja v2 lehed sisuliselt samad |
| `docs/metoodika_v3_otsused.md` (uus), `docs/metoodika.md` (uus § 5.5), `README.md` | otsused, hinnatav suurus, piirangud, versioonitabel | — |
| `data/tulemused/MANIFEST_v2.sha256` (uus) | v2 failide räsid | — |

`stats.py`, `median.py`, `aggregate.py`, `pipeline.py`, `fields.py`, `catalog.py`, `andmetabel.py`, `vordlus.py` ja
`sitebuild.py` ei muutu. Excel ei muutu, sest seal ei ole paaritatud hinnanguid ja suurte ökosüsteemide lehel on 31/32 juba olemas.

### 4.4 v3 arvutused

* **Paaritatud Δ_g** (§ 1.1), CI, p, `n_strata`, `n_clusters_m`, `enough_m`: muutmata `analyse_layer*` loogikaga, ühikuks rühm.
* **Paaritamata:** rühma × seisundi täpne pikslimediaan klasside ühendist ja täpne klastribootstrap
  (`median.cluster_boot_medians_seg`), sama W.
* **Lahtrid:** n, keskmine, SD, mediaan, mediaan > 0, plokimediaanide kvantiilid (plokk × rühm).
* **Algklassid:** mediaan algse seisundiklassi kaupa rühma sees.
* **Jaotused:** klasside histogrammid rühma tasemele. Peab võrduma rühma alamökosüsteemide summaga.
* **FDR:** BH perekonnas `ruhm`, kõigi kuue p-veeru jaoks eraldi nagu v2 (`analysis._FDR`).
* **v4 ettevalmistus (K9):** `paarid_tasemed.parquet` = (`layer_id`, `unit_level`, `unit_code`, `pair`, `level_a_m_med`,
  `level_b_m_med`, `sum_w_m_med`) kõigil tasemetel. Arvutatakse ainult `__blkmed`-ist, ilma bootstrapita. Peab kehtima
  `level_b − level_a = delta_m_med` (tolerants 1e-9 suhteliselt).
* **Arvutuskulu:** v2 põhijooks võttis 67 min (34 kihti). Rühmade läbikäik arvutab kaks rühma ja kordab rühma alamökosüsteemide
  paaritamata bootstrapi (kontrolliks). Hinnanguliselt 20–40 min. See on eeldus, mida pole mõõdetud.

### 4.5 v4 disain (ainult spetsifikatsioon)

**Kasutajaliides (`site_src/sections/results.js`):**

* Uus segmentnupp „Näitaja“: **Tase (mediaan)** (vaikimisi, praegune vaade) | **Muutus (paaritatud)**.
* Paaritatud vaates:
  * Rida „Tüübid“ tähendab tase `alam` (39 alamökosüsteemi, millel on ≥ 2 seisundit). Rida „Suured ökosüsteemid“ tähendab
    tasemeid `okosusteem` 1–4 ja `ruhm` 31/32 (vajab v3 andmeid).
  * Rannikul ning asustusel ja muul paaritatud hinnangut ei ole. Selle kohta on märkus.
  * Filter „Seisund“ asendub filtriga „Seisundipaar“ (kiibid, vaikimisi vilets → hea, mitu korraga lubatud: rida = ühik × paar).
    Seisundid määramata ja hindamata ei kehti.
* **Lahter:** Δ kihi ühikus koos märgiga.
  * Oluline (q < 0,05): täisvärv suuna skaalal (oranž–sinine, `docs/disain.md`). Värv tähendab väärtuse suunda, mitte hüve
    suunda.
  * Mitteoluline: kahvatu tekst.
  * `enough_m = false`: „–“ ja kohtspikker „andmeid ei piisa (alla 20 paari või 5 klastri)“.
  * Hinnang puudub: tühi.
  * Kui mõlemas seisundis on tasemevaate staatus „ei paku“: tekst „ei paku“ (K8).
* **Lüliti „Δ | Δ %“**. Δ % ei kuvata, kui M_a = 0 („alus 0“). Väärtus esitatakse kärpimata, kuid üle ±500 % märgitakse
  „ebastabiilne alus“.
* **Kohtspikker:**
  * Δ ja 95 % CI, p, q;
  * Δ % ja selle alus M_a;
  * paaritatud tasemed M_a → M_b („plokimediaanide kaalutud keskmine samades paarides“);
  * paaritamata mediaanid („kogu klassi mediaanid, vt tasemevaade“);
  * paaride ja klastrite arv;
  * †/‡/§, η² hoiatus. Ühiku ja rühma tasemel ka FDR-perekond.
* **Pealkiri ja alapealkiri:** „Paaritatud muutus: tüüpiline muutus samas 1 km plokis ja alamökosüsteemis“ ning hoiatus, et
  mediaanide muutust ei tohi korrutada pindalaga.
* **CSV (praegune vaade):** ühik, paar, kiht, Δ, CI, q, oluline, Δ %, M_a, M_b, paare, klastreid, `metoodika_versioon`.
* **Excel (K8):** uus leht „Paaritatud muutus“ (pikk tabel). Olemasolevad lehed jäävad muutmata.

**Andmed:** `paarid.json` saab veerud `level_a_m_med`, `level_b_m_med` (failist `paarid_tasemed.parquet`). Tulemustabeli read
seotakse ühikutega `meta.uhikud` kaudu (`tase`, `kood` ↔ `alam_kood` / `okosusteem_kood` / 31, 32). Uusi statistilisi
arvutusi brauseris ei tehta.

**Mida v4 ei muuda:** tasemevaadet, `kaasnev.json`, stsenaariumi arvutust, kuumkaarti ega ühtegi `data/tulemused` v2/v3 faili.

### 4.6 Versioonide vahetamine

* **Koodis:** `config.METHOD_VERSION` (`"v3"`, hiljem `"v4"`). Väärtus kirjutatakse `meta.json`-i (`metoodika`) ja
  CSV veergu (K10). Saidi päises ja jaotises „Meetod“ on versioonimärk. v1 ja v2 lehed jäävad muutmata, seega märki neil ei ole.
* **Andmetes:** v2 failid on külmutatud (manifest). v3 lisab ainult uusi faile. Sait kasutab v3 faile ainult siis, kui need on
  olemas. v2 commit'ist ehitatud sait neid ei loe.
* **Avaldamisel (`pages.yml`):** iga versioon ehitatakse oma commit'ist eraldi git-worktree'st, nagu v1-ga juba praegu.

  | Aadress | Allikas | Märge |
  |---|---|---|
  | `/` | `V1_COMMIT=5aa4596` | muutmata, kuni peaaadressi vahetus otsustatakse |
  | `/v2/` | `V2_COMMIT=de7aca9` (**uus kinnitus**; praegu ehitatakse HEAD-ist) | `noindex` |
  | `/v3/` | HEAD (vaikeharu) | `noindex` |
  | `/v4/` | ainult pärast v4 rakendamist | — |

  **Tähtis:** `/v2/` tuleb kinnitada commit'ile **enne** v3 liitmist. Muidu ehitaks töövoog v3 koodi aadressile `/v2/`.
* **Peaaadressi vahetus** (hilisem otsus): `/` ehitatakse soovitud versiooni commit'ist ja eelmine viiakse oma alamaadressile.
  See on üks muudatus töövoos.
* **Tagasipööramine:** v3 on üks squash-commit. `git revert <v3>` taastab v2 koodi. v2 andmefailid on niikuinii muutmata ja
  `/v2/` ehitatakse kinnitatud commit'ist, seega v3 tagasivõtmine ei mõjuta v2 lehte.

### 4.7 Olemasolevate tulemuste kaitse

1. **v2 koodirada muutmata.** Kontroll: `git diff de7aca9 -- src/oks/stats.py src/oks/median.py src/oks/aggregate.py`
   on tühi. `analysis.run` muudetakse ainult lisaparameetrite kaudu, mille vaikeväärtus säilitab käitumise.
2. **Manifest.** `data/tulemused/MANIFEST_v2.sha256` (`sha256sum` v2 failidest commit'is `de7aca9`). Test
   `tests/test_v2_frozen.py` võrdleb. CI ebaõnnestub, kui mõni v2 fail muutub.
3. **`oks analyse` ei käivitata v3 töös.** Rühmad arvutab ainult `oks analyse-groups`, mis kirjutab ainult `*_ruhmad` ja
   `paarid_tasemed` failid. Käsu dokumentatsioonis on see hoiatus.
4. **Sisemine kontroll.** Rühmade läbikäigu alam-read peavad võrduma v2 `paarid.parquet` / `lahtrid.parquet` vastavate
   ridadega (abs. tolerants 1e-12; BLAS-i järjekord võib viimast bitti muuta).
5. **Saidi võrdlus.** v3 `paarid.json` / `lahtrid.json` read v2 ühikute kohta võrduvad v2 saidi failidega (skript,
   v2 ühikute indeksid ei muutu).
6. **Vahemälu.** `_layer_cache` võtmesse lisatakse `METHOD_VERSION`. Enne jooksu kustutatakse `data/cache/analyys`.

### 4.8 Testid

**Ühiktestid (sünteetilised, `tests/test_ruhmad.py`):**

| Test | Mida kontrollib |
|---|---|
| `test_group_definition_single_source` | `kaasnev.FOREST_SPLIT` ≡ `ruhmad.GROUPS`; rühmad ei kattu; Muu (31100, 31200) ei kuulu rühma |
| `test_group_of_one_alam_equals_alam` | rühm ühest alamökosüsteemist: paaritatud ja paaritamata read = alam-read (täpne võrdus) |
| `test_group_of_all_alams_equals_eco` | rühm = kõik ökosüsteemi alamökosüsteemid (≥ 2 seisundit) → read = ökosüsteemi read |
| `test_forest_decomposition` | Δ_mets = Σ W_g·Δ_g / Σ W_g (rühmad + Muu), W = `sum_w_m_med` |
| `test_group_block_medians_exact` | `ruhmad.block_medians` sagedustabelist = `aggregate.segment_medians` laiendatud pikslitel = `numpy.median` |
| `test_fdr_family_separate` | `add_fdr` koos `ruhm` ridadega: `okosusteem` ja `alam` q-väärtused identsed ilma nendeta arvutatutega |
| `test_bootstrap_reproducible` | sama seeme ja W → identne CI/p |
| `test_group_cells_match_big_classes` | rühma seisundi mediaan = `kaasnev.median_table` 31/32 mediaan sama sagedustabeli peal |
| `test_distribution_group_is_sum_of_alams` | rühma jaotus = alamökosüsteemide jaotuste summa |
| `test_v2_frozen` | v2 andmefailide SHA-256 = manifest |
| `test_export_units_appended` | `meta.uhikud`: v2 ühikud samadel indeksitel, rühmad lõpus (`tase = "ruhm"`, `eco = 3`); `unit_level` kood 2 |
| `test_kaasnev_unchanged_after_refactor` | `kaasnev.big_classes` / `_big_groups` väljund enne ja pärast importi `ruhmad`-ist identne |

**Andmekontroll täisandmetel (`scripts/valideeri_ruhmad.py`):**

* V-R1: alam-read vs v2 (punkt 4.7.4).
* V-R2: pesastatus Δ_mets.
* V-R3: `n_strata`: mets = kuiv + märg + Muu.
* V-R4: rühma mediaanid vs `kaasnev_suured`.
* V-R5: rühma jaotus vs alamökosüsteemide summa.
* V-R6: `level_b − level_a = delta_m_med`.

Eesmärk on kõigil 0 lahknevust.

**Veebikontroll:** `valideeri_veeb.py` V11 (kuumkaardi rühmalahtrid ja kohtspikrid) ja V12 (stsenaariumi paaritatud tõendus
31/32 kohta). Pärast v4 rakendamist lisanduvad V13 (paaritatud vaate lahtrid = `paarid.json`) ja V14 (paaritatud vaate CSV).

**v4 testid (spetsifikatsioon):**

* `level_b − level_a = delta_m_med`;
* `rel_m_med = delta_m_med / |level_a|` (kui `level_a ≠ 0`);
* paaritatud vaates on read ainult ühikutel, millel on hinnang;
* seisundifilter ei mõjuta paaritatud vaadet;
* tasemevaate HTML on enne ja pärast v4 identne (snapshot).

---

## 5. Mõju olemasolevale süsteemile

| Osa | v3 | v4 |
|---|---|---|
| v2 hinnangud (`paarid`, `lahtrid` jt) | muutumatud (manifest) | muutumatud |
| v2 q-väärtused ja olulisus | muutumatud (eraldi perekond) | muutumatud |
| Tulemustabel, tasemevaade | muutumatu | muutumatu (uus lüliti, vaikimisi tase) |
| Excel | muutumatu | lisandub leht (K8) |
| Kuumkaart ja teised statistilise analüüsi vaated | lisanduvad 2 veergu/ühikut | — |
| Kvalitatiivne, stsenaarium | rühmade tõendus täidab praeguse tühimiku | — |
| `tulemused_paarid.csv` | lisanduvad read `tase = ruhm` (+ versiooniveerg, K10) | — |
| v1→v2 võrdlus (`vordlus.*`) | muutumatu (rühmadel puudub v1 vaste) | muutumatu |
| `docs/tulemused.md` | lisandub jaotis | — |
| Sait v1 (`/`) ja v2 (`/v2/`) | muutumatud; `/v2/` kinnitatakse commit'ile | muutumatud |
| Arvutuskeskkond | vajab `data/derived/plokid` (K6) | ainult kui M_a/M_b ei arvutatud v3-s |
| Välised tarbijad, kes loevad `tulemused_paarid.csv` ilma `tase` filtrita | näevad uusi ridu | — |

---

## 6. Riskid

| Risk | Tõenäosus / mõju | Leevendus |
|---|---|---|
| `/v2/` hakkab näitama v3 koodi (töövoog ehitab HEAD-ist) | kõrge, kui ei tehta / kõrge | `V2_COMMIT` kinnitus esimese sammuna, enne v3 liitmist |
| v2 tulemusfailid kirjutatakse üle (`oks analyse` käivitatakse kogemata) | keskmine / kõrge | eraldi käsk, manifest-test CI-s, hoiatus README-s |
| Plokitabelid puuduvad, taastamine ebaõnnestub (arhiiv, ketas) | keskmine / keskmine | K6; jooks jätkatav (vahemälu); kontroll `pipeline.done()` |
| Kasutaja keskmistab kuiva ja märja metsa või loeb metsa hinnangut pindalakaalutud keskmisena | keskmine / keskmine | kohtspikker ja metoodika: täpsuskaal, Muu osa, pesastatus |
| Paaritamata rühmahinnangut loetakse seisundi mõjuna (koosseis!) | kõrge / keskmine | hoiatus nagu ökosüsteemi tasemel, paaritatud vaikimisi |
| Kahe FDR-perekonna q-väärtused ühes vaates | madal / madal | märgend kohtspikris ja metoodikas |
| „Kuiv/märg“ nimetus eksitab (kõdusoomets) | keskmine / madal | K1; definitsioon igal pool kohtspikris |
| v4: paaritatud Δ-d korrutatakse pindalaga või aetakse segi tasemetega | keskmine / kõrge | eraldi vaade, „muutus“ pealkirjas, hoiatus, ei toida stsenaariumi |
| v4: Δ % tühjad ja äärmuslikud lahtrid | kõrge (18 % / 19 % ridadest) / madal | Δ vaikimisi, Δ % lülitina koos märgistusega |
| v4: M_a tuletatakse Δ/Δ %-ist | — / keskmine (27 % ridadel määramata) | M_a, M_b otse analüüsist (K9) |
| BLAS-i järjekord muudab alam-kontrollis viimast bitti | madal / madal | kontroll tolerantsiga 1e-12; v2 failid on niikuinii muutmata |
| Arvutusaja hinnang (20–40 min) on vale | keskmine / madal | mõõta piloodil ühe kihiga (`--only`) |

---

## 7. Claude Code'i muudatuste plaan

Töö haru: määrab kasutaja (nt `claude/metoodika-v3`). Iga samm on eraldi commit ja märgitakse tehtuks alles pärast kontrolli.
v4 sammud (V4-*) on ainult spetsifikatsioon ja neid ei rakendata enne eraldi otsust.

| # | Samm | Valmis, kui | Kontroll |
|---|---|---|---|
| V3-0 | Otsused K1–K13 kirja: `docs/metoodika_v3_otsused.md` | kasutaja kinnitas | — |
| V3-1 | `pages.yml`: `/v2/` commit'ist `V2_COMMIT=de7aca9`, HEAD → `/v3/`, kontrollid kolmele saidile | töövoog roheline, `/v2/` sisu = `de7aca9` ehitus | kohalik kuiv jooks (worktree) |
| V3-2 | `MANIFEST_v2.sha256` ja `tests/test_v2_frozen.py` | test roheline `de7aca9` andmetel | `uv run pytest -q` |
| V3-3 | `src/oks/ruhmad.py` (`GROUPS`, `make_group_units`, `block_medians`); `kaasnev` impordib definitsiooni sealt | `test_group_definition_single_source`, `test_kaasnev_unchanged_after_refactor`, `test_group_block_medians_exact` | pytest, ruff, mypy |
| V3-4 | `analysis.run_groups`, `add_fdr(levels=…)`, `distributions` rühmadega, `_layer_cache` + versioon, käsk `oks analyse-groups`, `config.METHOD_VERSION` | ühiktestid § 4.8 rohelised sünteetilistel andmetel | pytest, ruff, mypy; `git diff de7aca9 -- src/oks/stats.py` tühi |
| V3-5 | `paarid_tasemed.parquet` (K9) | `level_b − level_a = delta_m_med` testis | pytest |
| V3-6 | Piloot: `oks analyse-groups --only <1 nullirohke + 1 pidev kiht>` | aeg mõõdetud, V-R1…V-R6 0 lahknevust | `scripts/valideeri_ruhmad.py` |
| V3-7 | Täisjooks (vajab K6 andmeid) | 34 kihti, `*_ruhmad.parquet` olemas; manifest-test roheline | V-R1…V-R6, `test_v2_frozen` |
| V3-8 | `export.py`, `kaasnev_export.py`: rühmad JSON-is, CSV-s ja tõendusbaasis | `test_export_units_appended`; v2 ühikute JSON-read = v2 sait | pytest, võrdlusskript |
| V3-9 | Sait: `app.js` (kuumkaart, valikud, kohtspikrid, hoiatused, versioonimärk), `scenario.js`, `quality.js` | brauseris JS-vigu 0, telefonilaius ilma horisontaalse kerimiseta, hele/tume teema | `valideeri_veeb.py` V8–V12 |
| V3-10 | `report.py` (tulemused.md jaotis), `docs/metoodika.md` § 5.5, README versioonitabel | dokumendid vastavad koodile | käsitsi läbivaatus |
| V3-11 | Lõppkontroll ja aruanne `docs/metoodika_v3_lopparuanne.md` (muudetud failid, mõjutabel, kontrollnimekiri, tagasipööramine) | kõik testid, kontrollskriptid, CI ja Pages rohelised | `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy src` |
| V4-1 | (spetsifikatsioon) `results.js`: lüliti „Näitaja“, paaritatud vaade § 4.5 | tasemevaate snapshot muutumatu | V13, V14 |
| V4-2 | (spetsifikatsioon) `export.py`: `level_a_m_med`, `level_b_m_med` `paarid.json`-i | v4 testid § 4.8 | pytest |
| V4-3 | (spetsifikatsioon) Excel leht „Paaritatud muutus“ (K8) | olemasolevad lehed identsed | `valideeri_veeb.py` V10 |
| V4-4 | (spetsifikatsioon) `pages.yml`: `/v4/`; `METHOD_VERSION = "v4"` | — | — |

**Käsud (V3-7):**

```bash
rm -rf data/cache/analyys
uv run python -m oks analyse-groups          # ainult *_ruhmad.parquet ja paarid_tasemed.parquet
uv run python scripts/valideeri_ruhmad.py
uv run pytest -q tests/test_v2_frozen.py
uv run python -m oks report && uv run python -m oks site --out site
```
