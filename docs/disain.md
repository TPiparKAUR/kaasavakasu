# Veebilehe disainiprintsiibid

Lehe eesmärk on, et ekspert saaks mõne sekundiga vastuse küsimusele „kuidas ja kui palju
muutub teenus, kui seisund läheb vilets → keskmine → hea, ja kas see on usaldusväärne“.
Alljärgnevad printsiibid kehtivad kõigile vaadetele (`site_src/`); iga printsiibi all on
kirjas, kuidas seda rakendatakse. Rõhk on selgusel, **mitte info vähendamisel**: kõik arvud
(keskmine, mediaan, usaldusvahemik, p/q, jaotus) on alles, kuid need on kihistatud.

## 1. Üks graafik – üks küsimus

* Iga kaart algab pealkirjaga, mis ütleb, mida graafik näitab, ja ühe lause alapealkirjaga,
  kuidas seda lugeda.
* Esmane sõnum (nt „mediaan kasvab 26 → 85 t C/ha“) on tekstina graafiku kohal; graafik tõestab,
  tabel annab täpsed arvud.
* Lehel on kolm sügavustaset: **ülevaade** (kuumkaart, kihtide ülevaade) → **detail** (üks teenus,
  üks üksus) → **tabel/CSV** (täpsed väärtused). Filtrid kehtivad kõigil tasemetel.

## 2. Värvil on kindel tähendus

| Tähendus | Värv | Reegel |
|---|---|---|
| Seisund: vilets / keskmine / hea | hallikas punane / hallikas kollane / hallikas roheline | kasutusel **ainult** seisundi tähistamiseks |
| Muutuse suund (kuumkaart) | oranž (väheneb) ↔ sinine (kasvab) | ei kasuta seisundivärve, et „punane“ ei tähendaks korraga „vilets“ ja „väheneb“ |
| Olulisus | täidetud vs. kahvatu/õõnes märk | ei sõltu värvist |
| Märgised, nupud | sinine aktsent | – |

* Seisundipalett on järjestatud (punane → kollane → roheline) ja **summutatud** (madal küllastus),
  et suured pinnad ei karju ja värvid eristuvad siiski. Joonte ja teksti jaoks on igal värvil
  tumedam „tindi“ variant (kontrast ≥ 3 : 1 graafikuelemendil, ≥ 4,5 : 1 tekstil; WCAG 2.2
  SC 1.4.11 ja 1.4.3).
* Punane–roheline ei tohi olla ainus eristaja (värvipimedus). Seepärast on lisaks
  * **lähedalasuv otsemärgistus** (seisundi nimi legendis ja arvukaartidel samas järjekorras),
  * **heleduse erinevus** (kollane on kõige heledam, punane ja roheline erinevad toonilt ja heleduselt),
  * **kuju** (punkt/ruut/romb legendis ja mini-graafikutes) ja
  * **järjekord** (alati vilets → keskmine → hea, vasakult paremale/ülalt alla).
* Hele ja tume teema on kumbki eraldi valitud (mitte pööratud); kasutaja süsteemiseade
  (`prefers-color-scheme`) on vaikimisi.

## 3. Ausad skaalad ja võrreldavus

* Tulpdiagrammi baas on alati 0. Joondiagrammil võib teljevahemik olla kitsam, kuid siis on
  nullist erinevust märgitud.
* **Osakaal (%), mitte arv.** Seisundite pindalad erinevad kordades; jaotusi võrreldakse igaüks
  oma 100 %-ga. Toorete pikslite arv (nt 10⁷, 10⁸) ei ole lugejale tähenduslik.
* Võrdlevatel graafikutel (kolm seisundit samal teljel) on sama x- ja y-skaala. Mini-graafikute
  ruudustikus on y-telg graafiku sees normeeritud, sest eesmärk on **kuju** võrdlus; selle kohta
  on märge, ja täpsed väärtused on hiirega/tabelis.
* Mitte-lineaarne telg (ruutjuur) on alati nimetatud graafiku all; telje sildid on
  „ümmargused“ arvud, mitte vahemike servad (nt mitte 79,1845).
* **Nullid eraldi.** Kui kihil on suur täpsete nullide osakaal (nt erosioon, marjasaak), tõmbab
  see ühe tulba kõrgeks ja kõik muu muutub nähtamatuks. Nullide osakaal on kirjas eraldi ja
  jaotust saab vaadata ilma nullideta (ülejäänud pikslid uuesti 100 %-ks normeeritud).
* Ei mingit teaduslikku arvuvormingut telgedel ega kaartidel; eesti numbrivorming
  (koma, hõre tühik tuhandete vahel); ühik on alati kirjas.

## 4. Näita jaotust, mitte ainult keskmist

* Keskmine peidab, kas muutus tuleb kogu jaotuse nihkest või väikesest tippude osast. Seetõttu
  näidatakse iga seisundi kohta **mediaan, keskmine ja 25–75 % vahemik** (vahemike täpsusega).
* Kolm vaadet samale jaotusele, sest igaüks vastab teisele küsimusele:
  *kattuvad kõverad* – kui palju seisundid kattuvad; *eraldi paneelid* – kuidas iga jaotuse
  kuju välja näeb; *kumulatiivne* – „mitu % pikslitest on ≤ x“, kus vertikaalne vahe on
  otse loetav ja vahemike valik ei mõjuta muljet.
* Kahe jaotuse erinevus on arvuna: kattuvus (Σ min) ja tõenäosus, et parema seisundi piksel
  on suurem. Need on kirjeldavad näitajad; olulisus on bootstrap-hinnangust.

## 5. Selgus enne kaunistust

* Vähe joont, palju ruumi: ainult horisontaalsed abijooned, ilma kastide ja varjudeta
  graafikus; täitevärv kerge (läbipaistvus), kontuur tugev.
* Otsemärgistus legendi asemel kus võimalik; legend siiski alati olemas (ligipääsetavus).
* Visuaalne hierarhia: pealkiri → põhiarv (suur) → graafik → märkused (väike, hall).
  Märkused on **lisainfo**, mitte peidetud selgitus: pikemad selgitused on „i“-nuppude taga
  või kokkuvolditavas osas.
* Üks vahetükk teksti pikkus ≤ 62 rem (loetav rida); mobiilis üks veerg, 16 px küljeruumi,
  horisontaalne kerimine ainult tabelis ja laiadel kuumkaartidel.

## 6. Interaktiivsus ja ligipääsetavus

* Iga graafik on kasutatav klaviatuuriga (fookus, Enter) ja omab `aria-label`it; hiire
  tööriistavihje (tooltip) kordab sama infot fookuse korral.
* Iga graafikuga kaasneb tabelivaade (sama info tekstina) või CSV.
* Filtrid: iga filtri juures „i“-nupp selgitusega; muutus kajastub kohe loendurina
  („97 sobivat hinnangut“).
* Ära kasuta ainult hõljumist (hover) – klõps/puudutus avab sama sisu.
* Heledas ja tumedas režiimis, `forced-colors` korral ja 320 px laiuses kontrollitud.

## 7. Ausus ja päritolu

* Iga arv on märgistatud päritolu järgi: **mõõdetud/modelleeritud kiht** (ELME), **tuletatud**
  (seisund baaskaardilt), **madalam lahutusvõime** (‡; 930 m / 1 km kiht viidud 10 m lahutusvõimele),
  **erandkiht** (§; puuduvad andmed välja jäetud), **definitsiooniline** (†). Segumudel on uuriv ja ainult võrdluseks.
* Ebakindlus on nähtav: usaldusvahemik, olulisus (q), hinnangute arv (paare/plokke).
* Hoiatused (mudelipõhisus, madalam lahutusvõime, vähe andmeid) on graafikuga samas kohas, mitte
  eraldi lehel.

## 8. Tehniline

* Ilma välisteekideta (üks HTML + JS + CSS), töötab `file://` kaudu (ühefailne väljund) ja
  GitHub Pages'is. Andmed on lehe sees või `data/*.json`.
* Värvid on CSS-muutujad (`:root`) – ühes kohas muudetavad; JS loeb need `getComputedStyle`
  kaudu, nii et teema vahetus uuendab ka SVG-d.

---

## Kolleegi graafiku analüüs (kihtide ülevaade)

Kolleeg koostas 26 histogrammi toorete pikslite arvuga (üks paneel kihi kohta). Lehel on selle
põhjal vaheleht **Kihtide ülevaade**. Mida graafik tegi hästi ja mida parandasime:

| Tähelepanek kolleegi graafikul | Mida see teeb lugejale | Lahendus lehel |
|---|---|---|
| Y-telg on toorarv koos astendajaga (`1e7`, `1e8`) | teljesildi pole kerge lugeda, paneelide vahel ei saa arve võrrelda; 930 m kihtidel on arv tuhandetes, 5–10 m kihtidel sadades miljonites | osakaal (%) igal paneelil, ühik teljel |
| Pealkiri on failinimi (`c_tonn_per_ha_final_2022_10m`) | ekspert peab nime meelde tuletama; pikad nimed lähevad kokku (`vee_reguleerimisvoime…`) | teenuse nimi ametlikust kihitabelist + ühik + grupp; sorteeritav ja rühmitatud |
| Üks paneel kihi kohta, kõik seisundid kokku | ei näita, kas jaotus erineb seisundiga – projekti põhiküsimus | **virnastatud tulbad seisundivärvides**: tulba kõrgus = kõigi pikslite osakaal, värv = milline seisund selle väärtuse annab |
| Täpne null domineerib (seisundiga pikslitest on täpne 0 mustikate/pohlade saagikusel 86 %, fosfori ja süsiniku ärakandel 43 %, söögiseente saagikusel 39 %, kasemahla tulul 22 %; kolleegi graafikul on tipp veelgi kõrgem, tõenäoliselt seetõttu, et sinna jääb ka seisundita ala – seda ei ole kontrollitud) | ülejäänud jaotus on nähtamatu | nullide osakaal eraldi sildina; lüliti „ilma nullideta“ |
| Heterogeensed vahemikud (diskreetsed + pidevad kihid sama stiiliga; `26.88`, `79.1845` telje sildid) | sildid on müra; diskreetsed skoorid (0–10, 1–3) ja pidevad kihid vajavad eri joonist | diskreetsed kihid tulpadena väärtuse kaupa, pidevad astmelise histogrammina; ümmargused teljesildid |
| Viltused jaotused lineaarsel teljel (süsiniku varu, ärakanne) | tipp pressitakse vasakule, saba tühi | ruutjuure telg (märgitud) viltustel jaotustel |
| Mõned paarid näevad välja identsed | paneelid dubleerivad infot | kontrollitud: neljal paaril on seisundikaupa jaotuse kattuvus kõigis ökosüsteemides ≥ 0,98 (mustikate/pohlade saagikus ja tulu 0,99; fosfori ärakanne kg ja EUR 1,00; veevoogude reguleerimisvõime m³ ja EUR 0,98; õhusaaste puhverdamisvõime ja selle rahaline väärtus 1,00). Need kihid erinevad skaala (hinna), mitte kuju poolest; lehel on neil märge „sama kuju kui …“ |
| Ökosüsteemi/seisundi lõige puudub | graafik ei näita, millise ökosüsteemi/seisundi pikslid jaotuse moodustavad (kõik klassid koos, ilmselt ka seisundita ala) | lõige ökosüsteemi/alamökosüsteemi järgi; arvesse lähevad ainult seisundiga pikslid (vt metoodika § 5.3) |
| Kõik paneelid sama kõrgusega | oluline ja ebaoluline ei eristu | järjestus: grupp → nimi; lisaks sort kattuvuse, nullide osakaalu või muutuse järgi |

Metoodika v2: ka madalama lahutusvõimega kihtidel (930 m, 1 km vektor) on jaotus 10 m lahutusvõimel
(ruudu sees on väärtus sama). Kihtide ülevaade arvestab ainult seisundiga
piksleid (hea/keskmine/vilets), mitte kogu kihi pindala, seega ei lange paneelid täpselt kokku
kogu raster-histogrammiga.
