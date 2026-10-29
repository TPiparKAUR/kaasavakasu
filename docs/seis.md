# Seis, avatud küsimused ja järgmised sammud

## Tehtud

| Samm | Seis |
|---|---|
| Arhiivi inventuur (105 faili, 43,6 GB) | tehtud, `data/arhiiv_failid.csv` |
| Ametliku kihtide tabeli (`eval = TRUE`) sidumine arhiiviga | tehtud, 31 teenust, `docs/andmekataloog.md` |
| Seisundi tähenduse tuletamine ja kontroll täisresolutsioonil | tehtud (264 koodi, 0 erandit) |
| 25 rastri (5/10 m) ja 2 põllumassiivi vektorkihi aggregeerimine | tehtud |
| Statistiline analüüs (paaritatud/paaritamata, klastri-bootstrap, FDR) | tehtud, `data/tulemused/` |
| 930 m rastrid ja 1 km vektor | tehtud; metoodika v2: viidud 10 m lahutusvõimele (madalam lahutusvõime), segumudel (uuriv) võrdluseks |
| Metoodika v2: täpsed pikslimediaanid, NoData = 0 (v.a erandkihid), vektorireeglid | tehtud, `docs/metoodika_v2_lopparuanne.md` |
| Tundlikkus (klaster 5/20 km, min ala 0,25/4 ha, teine seeme) | tehtud, `docs/tulemused.md` § 6 |
| Veebileht | tehtud, `site_src/`, ehitus `python -m oks site` |
| Väärtuste jaotus seisundi kaupa (pikslitaseme histogrammid) | tehtud; 28 kihti, kontroll plokitabeli vastu 3 081 kombinatsiooni, 0 lahknevust; veebis: Teenuse detail, Jaotused |
| Disainiprintsiibid, seisundipalett (punane–kollane–roheline), jaotuse vaated (kattuvad / eraldi / kumulatiivne), vaheleht Kihtide ülevaade | tehtud, `docs/disain.md` |
| Veebilehe infonupud (iga filtri tähendus, nt paaritatud/paaritamata) | tehtud |
| Lähteülesande (LTM) ja lähtekasu kriitiline analüüs, nõuete täitmine | tehtud, `docs/lahteulesanne.md` |
| Lähtekasu tulemustabelid (tüüp × seisund, suured ökosüsteemid, rannik; pindala; nullid arvesse) | tehtud, Excel `andmetabel_kaasneva_kasu.xlsx` |
| Nullide käsitluse parandus (NoData = 0 kihid) ja klassitabelid kõigile 264 klassile | tehtud, `docs/metoodika.md` § 2.3 ja § 5.4 |
| Kvalitatiivne raamistik, tõendusbaas, tegevuste koondtabeli mall | tehtud (ettepanekud; ekspert kinnitab) |
| Tegevuspõhine koondtabel | **ootel**: KLIMi meetmete nimekiri puudub |
| GitHub Pages töövoog | tehtud (vaikeharust); vajab Settings → Pages → Source: GitHub Actions |
| Testid (sünteetilised andmed teadaoleva vastusega), Ruff, mypy | rohelised |

## Tuvastatud andmeprobleemid

1. Arhiivis on neli faili, mida ametlikus tabelis ei ole (`Elupaigahuve/.tif` (nimeta), `johvikad_hind_2022_10m_cog_mode.tif`, `sidusus_2020_100m.tif`, `output.fgb`).
2. `biotorje_kahjuritorje_vahenemine` on tabelis eraldi kihina, kuid arhiivis eraldi faili pole (väli `biotorje_2022.gpkg`-s).
3. Ametliku tabeli `properties` väärtus „biofüüsikalinefüüsikaline” (`biotorje_2022`) on kirjaviga; analüüsis on see loetud „biofüüsikaline”.
4. Põllukultuuride seisundiklass A–D langeb kokku `toiduteenus_2022` väärtusklassiga; seos seisundi ja boniteedi vahel on seetõttu osaliselt definitsiooniline.
5. Täisarvude ületäitumine (Int32) ja poolikud allalaadimised on leitud ja parandatud; kontrollid on koodis.

## Küsimused ekspertidele (kinnitus vajalik)

1. **Seisundi kaardistus.** Kas `seisund_uldine` 1/2/3 = hea/keskmine/vilets ja ökosüsteemide A–F vastavus (metoodika § 2.2) on ELME2 metoodika kohaselt õige? Tuletatud andmetest, mitte dokumentatsioonist.
2. **`ohusaaste_puhverdusvoime_2022_5m`:** tabeli märkus „255 käitub kui 0”. Käsitletud NoData-na. Kui 255 tähendab hoopis väärtust 0 (kehtiv), muutub kihi keskmine.
3. **Ühikud**, mida tabel ei nimeta: `biotorje_2022` (`pestits_vahenemine`, arvatavasti %), `toiduteenus_2022` (`boniteet`), `lamm_grd1000_am_drained_2022` (`lammide_taastamise_kulu`), `kliimaregulatsioon_2022_5m` (suhtarv).
4. **`eval = FALSE` kihid** (73 arhiivis): kas mõnda neist tuleb hiljem analüüsida? Täiendavad kihid (`*_taiendavad`) on andmekataloogis olemas.
5. **Madalama lahutusvõimega kihid** (930 m rastrid, `lamm_grd1000…`): 10 m lahutusvõimel kordab hinnang ruudu väärtust ja seisundite erinevus tuleb ainult ruutude vahelistest erinevustest. Kas see on neil kihtidel piisav või tuleks need jätta analüüsist välja? (Segumudel on võrdluseks.)
6. **Aastate erinevus:** teenuste algandmed 2020 vs baaskaart 2022; kas see on vastuvõetav?

## GitLab

Selle töö sessioonist ei ole ligipääsu `gitlab.sise.envir.ee`-le. Repositooriumis on olemas `.gitlab-ci.yml` (lint + test + Pages) ja GitHub Actions peegeldus. Ülekanne GitLabi: lisa GitLabi remote ja tõsta haru üle (`git remote add gitlab …; git push gitlab claude/compassionate-babbage-mdfftn`).

## Järgmised sammud

1. Ekspertide kinnitus ülaltoodud küsimustele; vajadusel uuenda `oks.catalog.UNITS` / `EXTRA_INVALID` ja käivita `python -m oks analyse --sensitivity`, `report`, `site`.
2. Pikaajaline jälgitavus: andmete uuenemisel ainult `aggregate` + `analyse` + `site`; toorandmeid ei hoita.
3. Võimalik täiendus: sama analüüs `eval = FALSE` kihtidele; seisundiklasside vahe algsetel klassidel (A–F) (juba `klassid`-tabelis, `Teenuse detail` → „Algsel seisundiskaalal”).
4. Kui avaldamine avalikult: kontrolli ELME/KAUR andmete litsents ja viited.
