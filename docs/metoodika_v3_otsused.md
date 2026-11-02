# Metoodika v3: kokkulepitud otsused

Metoodika v3 lisab statistilisse analüüsi kuivad ja märjad metsad samale tasemele suurte ökosüsteemidega. v2 hinnanguid ei
muudeta. Täiendused on näha ainult v3 veebilehel (`/v3/`). Analüüs ja alternatiivid on failis
[metoodika_v3_v4_ettepanek.md](metoodika_v3_v4_ettepanek.md).

Võrdlusalus on metoodika v2, commit `de7aca9`. Metoodika v1 on commit `5aa4596`.

## Rühmad (K1)

* **Kuivad metsad (kood 31):** salumets, palumets, laanemets, loomets, nõmmemets.
* **Märjad metsad (kood 32):** soovikumets, samblasoomets, rohusoomets, kõdusoomets, rabastuv mets.
* „Muu (metsa)kooslus“ (31100, 31200) ei kuulu kumbagi rühma. See on ainult kogu metsa hinnangus.
* Jaotus on alamökosüsteemi (kasvukohatüübi) järgi, mitte praeguse veerežiimi järgi. Näiteks kõdusoomets on kuivendatud
  turvasmullal, kuid kuulub märgade metsade hulka.
* Definitsioon on ühes kohas (`oks.ruhmad.GROUPS`). Sama definitsiooni kasutab tulemustabel (`kaasnev.FOREST_SPLIT`), mis
  sisaldas kuivi ja märgi metsi juba v2-s.

## Hinnangud

* **Paaritatud hinnang:** rühma alamökosüsteemide stratumite (1 km plokk × alamökosüsteem) mediaanide erinevuste kaalutud
  keskmine. Kaal on `n_a·n_b/(n_a+n_b)`. Arvutus on sama mis v2 ökosüsteemi tasemel: samad funktsioonid, samad stratumid,
  sama bootstrap (10 km klastrid, B = 4 000, sama seeme) ja samad piisavuse lävendid. Ainult koondatavate stratumite hulk on
  kitsam.
* **Metsa hinnang** on kuiva metsa, märja metsa ja muu koosluse stratumite koondhinnang. See ei ole kahe rühma lihtkeskmine
  ega pindalakaalutud keskmine.
* **Paaritamata hinnang:** rühma ja seisundi täpne pikslimediaan klasside ühendist. Nagu ökosüsteemi tasemel on see
  toorhinnang, sest rühma sees on seisundite alamökosüsteemide koosseis erinev.
* **Plokimediaanid** plokk × rühm × seisund arvutatakse sagedustabelist (`ruhmad.block_medians`). Reegel on sama mis v2
  plokimediaanidel.
* **Paaritatud tasemed (K9):** kõigil tasemetel salvestatakse lisaks halvema ja parema seisundi plokimediaanide kaalutud
  keskmine samades paarides (`level_a_m_med`, `level_b_m_med`) ja kaalude summa (`sum_w_m_med`). Need on v4 tulemustabeli
  paaritatud vaate jaoks. Kehtib `level_b − level_a = delta_m_med`.

## Mitmene testimine (K2)

Benjamini–Hochbergi FDR-parandus tehakse iga taseme sees eraldi: ökosüsteemid, alamökosüsteemid ja metsarühmad on igaüks oma
grupp. Seetõttu on v2 ökosüsteemi ja alamökosüsteemi q-väärtused ning olulisuse märked v3-s samad.

## Muud otsused

* **K3:** kuiva ja märja metsa erinevust omavahel ei testita.
* **K5:** tundlikkusanalüüs (5 ja 20 km klastrid, 0,25 ja 4 ha, teine seeme) hõlmab ka rühmi.
* **K12:** η² (mudelipõhisuse märk) on rühmadel kogu metsa väärtus.
* **Segumudel** (madalama lahutusvõimega kihtide uuriv võrdlus) on endiselt ainult ökosüsteemi tasemel.

## Tulemused ja kontroll

* Kõik tasemed arvutatakse ühe jooksuga (`oks analyse`) ning tulemused (`data/tulemused`) sisaldavad taset `ruhm`.
* Plokitabelid arvutati v3 jaoks arhiivist uuesti, v2 koodiga.
* `scripts/vordle_v2.py` võrdleb v3 tulemuste ökosüsteemi ja alamökosüsteemi ridu v2 tulemustega (git, `de7aca9`). Nõue on, et
  erinevusi ei ole. See kontrollib ühtlasi, et kogu ahel on nullist reprodutseeritav.
* `scripts/valideeri_ruhmad.py` kontrollib rühmade sisemist kooskõla. Kontrollid on nummerdatud V-R2…V-R7:
  * metsa hinnangu lagunemine rühmadeks;
  * paaride arv;
  * vastavus tulemustabeli mediaanidega;
  * jaotused;
  * paaritatud tasemed;
  * FDR-grupp.
* Analüüsi käigus kontrollib `analysis.run` iga kihi juures, et rühmajooksu alamökosüsteemi read võrduvad põhijooksu omadega.

## Versioonid ja tagasiminek

* `/` = v1 (commit `5aa4596`), `/v2/` = v2 (commit `de7aca9`). Mõlemad ehitatakse oma kindlast commit'ist ja v3 neid ei
  muuda.
* `/v3/` = vaikeharu seis.
* **Tagasi v2-le:** `git revert <v3 commit>` ja push. Kood ja tulemusfailid on siis täpselt v2 omad ning `/v3/` kaob
  järgmise Pages-ehitusega.
