# Metoodika v2: teise etapi tööplaan ja seis

Kontrollnimekiri täisjooksu ja teise etapi jaoks. Iga samm märgitakse tehtuks alles siis, kui selle kontroll on läbitud ja muudatus on töö harule salvestatud. Otsused on failis `docs/metoodika_v2_otsused.md`.

| # | Samm | Valmis, kui | Kontroll | Seis |
|---|---|---|---|---|
| 1 | Täisjooksu agregeerimine: kõik rastrid (`oks aggregate`) ja vektorid (`oks fields`) | Kõigil kihtidel on `plokid/<id>.parquet`, `__cls`, `__hist`, `__val/`, `__blkmed` | `pipeline.done()` on tõene kõigil hinnatavatel kihtidel | tehtud: 35/35 kihti (rastrid 1 h 51 min, vektorid 15 min) |
| 2 | `report.py`: tulemuste dokument mediaanidega | `docs/tulemused.md` näitab mediaane ja mediaanipõhist Δ | testid, ruff, mypy | tehtud (kontrollitud piloodi tulemustel) |
| 3 | Metoodikate võrdlus (v1 → v2) saidi jaotisena ja CSV-na | `vordlus.json`, jaotis „Metoodika võrdlus“ | saidi ehitus, brauserikontroll | kood valmis (`oks.vordlus`, `scripts/vordle_metoodikad.py`, jaotis `compare.js`), täisjooksu CSV-d `data/tulemused/vordlus_*.csv` loodud; sait ehitatud ja brauseris kontrollitud (JS-vigu 0, telefonilaius ilma horisontaalse kerimiseta) |
| 4 | Avaldamine: v1 (commit `5aa4596`) peaaadressil, v2 aadressil `/v2/` | `pages.yml` ehitab mõlemad; v1 muutmata, v2 ainult otselingiga (`noindex`) | töövoo kuiv jooks kohapeal | tehtud: kuiv jooks läbis (mõlemad lehed, Exceli ja CSV allalaadimine testitud) |
| 5 | Analüüs: `oks analyse` (põhijooks) | `data/tulemused/paarid.parquet` jt mediaaniveergudega | kõigi kihtide read olemas | tehtud: 34 kihti, 4 180 paari (67 min, mälu ≤ 3 GB) |
| 6 | Tulemustabelid: `oks kaasnev` | `kaasnev_*.parquet` mediaanidega | read olemas, pindalad v1-ga samad | tehtud: 34 kihti (v1: 31), pindalad v1-ga identsed (152 rida, 0 erinevust) |
| 7 | Tundlikkus: `oks analyse --sensitivity` | `data/tulemused/tundlikkus.csv` (mediaanipõhine) | 5 varianti × 2 taset | tehtud (60 min): säilinud olulised 90–100 % (ökosüsteem), 86–100 % (alam) |
| 8 | Kontrollskriptid: mediaanide sõltumatu ümberarvutus, ruff-vigade parandus | `valideeri_*.py` töötavad, 0 lahknevust | `ruff check .` roheline | tehtud: täisjooksul V1–V8 ja veebikontroll V8–V10 0 lahknevust (V8 ühiku/tüübi mediaanid 28 kihil, 6 suurima sagedustabeliga kihti jäetud mälu tõttu välja; paaritatud Δ kõigil 34 kihil); `ruff check .` roheline |
| 9 | Dokumentatsioon: `metoodika.md`, `keskmiste_arvutus.md` (v1 märge), `README.md`, genereeritud `docs/*.md` | tekstid vastavad v2-le | käsitsi läbivaatus | tehtud: käsitsi dokumendid ja genereeritud `docs/tulemused.md`, `andmekataloog.md` (`oks report`) |
| 10 | Lõppkontroll ja lõpparuanne | kõik testid, kontrollskriptid, sait, `git diff --stat 5aa4596..HEAD` vastab nimekirjale | lõpparuanne | tehtud: [metoodika_v2_lopparuanne.md](metoodika_v2_lopparuanne.md) |
