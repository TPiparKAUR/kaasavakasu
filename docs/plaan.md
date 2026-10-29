# Plaan: ökosüsteemiteenuste muutus seisundiklasside vahel

Koostatud 2026-10-19. Plaani täitmise seis on lõpus. See on algne plaan (metoodika v1, keskmised); kehtiv metoodika v2 (täpsed
pikslimediaanid) on kirjeldatud failides [metoodika.md](metoodika.md) ja [metoodika_v2_otsused.md](metoodika_v2_otsused.md).

## 1. Eesmärk

Mõista, **kui palju ja kuidas** muutuvad ökosüsteemiteenused ühe ökosüsteemi või alamökosüsteemi sees,
kui seisund liigub klasside **vilets → keskmine → hea** vahel, ja kas muutus on **statistiliselt oluline**.
Tulemus on (1) dokumenteeritud analüüs ja (2) interaktiivne veebileht filtritega.

## 2. Sisendandmed ja ulatus

| Allikas | Sisu |
|---|---|
| `https://d549q4t3lqrx1.cloudfront.net/arhiiv/` | 105 andmefaili (rastrid 5/10/930 m, GeoPackage'id), ~43,6 GB. Inventuur: `data/arhiiv_failid.csv` |
| `alusmaterjalid/metaandmed/layer_definition_checked_vrs2.xlsx` | Ametlik kihtide tabel (136 kihti); **`eval = TRUE` = 32 kihti** (1 baaskaart + 31 teenust). Analüüsitakse need |
| Baaskaart 2022 (5 m, EPSG:3301) | `OS_det_seisund_det` (detailne tüüp + algne seisund, 263 klassi), `OS_detailne` (62 alamökosüsteemi tüüpi), `seisund_uldine` (ühtlustatud seisund) |

Ulatus (31 teenust): 25 rastrit ≤ 10 m (põhianalüüs), 2 rastrit 930 m (eraldi käsitlus),
3 vektorfaili (eraldi käsitlus, sest tabeli märkus on „Eraldi käsitlus”).
`eval = FALSE` kihid ja metaandmeteta failid jäävad välja ning on loetletud `docs/andmekataloog.md`-s.

## 3. Analüüsiüksused

* **Ökosüsteem**: rohumaad, sood, metsad, põllumaad (kood `kood // 10000`). Rannikud ning asustus ja muu on „seisundita”.
* **Alamökosüsteem**: `OS_detailne` tüüp (62 koodi; nt „6410 sinihelmikaniidud”, „Salumets”), ainult need, millel on ≥ 2 seisundit.
* **Seisund**: `seisund_uldine` 1 = hea, 2 = keskmine, 3 = vilets (tabeli kirjelduse ja täisresolutsiooni ristiksi alusel; 4, 5 = hindamata/määramata).
* **Võrdlused**: vilets → keskmine, keskmine → hea, vilets → hea (Δ = parem − halvem).

## 4. Meetod (kokkuvõte; täpne kirjeldus `docs/metoodika.md`)

1. **Ruumiline ühildamine**: baaskaart taasproovitakse teenuse ruudustikule lähima naabriga (teenuseid ei interpoleerita).
2. **Agregeerimine**: pikslid → 1 km plokid × detailne klass: n, Σx, Σx². Toorrastrid ei jää kettale.
3. **Hinnangud**: pindalakaalutud keskmine, absoluutne ja suhteline muutus.
4. **Paaritatud võrdlus (peamine)**: samas 1 km plokis ja samas alamökosüsteemis kõrvuti esinevad seisundid. See kontrollib asukoha ja koosseisu mõju.
5. **Paaritamata võrdlus (täiendav)**: kõik plokid koos; ökosüsteemi tasemel on see toorhinnang (koosseisu mõju sees).
6. **Statistiline olulisus**: 10 km klastri-bootstrap (arvestab ruumilist autokorrelatsiooni), Benjamini–Hochbergi FDR; lisaks Wilcoxon / Mann–Whitney ja Cliffi δ kontrolliks.
7. **Tundlikkus**: klastri suurus 5/20 km, minimaalne ala, sentinel-väärtused.
8. **Diagnostika**: kui suure osa kihi varieeruvusest seletab klass ise (η²) – see eristab mõõdetud ruumilist varieeruvust mudelipõhisest tabelväärtusest.

## 5. Kvaliteedikontrollid (kohustuslikud)

* Baaskaardi kontroll: `OS_detailne == OS_det_seisund_det // 100 * 100` (0 erandit), seisund on detailse koodi funktsioon (264 koodi, 0 erandit).
* Pindala: plokitabeli pindala vs täisresolutsiooni baaskaart (erinevus < 0,05 %).
* Täisarvude ületäitumine (Int32 summa), NoData/sentinel, aastate erinevus (2020 vs 2022), ühikud iga kihi kohta.
* Ringlus: kihid, mille väärtus on baaskaardi klassi otsene tabelväärtus (η² ≈ 1), märgitakse.

## 6. Tulemused

* Parquet/CSV/JSON: `data/tulemused/`.
* Veebileht: `site/` (staatiline; filtrid: ökosüsteem, alamökosüsteem, teenusegrupp, teenus, omadus, seisundipaar, olulisus, minimaalne muutus).
* Dokumentatsioon: `README.md`, `docs/`.

## 7. Seis

Täitmise seis on kirjas failis [`docs/seis.md`](seis.md).
