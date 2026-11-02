# Tulemuste kokkuvõte

Genereeritud `oks.report.write_results`-ga failist `data/tulemused/paarid.parquet`. Meetod: [metoodika.md](metoodika.md). Metoodika v2: hinnangud põhinevad täpsetel pikslimediaanidel (otsused: [metoodika_v2_otsused.md](metoodika_v2_otsused.md)). Metoodika v3: lisandusid kuivad ja märjad metsad (tase `ruhm`, oma FDR-perekond; otsused: [metoodika_v3_otsused.md](metoodika_v3_otsused.md)).

## 1. Ulatus

* 34 teenust, 45 ökosüsteemi/alamökosüsteemi üksust (taseme kaupa), 4384 seisundipaari hinnangut.
* Parameetrid: klaster 10×10 km, 4000 bootstrapi, min 1,0 ha, FDR α = 0,05.

| Tase | Hinnanguid | Paaritatud: piisavalt andmeid | …neist olulisi (q<0,05) | Paaritamata: piisavalt andmeid | …neist olulisi | Oluline mõlemal ja sama märk |
|---|---|---|---|---|---|---|
| Ökosüsteem | 408 | 391 | 184 | 398 | 168 | 98 |
| Kuivad ja märjad metsad | 204 | 204 | 129 | 204 | 111 | 85 |
| Alamökosüsteem | 3772 | 3043 | 991 | 3278 | 844 | 617 |

## 2. Ökosüsteemide tase: mitu teenust muutub seisundi paranedes

Paaritatud hinnang mediaanide põhjal, ainult hinnangud, kus on piisavalt andmeid. „Kasvab” = Δ > 0 ja q < 0,05; „väheneb” = Δ < 0 ja q < 0,05.

| Ökosüsteem | Seisundipaar | Teenuseid | Kasvab | Väheneb | Ei ole oluline |
|---|---|---|---|---|---|
| Rohumaad | vilets → keskmine | 34 | 9 | 6 | 19 |
| Rohumaad | keskmine → hea | 34 | 6 | 7 | 21 |
| Rohumaad | vilets → hea | 34 | 7 | 7 | 20 |
| Sood | vilets → keskmine | 32 | 9 | 7 | 16 |
| Sood | keskmine → hea | 31 | 3 | 7 | 21 |
| Sood | vilets → hea | 31 | 8 | 9 | 14 |
| Metsad | vilets → keskmine | 34 | 19 | 6 | 9 |
| Metsad | keskmine → hea | 34 | 20 | 0 | 14 |
| Metsad | vilets → hea | 34 | 21 | 1 | 12 |
| Kuivad metsad | vilets → keskmine | 34 | 19 | 5 | 10 |
| Kuivad metsad | keskmine → hea | 34 | 19 | 0 | 15 |
| Kuivad metsad | vilets → hea | 34 | 21 | 1 | 12 |
| Märjad metsad | vilets → keskmine | 34 | 17 | 8 | 9 |
| Märjad metsad | keskmine → hea | 34 | 20 | 2 | 12 |
| Märjad metsad | vilets → hea | 34 | 17 | 0 | 17 |
| Põllumaad | vilets → keskmine | 31 | 12 | 4 | 15 |
| Põllumaad | keskmine → hea | 31 | 7 | 0 | 24 |
| Põllumaad | vilets → hea | 31 | 8 | 1 | 22 |

## 3. Suurimad muutused (vilets → hea, paaritatud mediaanide põhjal, olulised)

„Mediaan vilets/hea“ on kogu ökosüsteemi pikslite mediaan. Δ on samas 1 km plokis ja alamökosüsteemis arvutatud mediaanide vahede kaalutud keskmine, seega võib Δ erineda kahe mediaani vahest (nt mõlemad mediaanid 0, kuid plokkide sees on erinevus).

### Rohumaad

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,00 | 8,00 | 2,70 | +53 % | 2,61 … 2,77 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 14,0 | 26,0 | 5,14 | +24 % | 4,66 … 5,64 |  |
| Ökosüsteemide tugi tolmeldajatele | indeks 0-1 | 0,153 | 0,106 | 0,037 | +23 % | 0,030 … 0,046 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 47,0 | 80,0 | 13,9 | +21 % | 13,2 … 14,6 |  |
| Söögiseentest saadav potentsiaalne tulu | EUR/ha/a | 0,000 | 0,000 | -1,98 | -32 % | -3,74 … -0,608 |  |
| Niidu puitsesse biomassi seotud süsiniku varu | t C/ha | 0,000 | 0,000 | -8,16 | -56 % | -9,56 … -6,93 |  |
| Mustikate ja pohlade potentsiaalne tulu | EUR/ha/a | 0,000 | 0,000 | -0,813 | -88 % | -1,96 … -0,128 |  |
| Mustikate ja pohlade potentsiaalne saagikus | kg/ha | 0,000 | 0,000 | -0,325 | -88 % | -0,782 … -0,051 |  |

### Sood

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 4,00 | 9,00 | 2,43 | +41 % | 2,36 … 2,51 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 11,0 | 26,0 | 4,11 | +20 % | 3,88 … 4,36 |  |
| Loodusturismi hüve rahaline väärtus tarbijakulude alusel | EUR/ha | 158,0 | 237,0 | 32,8 | +18 % | 30,8 … 35,0 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 50,0 | 72,0 | 10,4 | +18 % | 10,1 … 10,8 |  |
| Fosfori mullaerosiooniga ärakande hind | EUR/ha/a | 0,001 | 0,000 | -0,001 | -64 % | -0,001 … -0,001 |  |
| Orgaanilise süsiniku ärakanne | kg/ha/a | 0,009 | 0,000 | -0,009 | -65 % | -0,012 … -0,007 |  |
| Söögiseentest saadav potentsiaalne tulu | EUR/ha/a | 0,000 | 0,000 | -28,0 | -99 % | -31,6 … -24,5 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 0,000 | 0,000 | -6,23 | -99 % | -7,03 … -5,46 |  |

### Metsad

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 16,0 | 81,0 | 72,7 | +291 % | 70,6 … 74,7 |  |
| Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | EUR/ha | 4 726 | 24 005 | 21 515 | +291 % | 20 891 … 22 129 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,00 | 8,00 | 4,21 | +125 % | 4,20 … 4,23 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 12,0 | 31,7 | 24,5 | +113 % | 23,1 … 25,8 |  |
| Mulla orgaanilise süsiniku varu | t C/ha | 688,0 | 934,0 | 38,9 | +4 % | 31,2 … 47,0 |  |
| Mulla orgaanilise süsiniku varu rahaline väärtus (sotsiaalse kulu hind) | EUR/ha | 428 662 | 581 934 | 24 239 | +4 % | 19 430 … 29 304 |  |
| Loodusmaastiku sidusus 1 km raadiuses | osakaal 0-100 (tõlgendus kinnitada) | 49,0 | 81,0 | 2,71 | +4 % | 2,53 … 2,90 |  |
| Pohlade potentsiaalne saagikus | kg/ha | -1,00 | -1,00 | -0,045 | -11 % | -0,069 … -0,020 |  |

### Kuivad metsad

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 14,0 | 102,0 | 84,5 | +366 % | 81,8 … 87,2 |  |
| Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | EUR/ha | 4 189 | 30 299 | 25 022 | +366 % | 24 207 … 25 812 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,00 | 8,00 | 4,21 | +129 % | 4,19 … 4,23 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 26,2 | 81,1 | 33,4 | +115 % | 31,5 … 35,2 |  |
| Mulla orgaanilise süsiniku varu rahaline väärtus (sotsiaalse kulu hind) | EUR/ha | 358 880 | 415 578 | 20 368 | +5 % | 14 790 … 25 566 |  |
| Mulla orgaanilise süsiniku varu | t C/ha | 576,0 | 667,0 | 32,7 | +5 % | 23,7 … 41,0 |  |
| Loodusmaastiku sidusus 1 km raadiuses | osakaal 0-100 (tõlgendus kinnitada) | 46,0 | 78,0 | 2,57 | +4 % | 2,35 … 2,79 |  |
| Pohlade potentsiaalne saagikus | kg/ha | -1,00 | 3,00 | -0,101 | -9 % | -0,132 … -0,071 |  |

### Märjad metsad

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Metsa puitsesse biomassi seotud süsiniku varu | t C/ha | 19,0 | 66,0 | 57,9 | +212 % | 55,6 … 60,0 |  |
| Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | EUR/ha | 5 543 | 19 456 | 17 133 | +212 % | 16 472 … 17 777 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 3,00 | 8,00 | 4,22 | +121 % | 4,20 … 4,24 |  |
| Söögiseente potentsiaalne saagikus | kg/ha | 7,20 | 14,4 | 13,4 | +107 % | 12,3 … 14,5 |  |
| Loodusmaastiku sidusus 1 km raadiuses | osakaal 0-100 (tõlgendus kinnitada) | 53,0 | 84,0 | 2,89 | +4 % | 2,64 … 3,18 |  |
| Mulla orgaanilise süsiniku varu | t C/ha | 913,0 | 1 638 | 46,9 | +4 % | 33,5 … 60,7 |  |
| Mulla orgaanilise süsiniku varu rahaline väärtus (sotsiaalse kulu hind) | EUR/ha | 568 850 | 1 020 566 | 29 209 | +4 % | 20 891 … 37 789 |  |
| Mulla orgaanilise süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | EUR/ha | 270 335 | 485 005 | 13 881 | +4 % | 9 928 … 17 958 |  |

### Põllumaad

| Teenus | Ühik | Mediaan vilets | Mediaan hea | Δ | Δ % | 95 % CI (Δ) | Märkus |
|---|---|---|---|---|---|---|---|
| Kahjuritõrje vajaduse vähenemine | arvatavasti % (väli pestits_vahenemine) | 0,000 | 0,000 | 26,6 | +320 % | 22,7 … 30,7 |  |
| Elupaikade säilitamine looduslikele liikidele | indeks 0-10 | 1,00 | 3,00 | 1,63 | +102 % | 1,52 … 1,74 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus | skoor | 6,00 | 12,0 | 3,09 | +30 % | 2,71 … 3,49 |  |
| Maismaaökosüsteemide summaarne virgestusväärtus tarbijakulude alusel | EUR/ha | 55,0 | 55,0 | 9,67 | +16 % | 8,04 … 11,4 |  |
| Loodusmaastiku sidusus 1 km raadiuses | osakaal 0-100 (tõlgendus kinnitada) | 20,0 | 36,0 | 2,13 | +8 % | 1,46 … 2,74 |  |
| Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | skoor | 43,0 | 46,0 | 0,600 | +1 % | 0,334 … 0,874 |  |
| Loodusturismi hüve rahaline väärtus tarbijakulude alusel | EUR/ha | 118,0 | 158,0 | 1,82 | +1 % | 0,717 … 2,97 |  |
| Põllumajanduslike ökosüsteemide reaalboniteedid | reaalboniteet (väli boniteet) | 40,0 | 0,000 | -0,568 | -3 % | -0,998 … -0,165 |  |

### Võrdluseks: segumudel (930 m rastrid ja 1 km vektorruudud)

Need kihid on madalama lahutusvõimega kui seisundiüksus. Põhihinnang tuleb 10 m lahutusvõimele viidud kihist (ülal); segumudel (klasside pindalaosade lineaarne mudel, keskmisel põhinev, **uuriv**) on võrdluseks. Näidatud on kõik ökosüsteemid (vilets → hea), sõltumata olulisusest.

| Teenus | Ökosüsteem | Ühik | β vilets | β hea | Δ % | 95 % CI (Δ) | Oluline |
|---|---|---|---|---|---|---|---|
| Lammimuldade taastamise kulu | Rohumaad | EUR/ha/a (väli lammide_taastamise_kulu) | 4 702 | 6 634 | +41 % | 864,7 … 3 275 | jah |
| Lammimuldade taastamise kulu | Sood | EUR/ha/a (väli lammide_taastamise_kulu) | 351,6 | 6 857 | +1850 % | 4 482 … 8 999 | jah |
| Lammimuldade taastamise kulu | Metsad | EUR/ha/a (väli lammide_taastamise_kulu) | 1 178 | 4 659 | +296 % | 2 554 … 4 372 | jah |
| Lammimuldade taastamise kulu | Põllumaad | EUR/ha/a (väli lammide_taastamise_kulu) | 2 545 | 3 722 | +46 % | -1 098 … 3 516 | ei |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Rohumaad | EUR/ha | 5,49 | 4,97 | -9 % | -0,805 … -0,286 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Sood | EUR/ha | 6,75 | 5,84 | -14 % | -1,26 … -0,584 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Metsad | EUR/ha | 6,59 | 5,93 | -10 % | -0,914 … -0,401 | jah |
| Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | Põllumaad | EUR/ha | 6,54 | 5,64 | -14 % | -1,48 … -0,174 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Rohumaad | kg/ha/a | 1,37 | 1,24 | -9 % | -0,201 … -0,071 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Sood | kg/ha/a | 1,69 | 1,46 | -14 % | -0,314 … -0,146 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Metsad | kg/ha/a | 1,65 | 1,48 | -10 % | -0,229 … -0,100 | jah |
| Vee puhastamise potentsiaal kaldapuhvrite poolt | Põllumaad | kg/ha/a | 1,64 | 1,41 | -14 % | -0,370 … -0,043 | jah |

## 4. Paaritatud ja paaritamata hinnang

* Võrreldavaid hinnanguid: 3638; sama märgiga: 2420 (67 %).
* Mõlemal hinnangul olulised, kuid **vastupidise märgiga**: 25 (nende puhul muudab asukoha/koosseisu kontroll järelduse suunda).

| Teenus | Üksus | Seisundipaar | Δ paaritatud | Δ paaritamata |
|---|---|---|---|---|
| Orgaanilise süsiniku ärakanne | Rohumaad | vilets → keskmine | 0,035 | -0,020 |
| Orgaanilise süsiniku ärakanne | Metsad | keskmine → hea | 0,048 | -0,026 |
| Orgaanilise süsiniku ärakanne | Metsad | vilets → hea | 0,059 | -0,042 |
| Orgaanilise süsiniku ärakanne | alam 11800 | vilets → keskmine | 0,036 | -0,022 |
| Orgaanilise süsiniku ärakanne | Märjad metsad | keskmine → hea | 0,008 | -0,017 |
| Fosfori mullaerosiooniga ärakande hind | Metsad | keskmine → hea | 0,024 | -0,002 |
| Fosfori mullaerosiooniga ärakande hind | alam 11800 | vilets → keskmine | 0,017 | -0,009 |
| Fosfori mullaerosiooniga ärakande hind | Kuivad metsad | keskmine → hea | 0,044 | -0,014 |
| Fosfori mullaerosiooniga ärakande hind | Märjad metsad | keskmine → hea | 0,003 | -0,001 |
| Fosfori ärakanne | Metsad | keskmine → hea | 0,006 | -0,000 |
| Fosfori ärakanne | alam 11800 | vilets → keskmine | 0,004 | -0,002 |
| Fosfori ärakanne | Kuivad metsad | keskmine → hea | 0,011 | -0,003 |
| Fosfori ärakanne | Märjad metsad | keskmine → hea | 0,001 | -0,000 |
| Kasemahla tootmisest saadava tulu potentsiaal | Metsad | vilets → hea | 4,88 | -2,00 |
| Kasemahla tootmisest saadava tulu potentsiaal | Kuivad metsad | vilets → hea | 3,48 | -4,00 |
| Kasemahla potentsiaalne saagikus | Metsad | vilets → hea | 16,0 | -7,54 |
| Kasemahla potentsiaalne saagikus | alam 30500 | vilets → keskmine | 1,22 | -1,89 |
| Kasemahla potentsiaalne saagikus | Kuivad metsad | vilets → hea | 11,3 | -11,3 |
| Ökosüsteemide tugi tolmeldajatele | Rohumaad | vilets → hea | 0,037 | -0,047 |
| Ökosüsteemide tugi tolmeldajatele | Sood | vilets → keskmine | -0,017 | 0,008 |
| Ökosüsteemide tugi tolmeldajatele | Sood | vilets → hea | -0,020 | 0,010 |
| Ökosüsteemide tugi tolmeldajatele | Kuivad metsad | vilets → keskmine | -0,002 | 0,016 |
| Soo puitsesse biomassi seotud süsiniku varu | Sood | vilets → keskmine | -0,648 | 0,759 |
| Veevoogude reguleerimisvõime (va linnalised teed veekogud) rahaline väärtus | Rohumaad | vilets → keskmine | -27,0 | 5,00 |
| Veevoogude reguleerimisvõime (va linnalised teed veekogud) maht | Rohumaad | vilets → keskmine | -50,9 | 10,0 |

## 5. Mudelipõhisus (η² ≥ 0,9)

Kihid ja ökosüsteemid, kus ≥ 90 % pikslitaseme dispersioonist on seletatav baaskaardi klassiga. Muutus seisundi vahel on neil osaliselt definitsiooniline.

| Teenus | Ökosüsteem | η² (klass) | η² (seisund alamökosüsteemi sees) |
|---|---|---|---|
| Elupaikade säilitamine looduslikele liikidele | Sood | 0,93 | 0,68 |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Rohumaad | 1,00 | – |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Sood | 1,00 | – |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Metsad | 1,00 | 0,00 |
| Mikrokliima reguleerimine (temperatuuri erinevuse määr) | Põllumaad | 1,00 | – |
| Õhusaaste puhverdamisvõime | Põllumaad | 1,00 | 0,00 |
| Õhusaaste puhverdamisvõime rahaline väärtus | Põllumaad | 1,00 | 0,00 |
| Ökosüsteemide tugi tolmeldajatele | Metsad | 0,90 | 0,13 |

## 6. Tundlikkus

Põhijooksu olulistest hinnangutest (paaritatud) säilis oluliseks sama märgiga:

| Variant | Tase | Võrreldavaid | Põhijooksu olulisi | Säilinud | Säilinud % | Uusi olulisi | Spearman ρ (Δ) |
|---|---|---|---|---|---|---|---|
| klaster5km | okosusteem | 391 | 184 | 184 | +100 % | 9 | 1,000 |
| klaster5km | alam | 3043 | 991 | 983 | +99 % | 32 | 1,000 |
| klaster5km | ruhm | 204 | 129 | 127 | +98 % | 0 | 1,000 |
| klaster20km | okosusteem | 391 | 184 | 184 | +100 % | 1 | 1,000 |
| klaster20km | alam | 3043 | 991 | 973 | +98 % | 20 | 1,000 |
| klaster20km | ruhm | 204 | 129 | 125 | +97 % | 0 | 1,000 |
| ala_0_25ha | okosusteem | 391 | 184 | 182 | +99 % | 17 | 0,986 |
| ala_0_25ha | alam | 3043 | 991 | 973 | +98 % | 79 | 0,919 |
| ala_0_25ha | ruhm | 204 | 129 | 129 | +100 % | 4 | 0,990 |
| ala_4ha | okosusteem | 390 | 183 | 164 | +90 % | 3 | 0,859 |
| ala_4ha | alam | 2163 | 832 | 716 | +86 % | 38 | 0,879 |
| ala_4ha | ruhm | 204 | 129 | 127 | +98 % | 1 | 0,959 |
| seeme_2 | okosusteem | 391 | 184 | 184 | +100 % | 6 | 1,000 |
| seeme_2 | alam | 3043 | 991 | 990 | +100 % | 10 | 1,000 |
| seeme_2 | ruhm | 204 | 129 | 128 | +99 % | 0 | 1,000 |

Variandid: `klaster5km`, `klaster20km` (bootstrap-klastri suurus), `ala_0_25ha`, `ala_4ha` (minimaalne ala stratumis), `seeme_2` (teine juhuslik seeme).
