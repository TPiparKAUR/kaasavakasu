# Andmekataloog

Genereeritud `oks.report.write_catalogue`-ga failidest `alusmaterjalid/metaandmed/layer_definition_checked_vrs2.xlsx` ja `data/arhiiv_failid.csv`.

Ametlikus tabelis on 136 kihti, neist `eval = TRUE`: 32 (1 baaskaart + 35 teenust).

## Analüüsitavad teenused (`eval = TRUE`)

| Grupp | Nimi | Kihi id | Tüüp | Eraldusvõime (m) | Väärtuse tüüp | Omadus | Ühik (tabelist) | Allikas | Fail arhiivis |
|---|---|---|---|---|---|---|---|---|---|
| Bioloogiline tõrje | Kahjuritõrje potentsiaalne kulu | biotorje_kahjuritorje_vahenemine | puudub |  |  | rahaline | – | ELME2 | puudub arhiivis |
| Bioloogiline tõrje | Kahjuritõrje vajaduse vähenemine | biotorje_2022 | vektor |  |  | biofüüsikaline | arvatavasti % (väli pestits_vahenemine) | ELME2 | Bioloogiline_torje/biotorje_2022.gpkg |
| Elupaikade säilitamine | Elupaikade säilitamine looduslikele liikidele | elupaigahuve_pakkumine_2022_10m | raster | 10 | Järjestus | muu | indeks 0-10 | ELME2 | Elupaigahuve/elupaigahuve_pakkumine_2022_10m.tif |
| Elupaikade säilitamine | Loodusmaastiku sidusus 1 km raadiuses | sidusus_1km_2022_10m | raster | 10 | Pidev | muu | osakaal 0-100 (tõlgendus kinnitada) | ELME2 | Sidusus/sidusus_1km_2022_10m.tif |
| Globaalne kliimaregulatsioon | Metsa puitsesse biomassi seotud süsiniku varu | puitne_biomass_c_t_ha_kogu_eesti_sum_2022_5m | raster | 5 | Pidev | biofüüsikaline | t C/ha | ELME2 | Globaalne_kliimaregulatsioon/puitne_biomass_c_t_ha_kogu_eesti_sum_2022_5m.tif |
| Globaalne kliimaregulatsioon | Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m | raster | 5 | Pidev | rahaline | EUR/ha | ELME2 | Globaalne_kliimaregulatsioon/puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m.tif |
| Globaalne kliimaregulatsioon | Mulla orgaanilise süsiniku varu | c_tonn_per_ha_final_2022_10m | raster | 10 | Pidev | biofüüsikaline | t C/ha | ELME2 | Globaalne_kliimaregulatsioon/c_tonn_per_ha_final_2022_10m.tif |
| Globaalne kliimaregulatsioon | Mulla orgaanilise süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind) | mullasusinik_aasta_keskmine_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha | ELME2 | Globaalne_kliimaregulatsioon/mullasusinik_aasta_keskmine_2022_10m.tif |
| Globaalne kliimaregulatsioon | Mulla orgaanilise süsiniku varu rahaline väärtus (sotsiaalse kulu hind) | mullasusinik_aasta_sotsiaalne_kulu_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha | ELME2 | Globaalne_kliimaregulatsioon/mullasusinik_aasta_sotsiaalne_kulu_2022_10m.tif |
| Globaalne kliimaregulatsioon | Niidu puitsesse biomassi seotud süsiniku varu | puitne_biomass_c_t_ha_niit_sum_2022_5m | raster | 5 | Pidev | biofüüsikaline | t C/ha | ELME2 | Globaalne_kliimaregulatsioon/puitne_biomass_c_t_ha_niit_sum_2022_5m.tif |
| Globaalne kliimaregulatsioon | Soo puitsesse biomassi seotud süsiniku varu | puitne_biomass_c_t_ha_soo_sum_2022_5m | raster | 5 | Pidev | biofüüsikaline | t C/ha | ELME2 | Globaalne_kliimaregulatsioon/puitne_biomass_c_t_ha_soo_sum_2022_5m.tif |
| Kultuurilised hüved | Loodusturismi hüve rahaline väärtus tarbijakulude alusel | loodusturism_eur_ha_2022_5m | raster | 5 | Järjestus | rahaline | EUR/ha | ELME2 | Kultuurilised_huved/loodusturism_eur_ha_2022_5m.tif |
| Kultuurilised hüved | Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina | loodusturism_kaalsum_2022_5m | raster | 5 | Järjestus | muu | skoor | ELME2 | Kultuurilised_huved/loodusturism_kaalsum_2022_5m.tif |
| Kultuurilised hüved | Maismaaökosüsteemide summaarne virgestusväärtus | virgestuse_koondvaartus_2022_5m | raster | 5 | Järjestus | muu | skoor | ELME2 | Kultuurilised_huved/virgestuse_koondvaartus_2022_5m.tif |
| Kultuurilised hüved | Maismaaökosüsteemide summaarne virgestusväärtus tarbijakulude alusel | virgestuse_koondvaartus_eur_ha_2022_5m | raster | 5 | Järjestus | rahaline | EUR/ha | ELME2 | Kultuurilised_huved/virgestuse_koondvaartus_eur_ha_2022_5m.tif |
| Loodusannid | Kasemahla potentsiaalne saagikus | kasemahl_saagikus_2020_10m | raster | 10 | Pidev | biofüüsikaline | l/0,01 ha | ELME2 | Loodusannid/kasemahl_saagikus_2020_10m.tif |
| Loodusannid | Kasemahla tootmisest saadava tulu potentsiaal | kasemahl_hind_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha | ELME2 | Loodusannid/kasemahl_hind_2022_10m.tif |
| Loodusannid | Mustikate ja pohlade potentsiaalne saagikus | mustikad_pohlad_saagikus_2020_10m | raster | 10 | Järjestus | biofüüsikaline | kg/ha | ELME1 | Loodusannid/mustikad_pohlad_saagikus_2020_10m.tif |
| Loodusannid | Mustikate ja pohlade potentsiaalne tulu | mustikad_pohlad_hind_2022_10m | raster | 10 | Järjestus | rahaline | EUR/ha/a | ELME2 | Loodusannid/mustikad_pohlad_hind_2022_10m.tif |
| Loodusannid | Pohlade potentsiaalne saagikus | pohlad_saagikus_2020_10m | raster | 10 | Diskreetne | biofüüsikaline | kg/ha | ELME1 | Loodusannid/pohlad_saagikus_2020_10m.tif |
| Loodusannid | Söögiseente potentsiaalne saagikus | seened_saagikus_2020_10m | raster | 10 | Pidev | biofüüsikaline | kg/ha | ELME1 | Loodusannid/seened_saagikus_2020_10m.tif |
| Loodusannid | Söögiseentest saadav potentsiaalne tulu | seened_hind_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha/a | ELME2 | Loodusannid/seened_hind_2022_10m.tif |
| Mikrokliima reguleerimine | Mikrokliima reguleerimine (temperatuuri erinevuse määr) | kliimaregulatsioon_2022_5m | raster | 5 | Järjestus | muu | suhtarv (klassi põhine) | ELME2 | Mikrokliima_regulatsioon/kliimaregulatsioon_2022_5m.tif |
| Puhverdavad teenused | Fosfori mullaerosiooniga ärakande hind | erosioon_p_eur_ha_a_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha/a | ELME2 | Puhverdavad_teenused/erosioon_P_eur_ha_a_2022_10m.tif |
| Puhverdavad teenused | Fosfori ärakanne | erosioon_p_kg_ha_a_2022_10m | raster | 10 | Pidev | biofüüsikaline | kg/ha/a | ELME2 | Puhverdavad_teenused/erosioon_P_kg_ha_a_2022_10m.tif |
| Puhverdavad teenused | Lammimuldade taastamise kulu | lamm_grd1000_am_drained_2022 | vektor |  |  | rahaline | EUR/ha/a (väli lammide_taastamise_kulu) | ELME2 | Puhverdavad_teenused/lamm_grd1000_am_drained_2022.gpkg |
| Puhverdavad teenused | Orgaanilise süsiniku ärakanne | erosioon_c_kg_ha_a_2022_10m | raster | 10 | Pidev | biofüüsikaline | kg/ha/a | ELME2 | Puhverdavad_teenused/erosioon_C_kg_ha_a_2022_10m.tif |
| Puhverdavad teenused | Vee puhastamise potentsiaal kaldapuhvrite poolt | vee_puhastamise_potentsiaal_p_kg_ha_a_2022_930m | raster | 930 | Pidev | biofüüsikaline | kg/ha/a | ELME2 | Puhverdavad_teenused/vee_puhastamise_potentsiaal_P_kg_ha_a_2022_930m.tif |
| Puhverdavad teenused | Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus | vee_puhastamise_potentsiaal_p_eur_ha_2022_930m | raster | 930 | Pidev | rahaline | EUR/ha | ELME2 | Puhverdavad_teenused/vee_puhastamise_potentsiaal_P_eur_ha_2022_930m.tif |
| Puhverdavad teenused | Veevoogude reguleerimisvõime (va linnalised teed veekogud) maht | vee_reguleerimisvoime_vol_ha_linnalised_teed_veekogud_2022_10m | raster | 10 | Pidev | biofüüsikaline | m3/ha | ELME2 | Puhverdavad_teenused/vee_reguleerimisvoime_vol_ha_linnalised_teed_veekogud_2022_10m.tif |
| Puhverdavad teenused | Veevoogude reguleerimisvõime (va linnalised teed veekogud) rahaline väärtus | vee_reguleerimisvoime_eur_ha_linnalised_teed_veekogud_2022_10m | raster | 10 | Pidev | rahaline | EUR/ha | ELME2 | Puhverdavad_teenused/vee_reguleerimisvoime_eur_ha_linnalised_teed_veekogud_2022_10m.tif |
| Puhverdavad teenused | Õhusaaste puhverdamisvõime | ohusaaste_puhverdusvoime_2022_5m | raster | 5 | Järjestus | muu | indeks 1-10 | ELME2 | Puhverdavad_teenused/ohusaaste_puhverdusvoime_2022_5m.tif |
| Puhverdavad teenused | Õhusaaste puhverdamisvõime rahaline väärtus | ohusaaste_puhverdusvoime_eur_ha_2022_5m | raster | 5 | Pidev | rahaline | EUR/ha | ELME2 | Puhverdavad_teenused/ohusaaste_puhverdusvoime_eur_ha_2022_5m.tif |
| Toit ja sööt põllult | Põllumajanduslike ökosüsteemide reaalboniteedid | toiduteenus_2022 | vektor |  |  | muu | reaalboniteet (väli boniteet) | ELME2 | Toit_soot_pollult/toiduteenus_2022.gpkg |
| Tolmeldamine | Ökosüsteemide tugi tolmeldajatele | okosusteemide_tugi_tolmeldajatele_2022_10m | raster | 10 | Pidev | muu | indeks 0-1 | ELME2 | Tolmeldamine/okosusteemide_tugi_tolmeldajatele_2022_10m.tif |

## Märkused kihtide kohta (ametlikust tabelist ja kontrollidest)

* **Kahjuritõrje potentsiaalne kulu** (`biotorje_kahjuritorje_vahenemine`): Tabeli märkus: Kasutada ühte. Eraldi käsitlus
* **Kahjuritõrje vajaduse vähenemine** (`biotorje_2022`): Kahjuritõrje vajaduse vähenemine põllumassiivil; arvutatud maastikuelementide katvusest ja põllu seisundiklassist (seos seisundiga on definitsiooniline). Tabeli märkus: 'Kasutada ühte. Eraldi käsitlus'; pestitshind_ha (EUR/ha) on sama muutuja rahas · Tabeli märkus: Kasutada ühte. Eraldi käsitlus
* **Elupaikade säilitamine looduslikele liikidele** (`elupaigahuve_pakkumine_2022_10m`): 0 madal, 10 kõrge
* **Loodusmaastiku sidusus 1 km raadiuses** (`sidusus_1km_2022_10m`): Loodusmaastiku sidusus 1 km raadiuses: heas seisundis looduslike ökosüsteemide osakaal maismaapikslitest 1 km raadiuses. Lähtekas: 'kasutame ühte sidusust (nt 1 km raadiusega loodusmaastik?)'; raadius ja skaala kinnitada. Tabeli märkus: 'Võib vajada teistsugust lähenemist'. Seos seisundiga on osaliselt definitsiooniline (sidusus arvutatud heas seisundis ökosüsteemide osakaalust) · Tabeli märkus: Võib vajada teistsugust lähenemist
* **Metsa puitsesse biomassi seotud süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind)** (`puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m`): Metsa puitse biomassi süsinikuvaru väärtus (varu, mitte aastane voog), ETS 80,68 EUR/t CO2. Lisakiht lähtekasu alusel
* **Mulla orgaanilise süsiniku varu** (`c_tonn_per_ha_final_2022_10m`): Mulla orgaanilise süsiniku varu; suuremad veekogud, linnad ja >6 m teed eemaldatud
* **Mulla orgaanilise süsiniku varu rahaline väärtus (aasta keskmine ETS börsihind)** (`mullasusinik_aasta_keskmine_2022_10m`): Mulla süsinikuvaru väärtus (varu, mitte aastane voog), ETS 2022 keskmine börsihind 80,68 EUR/t CO2; tabeli märkus: 'Hind kokku leppida'. Lisakiht lähtekasu alusel · Tabeli märkus: Hind kokku leppida
* **Mulla orgaanilise süsiniku varu rahaline väärtus (sotsiaalse kulu hind)** (`mullasusinik_aasta_sotsiaalne_kulu_2022_10m`): Mulla süsinikuvaru väärtus (varu, mitte aastane voog), sotsiaalse kulu hind 169,77 EUR/t CO2 (Rennert et al. 2022). Lisakiht lähtekasu alusel
* **Niidu puitsesse biomassi seotud süsiniku varu** (`puitne_biomass_c_t_ha_niit_sum_2022_5m`): Tabeli märkus: 'Üle otsustada. Sõltub kihi metoodika sobivusest' · Tabeli märkus: Üle otsustada. Sõltub kihi metoodika sobivusest
* **Loodusturismi hüve rahaline väärtus tarbijakulude alusel** (`loodusturism_eur_ha_2022_5m`): 637 mln EUR jaotatud kaalude alusel; astmeline (11 taset)
* **Loodusturismi hüve – looduslikkuse suhteline väärtus loodusobjektina** (`loodusturism_kaalsum_2022_5m`): Ekspertkaalude summa
* **Maismaaökosüsteemide summaarne virgestusväärtus** (`virgestuse_koondvaartus_2022_5m`): Ekspertkaalude summa
* **Maismaaökosüsteemide summaarne virgestusväärtus tarbijakulude alusel** (`virgestuse_koondvaartus_eur_ha_2022_5m`): Aastane kogukulu (320 mln EUR) jaotatud kaalude alusel; astmeline (11 taset)
* **Kasemahla potentsiaalne saagikus** (`kasemahl_saagikus_2020_10m`): Soo- ja kõdusoometsades andmed puuduvad; avakooslused väärtusega 0
* **Kasemahla tootmisest saadava tulu potentsiaal** (`kasemahl_hind_2022_10m`): Kokkuostuhind 0,3 EUR/l
* **Mustikate ja pohlade potentsiaalne tulu** (`mustikad_pohlad_hind_2022_10m`): Kokkuostuhind 2,5 EUR/kg (2022)
* **Pohlade potentsiaalne saagikus** (`pohlad_saagikus_2020_10m`): Diskreetne; väärtused -1..7, -1 on tabeli järgi kehtiv väärtus (has_negative=1)
* **Söögiseente potentsiaalne saagikus** (`seened_saagikus_2020_10m`): 58 liigi hinnanguline saagikus
* **Söögiseentest saadav potentsiaalne tulu** (`seened_hind_2022_10m`): Kokkuostuhind 4,5 EUR/kg (2022)
* **Mikrokliima reguleerimine (temperatuuri erinevuse määr)** (`kliimaregulatsioon_2022_5m`): VÄIKSEM väärtus = ühtlasem temperatuur = parem regulatsioon; arvutatud baaskaardi klassi kohta
* **Fosfori mullaerosiooniga ärakande hind** (`erosioon_p_eur_ha_a_2022_10m`): Fosforikao kulu; suurem väärtus = suurem kulu
* **Fosfori ärakanne** (`erosioon_p_kg_ha_a_2022_10m`): Fosfori ärakanne: suurem väärtus = suurem ärakanne
* **Lammimuldade taastamise kulu** (`lamm_grd1000_am_drained_2022`): 1 km ruudustik, väärtus ainult lammiruutudes (am_osa > 0); väärtus väheneb kuivendatud pindalaga, seos seisundiga kaudne · Tabeli märkus: Lamminiidud, märjad niidud kui olulised kohad sellele teenusele
* **Orgaanilise süsiniku ärakanne** (`erosioon_c_kg_ha_a_2022_10m`): Orgaanilise süsiniku ärakanne: suurem väärtus = suurem ärakanne
* **Vee puhastamise potentsiaal kaldapuhvrite poolt** (`vee_puhastamise_potentsiaal_p_kg_ha_a_2022_930m`): Ainult kaldapuhvrid; eraldusvõime 930 m
* **Vee puhastamise potentsiaali kaldapuhvrite poolt rahaline väärtus** (`vee_puhastamise_potentsiaal_p_eur_ha_2022_930m`): Ainult kaldapuhvrid; eraldusvõime 930 m
* **Veevoogude reguleerimisvõime (va linnalised teed veekogud) rahaline väärtus** (`vee_reguleerimisvoime_eur_ha_linnalised_teed_veekogud_2022_10m`): Tabeli märkus: 'Rahalise ühiku metoodika vananenud' · Tabeli märkus: Rahalise ühiku metoodika vananenud
* **Õhusaaste puhverdamisvõime** (`ohusaaste_puhverdusvoime_2022_5m`): Tabeli märkus: 255 käitub kui 0 (NoData) · Tabeli märkus: 255 käitub kui 0
* **Õhusaaste puhverdamisvõime rahaline väärtus** (`ohusaaste_puhverdusvoime_eur_ha_2022_5m`): Aastane ärahoitud tervisekulu 20,88 mln EUR jaotatud
* **Põllumajanduslike ökosüsteemide reaalboniteedid** (`toiduteenus_2022`): RINGLUSE HOIATUS: põllukultuuride seisundiklass A-D langeb baaskaardil kokku selle kihi väärtusklassiga A-D (kontrollitud: keskmine väärtusklass klassides A/B/C/D = 1,0006 / 2,0000 / 3,0000 / 4,0000, SD ~ 0,01), mis on tuletatud samast reaalboniteedist; seos seisundi ja boniteedi vahel on seetõttu osaliselt definitsiooniline. Tabeli märkus: 'Eraldi käsitlus' · Tabeli märkus: Eraldi käsitlus

## Arhiivi failid, mida ametlikus tabelis ei ole

* `Elupaigahuve/.tif`
* `Loodusannid/johvikad_hind_2022_10m_cog_mode.tif`
* `Sidusus/sidusus_2020_100m.tif`
* `output.fgb`

## `eval = FALSE` kihid, mis on arhiivis (analüüsist väljas)

73 kihti; täielik loetelu on `data/teenused.csv` (`eval` = FALSE, `tyyp` != puudub).
