# Metoodika v2: kokkulepitud otsused

Selles dokumendis on kirjas, mida ja miks muudeti, kui tulemustabelites ja seisundite võrdluses mindi keskmiselt üle täpsele mediaanile. Vana metoodika (v1) on vaikeharus commit'is `5aa4596`.

## Statistik

* **Täpne pikslimediaan lisatakse kõikjale, kus seni oli keskmine.** Iga piksel on üks vaatlus ja valimisse kuuluvad kõik valimi pikslid. Paarisarvu korral võetakse kahe keskmise väärtuse keskmine. Tühja valimi korral on tulemus NaN. Mediaan arvutatakse kadudeta sagedustabelist, kus iga erinev väärtus on eraldi rida koos täpse pikslite arvuga. Histogrammilist ega ligikaudset mediaani ei kasutata.
* **Keskmine jääb andmetesse alles.** Tabelites näidatakse peamise väärtusena mediaani. Keskmist kasutatakse seal, kus mediaan ei ole sisuliselt õige:
  * stsenaariumi muutus pindala kohta, sest mediaan korda pindala ei ole koguhulk;
  * dispersioonipõhised näitajad (η², SD).
* **Klassirühma (tüüp, suur ökosüsteem, kokku-read) mediaan** arvutatakse kõigi rühma pikslite pealt korraga, mitte klasside mediaanidest.
* **Nullist erinevate pikslite mediaan** on lisanäitaja. Veebilehel saab seda vaadata märkeruuduga „Ilma täpsete nullideta“.

## Valim

* **Rastri NoData loetakse kehtivaks nulliks**, kui all on baaskaardi kood.
* **Erandid:** järgmistes kihtides jäetakse NoData valimist välja, sest NoData tähendab puuduvat hinnangut, mitte teenuse puudumist. Veebilehel on need kihid märgitud erandina.
  * `mustikad_pohlad_saagikus_2020_10m`
  * `mustikad_pohlad_hind_2022_10m`
  * `pohlad_saagikus_2020_10m`
  * `kasemahl_saagikus_2020_10m` ja `kasemahl_hind_2022_10m`. Kihi kirjelduse järgi andmed soo- ja kõdusoometsades puuduvad. Lisatud pärast pilootjooksu.
* **Teenuse ruudustikust väljapoole jäävad baaskaardi pikslid** loetakse NoData-ks ja seega nulliks (erandkihtides jäävad need välja). Ruudustikku laiendatakse samas võrgustikus. Joondamise loogika (EPSG:3301, lähim naaber, piksli keskpunkt) ei muutu.
* **NaN** rastris: Float32 kihtides NaN-e ei ole (kontrollitud kõigil 10 ujukomakihil).

## Vektorid

* **Rasterdamise reeglid:**
  * polügoonist väljas on 0;
  * NULL on 0;
  * −1 on 0;
  * NoData on 0;
  * kattuvate polügoonide korral võetakse maksimum.
* **Diagnostikakiht** `toiduteenus_2022__vaartusklass` järgib samu reegleid.
* **`lamm_grd1000_am_drained_2022`** rasterdatakse 10 m lahutusvõimele. Väli `lammide_taastamise_kulu` on EUR/ha/a, seega väärtust ei skaleerita.

## Madalama lahutusvõimega kihid

* **930 m rastrid ja 1 km ruudustik** viiakse baaskaardi 10 m lahutusvõimele lähima naabriga ja arvutatakse samamoodi nagu teised kihid.
* Veebilehel on märge: seisundite erinevus tuleb ainult algsete ruutude vahelistest erinevustest.
* **Segumudel** (keskmisel põhinev, uuriv) jääb võrdluseks alles ja ei muutu.

## Seisundite võrdlus

* **Paaritatud hinnang:** stratumi (1 km plokk × alamökosüsteem) erinevus on parema ja halvema seisundi mediaanide vahe. Stratumite koondamine (kaalutud keskmine, kaal `n_a·n_b/(n_a+n_b)`) ja 10 km klastrite bootstrap jäävad samaks.
* **Paaritamata hinnang:** ühiku mediaanide vahe. Ebakindlus arvutatakse sama klastribootstrapiga (B = 4000, sama seeme ja samad kaalud). Iga korduse mediaan on täpne.
* **Plokitasandi näitajad** (Mann-Whitney, kastide kvartiilid) arvutatakse plokimediaanidest. Lisaks on samad näitajad nullist erinevate pikslite kohta.
* **Tundlikkusanalüüs** (5 km ja 20 km klastrid, 0,25 ha ja 4 ha miinimumpindala, teine seeme) arvutatakse uuesti mediaanipõhise paaritatud hinnangu järgi.

## Veebileht

* **v1 sait** jääb esialgu peaaadressile muutmata kujul ja see ehitatakse commit'ist `5aa4596`. **v2 sait** avaldatakse aadressil `/v2/` ainult otselingiga (v1 lehel viidet ei ole, `noindex`); avalikkuse tase on sama mis v1-l (2026-10-29 otsus). Pärast kinnitamist vahetatakse: v2 läheb peaaadressile ja v1 aadressile `/v1/`.
* Võrdlusjaotis näitab muutust kahes osas: valimireeglite mõju ja statistiku vahetuse mõju.
* Kuumkaardil saab suhtelise muutuse asemel vaadata muutust kihi ühikutes (biofüüsikalised või rahalised).

## Muudatuste haldus

* Kõik muudatused on töö harus `claude/nifty-bohr-4eqjct`. Vaikeharu muutub ainult siis, kui ühendamine on kinnitatud. Ühendamisel kasutatakse „Squash and merge“ valikut, et kogu muudatuse saaks ühe sammuga tagasi võtta.
