# Metoodika v2: teise etapi tööplaan ja seis

Kontrollnimekiri täisjooksu ja teise etapi jaoks. Iga samm märgitakse tehtuks alles siis, kui selle kontroll on läbitud ja muudatus on töö harule salvestatud. Otsused on failis `docs/metoodika_v2_otsused.md`.

| # | Samm | Valmis, kui | Kontroll | Seis |
|---|---|---|---|---|
| 1 | Täisjooksu agregeerimine: kõik rastrid (`oks aggregate`) ja vektorid (`oks fields`) | Kõigil kihtidel on `plokid/<id>.parquet`, `__cls`, `__hist`, `__val/`, `__blkmed` | `pipeline.done()` on tõene kõigil hinnatavatel kihtidel | |
| 2 | `report.py`: tulemuste dokument mediaanidega | `docs/tulemused.md` näitab mediaane ja mediaanipõhist Δ | testid, ruff, mypy | tehtud (kontrollitud piloodi tulemustel) |
| 3 | Metoodikate võrdlus (v1 → v2) saidi jaotisena ja CSV-na | `vordlus.json`, jaotis „Metoodika võrdlus“ | saidi ehitus, brauserikontroll | kood valmis (`oks.vordlus`, `scripts/vordle_metoodikad.py`, jaotis `compare.js`), kontrollitud piloodi andmetel; CSV-d luuakse pärast sammu 6 |
| 4 | Avaldamine: v1 (commit `5aa4596`) peaaadressil, v2 aadressil `/v2/` | `pages.yml` ehitab mõlemad, v1-l on lingiga märge | töövoo kuiv jooks kohapeal | |
| 5 | Analüüs: `oks analyse` (põhijooks) | `data/tulemused/paarid.parquet` jt mediaaniveergudega | kõigi kihtide read olemas | |
| 6 | Tulemustabelid: `oks kaasnev` | `kaasnev_*.parquet` mediaanidega | read olemas, pindalad v1-ga samad | |
| 7 | Tundlikkus: `oks analyse --sensitivity` | `data/tulemused/tundlikkus.csv` (mediaanipõhine) | 5 varianti × 2 taset | |
| 8 | Kontrollskriptid: mediaanide sõltumatu ümberarvutus, ruff-vigade parandus | `valideeri_*.py` töötavad, 0 lahknevust | `ruff check .` roheline | |
| 9 | Dokumentatsioon: `metoodika.md`, `keskmiste_arvutus.md` (v1 märge), `README.md`, genereeritud `docs/*.md` | tekstid vastavad v2-le | käsitsi läbivaatus | |
| 10 | Lõppkontroll ja lõpparuanne | kõik testid, kontrollskriptid, sait, `git diff --stat 5aa4596..HEAD` vastab nimekirjale | lõpparuanne | |
