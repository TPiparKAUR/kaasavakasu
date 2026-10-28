# Ökosüsteemiteenuste muutus seisundiklasside vahel

Analüüs ja interaktiivne veebileht küsimusele: **kui palju ja kuidas muutuvad ökosüsteemiteenused ühe ökosüsteemi või alamökosüsteemi sees, kui seisund liigub klasside vilets → keskmine → hea vahel, ja kas muutus on statistiliselt oluline.**

Allikas: ELME kihtide arhiiv (`https://d549q4t3lqrx1.cloudfront.net/arhiiv/`, baaskaart 2022) ja ametlik kihtide tabel (`eval = TRUE` kihid, 31 teenust).

| Dokument | Sisu |
|---|---|
| [docs/plaan.md](docs/plaan.md) | Eesmärk, ulatus, plaan |
| [docs/metoodika.md](docs/metoodika.md) | Meetod, eeldused, piirangud, valideerimine |
| [docs/metoodika_v2_otsused.md](docs/metoodika_v2_otsused.md) | Metoodika v2 (mediaanid, NoData = 0) otsused ja põhjendused |
| [docs/tulemused.md](docs/tulemused.md) | Tulemuste kokkuvõte (genereeritud tulemustabelitest) |
| [docs/andmekataloog.md](docs/andmekataloog.md) | Analüüsitavad kihid, ühikud, märkused, arhiivi failid |
| [docs/seis.md](docs/seis.md) | Seis, avatud küsimused, järgmised sammud |

## Mida töö sisaldab

Töö täidab Kliimaministeeriumi looduse taastamise kava (LTK) kaasneva kasu hindamise lähteülesande kvantitatiivse osa ja
koostab kvalitatiivse osa raamistiku (`docs/lahteulesanne.md`: nõuded, seis, kriitika, avatud küsimused).

* **Tulemustabel** (lähtekas): teenuse mediaan (metoodika v2; keskmine kõrval) iga ökosüsteemitüübi ja seisundi (hea / keskmine / vilets)
  kohta, pindala ha, suurte ökosüsteemide (mets, soo, niit, põld, rannik) mediaanid; Excel `andmetabel_kaasneva_kasu.xlsx`.
* **Stsenaariumi kalkulaator:** tüüp + seisundi muutus + pindala → muutus teenuste kaupa.
* **Kvalitatiivne raamistik:** teenuste kaupa CICES sektsioon, suund, tugevuse ettepanek, ajaraam, topeltarvestus, ebakindlus;
  tegevuste koondtabeli mall (13 veergu).
* **Statistiline analüüs:** seisundite erinevuse paaritatud hinnang, olulisus, jaotused (algsed vaated on alles).

## Veebileht

* Ehitatud sait: `uv run python -m oks site --out site` → `site/index.html` (vajab veebiserverit, nt `python -m http.server -d site`) ja ühefailne `site/oks-seisund.html` (avaneb otse failina).
* Filtrid: ökosüsteem, alamökosüsteem, teenusegrupp, omadus, teenus, seisundipaar, hinnang (paaritatud/paaritamata), olulisus, minimaalne muutus. Põhijaotused: avaleht, tulemustabel, stsenaarium, kvalitatiivne, statistiline analüüs, lähteülesande täitmine, metoodika võrdlus (v1 → v2), meetod. Statistilise analüüsi vaated: kuumkaart, teenuse detail (sh **väärtuste jaotus** seisundi kaupa), profiil (keskmised), **jaotused** (kõik teenused ühes üksuses), **kihtide ülevaade** (kõigi kihtide väärtuste jaotus seisundi koosseisuga), tabel (CSV), meetod.
* Disain: seisundid on hallikas punane–kollane–roheline (vilets–keskmine–hea), muutuse suund oranž–sinine; printsiibid ja kolleegi graafiku analüüs on failis [`docs/disain.md`](docs/disain.md).
* Ei kasuta välisteeke ega väliseid päringuid; toetab hele/tume teema, klaviatuuri ja mobiili.

## GitHub Pages

Töövoog `.github/workflows/pages.yml` ehitab saidi igal pushil ja avaldab selle **repo vaikeharust**. Peaaadressil on metoodika v1 leht
(ehitatud commit'ist `5aa4596`, ülal märge ja link v2-le), metoodika v2 leht on aadressil `…/v2/`.

1. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions** (ühekordne).
2. Push vaikeharusse või **Actions → Veebileht → Run workflow**. Valmis aadress: `https://<kasutaja>.github.io/<repo-nimi>/` (praegu repo `kaasavakasu`: `https://tpiparkaur.github.io/kaasavakasu/`).
3. Kui deploy keeldub haru tõttu: **Settings → Environments → github-pages → Deployment branches** lisa vaikeharu.

Repo nime saab muuta: **Settings → General → Repository name**. Pages-aadress muutub nime järgi (vana aadress ei suuna ümber);
git-remote'i saab uuendada käsuga `git remote set-url origin <uus-url>`. Sait kasutab suhtelisi teid, seega töötab igal aadressil.

## Käivitamine

```bash
uv sync                                  # Python 3.12, uv
uv run pytest -q                         # 77 testi (sünteetilised andmed teadaoleva vastusega)
uv run ruff check . && uv run mypy src

# Täielik uuesti arvutus (vajab ligipääsu arhiivi hostile; ~ 2–3 h, laeb ~ 25 GB, kustutab toorfailid)
uv run python -m oks aggregate           # kõik rastrid (930 m -> 10 m) -> data/derived/plokid/ (sh sagedustabelid)
uv run python -m oks fields              # vektorid (põllumassiivid, lamm) -> rasteriseeritud -> plokid
uv run python -m oks analyse --sensitivity
uv run python -m oks kaasnev             # tulemustabelid (tüüp x seisund)
uv run python scripts/vordle_metoodikad.py   # v1 -> v2 võrdlus
uv run python -m oks report              # docs/tulemused.md, docs/andmekataloog.md
uv run python -m oks site --out site
```

Tulemustabelid (`data/tulemused/`) on repositooriumis, nii et sait ehitub ilma toorandmeteta.
Toorrastreid, plokitabeleid ja sagedustabeleid (`data/cache`, `data/derived/plokid`) ei hoita; need on taastatavad ülaltoodud käskudega.

## Kataloog

```
src/oks/          analüüsikood (baas, aggregate, stats, mixing, analysis, export, report, sitebuild)
site_src/         veebilehe lähtekood (HTML, CSS, JS; ilma sõltuvusteta)
tests/            pytest
data/tulemused/   tulemustabelid (Parquet/CSV)
data/derived/     baaskaardi klassitabelid ja täisresolutsiooni ristiks
data/teenused.csv, data/arhiiv_failid.csv   kihtide kataloog ja arhiivi inventuur
alusmaterjalid/   ametlik kihtide tabel (xlsx/csv) ja baaskaardi .aux.xml (klassinimed)
docs/             dokumentatsioon
```

## Olulised piirangud (täpsemalt [docs/metoodika.md](docs/metoodika.md))

* Tulemus kirjeldab **seoseid**, mitte põhjuslikku mõju.
* Osa teenuste kihte on arvutatud baaskaardi klassi/seisundi põhjal (nt kliimaregulatsioon, kahjuritõrje, toiduteenus); nende puhul on seisundi mõju osaliselt definitsiooniline (lehel märgitud η²-nurgamärgi ja märgiga †).
* 930 m rastrid ja 1 km vektorruudud on viidud 10 m lahutusvõimele (märgitud „madalam lahutusvõime“); uuriv segumudel on võrdluseks.
* NoData loetakse nulliks (teenust ei ole), v.a erandkihid mustikad/pohlad ja kasemahl, kus NoData tähendab „hindamata“.
* Ühikud on loetud ametlikust kihitabelist; kus tabel ühikut ei nimeta, on see tühi.
* Andmete kasutustingimused tuleb kontrollida enne taasavaldamist.
