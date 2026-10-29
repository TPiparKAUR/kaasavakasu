"""Dokumentatsiooni genereerimine tulemustabelitest (arvud ei ole käsitsi kirjutatud)."""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from . import catalog, config, kaasnev_export, nouded, stats

log = logging.getLogger(__name__)


def _md_table(rows: list[list[object]], head: list[str]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    return "\n".join(out)


def _pct(x: float | None, d: int = 0) -> str:
    return "–" if x is None or x != x else f"{x * 100:+.{d}f} %".replace(".", ",")


def _fmt(x: float | None) -> str:
    if x is None or x != x:
        return "–"
    a = abs(x)
    s = f"{x:,.0f}" if a >= 1000 else f"{x:.1f}" if a >= 10 else f"{x:.2f}" if a >= 1 else f"{x:.3f}"
    return s.replace(",", " ").replace(".", ",")


def write_catalogue(out_csv: Path, out_md: Path) -> pl.DataFrame:
    """Kirjuta ``data/teenused.csv`` ja ``docs/andmekataloog.md`` (ametlik tabel + arhiiv)."""
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    cat.drop("abstract", "keywords", "Unnamed: 0", strict=False).write_csv(out_csv)
    ev = catalog.evaluated(cat).sort(["grupp", "nimi"])
    inv = pl.read_csv(config.ROOT / "data/arhiiv_failid.csv").filter(~pl.col("tee").str.ends_with(".aux.xml"))
    matched = set(cat["fail"].drop_nulls().to_list())
    lines = [
        "# Andmekataloog",
        "",
        "Genereeritud `oks.report.write_catalogue`-ga failidest `alusmaterjalid/metaandmed/layer_definition_checked_vrs2.xlsx` ja `data/arhiiv_failid.csv`.",
        "",
        f"Ametlikus tabelis on {cat.height} kihti, neist `eval = TRUE`: {cat.filter(pl.col('eval')).height} (1 baaskaart + {ev.height} teenust).",
        "",
        "## Analüüsitavad teenused (`eval = TRUE`)",
        "",
    ]
    rows = [
        [
            r["grupp"],
            r["nimi"],
            r["id"],
            r["tyyp"],
            r["spatial_resolution"] or "",
            r["vaartuse_tuup"] or "",
            r["omadus"] or "",
            r["uhik"] or "–",
            r["data_origin"] or "",
            r["fail"] or "puudub arhiivis",
        ]
        for r in ev.iter_rows(named=True)
    ]
    lines.append(
        _md_table(
            rows,
            [
                "Grupp",
                "Nimi",
                "Kihi id",
                "Tüüp",
                "Eraldusvõime (m)",
                "Väärtuse tüüp",
                "Omadus",
                "Ühik (tabelist)",
                "Allikas",
                "Fail arhiivis",
            ],
        )
    )
    lines += ["", "## Märkused kihtide kohta (ametlikust tabelist ja kontrollidest)", ""]
    for r in ev.iter_rows(named=True):
        notes = [x for x in (r["markus"], f"Tabeli märkus: {r['comments']}" if r["comments"] else "") if x]
        if notes:
            lines.append(f"* **{r['nimi']}** (`{r['id']}`): " + " · ".join(notes))
    lines += [
        "",
        "## Arhiivi failid, mida ametlikus tabelis ei ole",
        "",
        *[f"* `{t}`" for t in inv["tee"] if t not in matched],
        "",
        "## `eval = FALSE` kihid, mis on arhiivis (analüüsist väljas)",
        "",
        f"{cat.filter(~pl.col('eval') & (pl.col('tyyp') != 'puudub')).height} kihti; täielik loetelu on `data/teenused.csv` (`eval` = FALSE, `tyyp` != puudub).",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return cat


def write_results(results: Path, out_md: Path) -> None:
    """Kirjuta ``docs/tulemused.md`` (arvud tulemustabelitest)."""
    p = pl.read_parquet(results / "paarid.parquet")
    diag = pl.read_parquet(results / "diagnostika.parquet")
    units = pl.read_parquet(results / "uhikud.parquet")
    par = pl.read_csv(results / "parameetrid.csv").row(0, named=True)
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    nm = dict(zip(cat["id"], cat["nimi"], strict=True))
    un = dict(zip(cat["id"], cat["uhik"], strict=True))
    econame = {
        r["unit_code"]: r["nimi"]
        for r in units.filter(pl.col("unit_level") == "okosusteem").iter_rows(named=True)
    }
    lowres = kaasnev_export.LOW_RES_LAYERS
    L: list[str] = [
        "# Tulemuste kokkuvõte",
        "",
        "Genereeritud `oks.report.write_results`-ga failist `data/tulemused/paarid.parquet`. Meetod: [metoodika.md](metoodika.md). Metoodika v2: hinnangud põhinevad täpsetel pikslimediaanidel (otsused: [metoodika_v2_otsused.md](metoodika_v2_otsused.md)).",
        "",
    ]

    n_layers = p["layer_id"].n_unique()
    L += [
        "## 1. Ulatus",
        "",
        f"* {n_layers} teenust, {p['unit_code'].n_unique()} ökosüsteemi/alamökosüsteemi üksust (taseme kaupa), {p.height} seisundipaari hinnangut.",
        f"* Parameetrid: klaster {par['cluster_blocks']}×{par['cluster_blocks']} km, {par['n_boot']} bootstrapi, min {str(par['min_area_ha']).replace('.', ',')} ha, FDR α = {str(par['alpha']).replace('.', ',')}.",
        "",
    ]
    rows = []
    for level, label in (("okosusteem", "Ökosüsteem"), ("alam", "Alamökosüsteem")):
        d = p.filter(pl.col("unit_level") == level)
        em = d.filter(pl.col("enough_m"))
        eu = d.filter(pl.col("enough_u"))
        rows.append(
            [
                label,
                d.height,
                em.height,
                int(em["oluline_m_med"].sum() or 0),
                eu.height,
                int(eu["oluline_u_med"].sum() or 0),
                int(d["kooskolas_med"].sum() or 0),
            ]
        )
    L += [
        _md_table(
            rows,
            [
                "Tase",
                "Hinnanguid",
                "Paaritatud: piisavalt andmeid",
                "…neist olulisi (q<0,05)",
                "Paaritamata: piisavalt andmeid",
                "…neist olulisi",
                "Oluline mõlemal ja sama märk",
            ],
        ),
        "",
    ]

    # 2. ökosüsteemi tase: suund ja olulisus
    L += ["## 2. Ökosüsteemide tase: mitu teenust muutub seisundi paranedes", ""]
    L.append(
        "Paaritatud hinnang mediaanide põhjal, ainult hinnangud, kus on piisavalt andmeid. „Kasvab” = Δ > 0 ja q < 0,05; „väheneb” = Δ < 0 ja q < 0,05."
    )
    L.append("")
    rows = []
    e = p.filter((pl.col("unit_level") == "okosusteem") & pl.col("enough_m"))
    for code, name in econame.items():
        for pair in stats.PAIR_NAMES:
            d = e.filter((pl.col("unit_code") == code) & (pl.col("pair") == pair))
            if d.is_empty():
                continue
            up = d.filter(pl.col("oluline_m_med") & (pl.col("delta_m_med") > 0)).height
            dn = d.filter(pl.col("oluline_m_med") & (pl.col("delta_m_med") < 0)).height
            rows.append([name, pair.replace("→", " → "), d.height, up, dn, d.height - up - dn])
    L += [
        _md_table(rows, ["Ökosüsteem", "Seisundipaar", "Teenuseid", "Kasvab", "Väheneb", "Ei ole oluline"]),
        "",
    ]

    # 3. suurimad muutused (vilets -> hea)
    L += [
        "## 3. Suurimad muutused (vilets → hea, paaritatud mediaanide põhjal, olulised)",
        "",
        "„Mediaan vilets/hea“ on kogu ökosüsteemi pikslite mediaan. Δ on samas 1 km plokis ja alamökosüsteemis arvutatud mediaanide vahede kaalutud keskmine, seega võib Δ erineda kahe mediaani vahest (nt mõlemad mediaanid 0, kuid plokkide sees on erinevus).",
        "",
    ]
    for code, name in econame.items():
        d = e.filter(
            (pl.col("unit_code") == code)
            & (pl.col("pair") == "vilets→hea")
            & pl.col("oluline_m_med")
            & pl.col("rel_m_med").is_not_null()
            & pl.col("rel_m_med").is_not_nan()
        )
        if d.is_empty():
            continue
        top = d.sort("rel_m_med", descending=True)
        sel = pl.concat([top.head(4), top.tail(4)]).unique("layer_id", maintain_order=True)
        rows = [
            [
                nm[r["layer_id"]],
                un[r["layer_id"]] or "–",
                _fmt(r["median_a"]),
                _fmt(r["median_b"]),
                _fmt(r["delta_m_med"]),
                _pct(r["rel_m_med"]),
                f"{_fmt(r['ci_m_med_lo'])} … {_fmt(r['ci_m_med_hi'])}",
                "madalam lahutusvõime" if r["layer_id"] in lowres else "",
            ]
            for r in sel.iter_rows(named=True)
        ]
        L += [
            f"### {name}",
            "",
            _md_table(
                rows, ["Teenus", "Ühik", "Mediaan vilets", "Mediaan hea", "Δ", "Δ %", "95 % CI (Δ)", "Märkus"]
            ),
            "",
        ]

    # 3b. segumudel (võrdluseks madalama lahutusvõimega kihtidele)
    segf = results / "paarid_segumudel.parquet"
    seg = pl.read_parquet(segf) if segf.exists() else pl.DataFrame()
    mix = (
        seg.filter((pl.col("unit_level") == "okosusteem") & (pl.col("pair") == "vilets→hea"))
        if not seg.is_empty()
        else seg
    )
    L += [
        "### Võrdluseks: segumudel (930 m rastrid ja 1 km vektorruudud)",
        "",
        "Need kihid on madalama lahutusvõimega kui seisundiüksus. Põhihinnang tuleb 10 m lahutusvõimele viidud kihist (ülal); segumudel (klasside pindalaosade lineaarne mudel, keskmisel põhinev, **uuriv**) on võrdluseks. Näidatud on kõik ökosüsteemid (vilets → hea), sõltumata olulisusest.",
        "",
    ]
    rows = [
        [
            nm[r["layer_id"]],
            econame[r["unit_code"]],
            un[r["layer_id"]] or "–",
            _fmt(r["mean_a"]),
            _fmt(r["mean_b"]),
            _pct(r["rel_m"]),
            f"{_fmt(r['ci_m_lo'])} … {_fmt(r['ci_m_hi'])}",
            "jah" if r["oluline_m"] else "ei",
        ]
        for r in mix.sort("layer_id", "unit_code").iter_rows(named=True)
    ]
    L += [
        _md_table(
            rows, ["Teenus", "Ökosüsteem", "Ühik", "β vilets", "β hea", "Δ %", "95 % CI (Δ)", "Oluline"]
        )
        if rows
        else "Puuduvad.",
        "",
    ]

    # 4. paaritatud vs paaritamata
    both = p.filter(
        pl.col("enough_m")
        & pl.col("enough_u")
        & pl.col("delta_m_med").is_not_null()
        & pl.col("delta_u_med").is_not_null()
    )
    opp = both.filter(
        pl.col("oluline_m_med")
        & pl.col("oluline_u_med")
        & (pl.col("delta_m_med").sign() != pl.col("delta_u_med").sign())
    )
    L += [
        "## 4. Paaritatud ja paaritamata hinnang",
        "",
        f"* Võrreldavaid hinnanguid: {both.height}; sama märgiga: {both.filter(pl.col('delta_m_med').sign() == pl.col('delta_u_med').sign()).height} "
        f"({both.filter(pl.col('delta_m_med').sign() == pl.col('delta_u_med').sign()).height / max(both.height, 1) * 100:.0f} %).",
        f"* Mõlemal hinnangul olulised, kuid **vastupidise märgiga**: {opp.height} (nende puhul muudab asukoha/koosseisu kontroll järelduse suunda).",
        "",
    ]
    if opp.height:
        rows = [
            [
                nm[r["layer_id"]],
                econame.get(r["unit_code"], str(r["unit_code"]))
                if r["unit_level"] == "okosusteem"
                else f"alam {r['unit_code']}",
                r["pair"].replace("→", " → "),
                _fmt(r["delta_m_med"]),
                _fmt(r["delta_u_med"]),
            ]
            for r in opp.sort("layer_id").head(25).iter_rows(named=True)
        ]
        L += [_md_table(rows, ["Teenus", "Üksus", "Seisundipaar", "Δ paaritatud", "Δ paaritamata"]), ""]

    # 5. mudelipõhisus
    L += [
        "## 5. Mudelipõhisus (η² ≥ 0,9)",
        "",
        "Kihid ja ökosüsteemid, kus ≥ 90 % pikslitaseme dispersioonist on seletatav baaskaardi klassiga. Muutus seisundi vahel on neil osaliselt definitsiooniline.",
        "",
    ]
    dd = diag.filter(pl.col("eta2_det").is_not_nan() & (pl.col("eta2_det") >= 0.9))

    def _eta(x: float | None) -> str:
        return "–" if x is None or x != x else f"{x:.2f}".replace(".", ",")

    rows = [
        [nm[r["layer_id"]], econame[r["eco_code"]], _eta(r["eta2_det"]), _eta(r["eta2_state_in_alam"])]
        for r in dd.sort("layer_id", "eco_code").iter_rows(named=True)
    ]
    L += [
        _md_table(rows, ["Teenus", "Ökosüsteem", "η² (klass)", "η² (seisund alamökosüsteemi sees)"])
        if rows
        else "Puuduvad.",
        "",
    ]

    # 6. tundlikkus
    sens = results / "tundlikkus.csv"
    if sens.exists():
        s = pl.read_csv(sens)
        L += [
            "## 6. Tundlikkus",
            "",
            "Põhijooksu olulistest hinnangutest (paaritatud) säilis oluliseks sama märgiga:",
            "",
        ]
        rows = [
            [
                r["variant"],
                r["unit_level"],
                r["voordluses"],
                r["pohijooksu_olulisi"],
                r["sailinud_olulised"],
                _pct(r["sailinud_osa"]),
                r["uusi_olulisi"],
                f"{r['spearman_delta']:.3f}".replace(".", ",") if r["spearman_delta"] is not None else "–",
            ]
            for r in s.iter_rows(named=True)
        ]
        L += [
            _md_table(
                rows,
                [
                    "Variant",
                    "Tase",
                    "Võrreldavaid",
                    "Põhijooksu olulisi",
                    "Säilinud",
                    "Säilinud %",
                    "Uusi olulisi",
                    "Spearman ρ (Δ)",
                ],
            ),
            "",
        ]
        L += [
            "Variandid: `klaster5km`, `klaster20km` (bootstrap-klastri suurus), `ala_0_25ha`, `ala_4ha` (minimaalne ala stratumis), `seeme_2` (teine juhuslik seeme).",
            "",
        ]
    out_md.write_text("\n".join(L), encoding="utf-8")


def write_requirements(out_md: Path) -> None:
    """Kirjuta ``docs/lahteulesanne.md``: nõuete täitmine, kriitika ja avatud küsimused (``nouded``)."""
    icon = {nouded.DONE: "✅", nouded.PART: "🟡", nouded.WAIT: "⏳", nouded.TODO: "⬜"}
    cnt = {s: sum(1 for r in nouded.REQUIREMENTS if r["staatus"] == s) for s in icon}
    lines = [
        "# Lähteülesande täitmine ja kriitiline hinnang",
        "",
        "Generaator: `python -m oks report` (sisu allikas `src/oks/nouded.py`; sama sisu on veebilehel vahekaardil "
        "„Lähteülesande täitmine“).",
        "",
        "Allikad: (1) *LTK kaasneva kasu hindamise lähteülesanne* (Kliimaministeerium; edaspidi **lähteülesanne**, "
        "nõuded L1–L15) ja (2) *LTK kaasneva kasu analüüsi kvantitatiivne analüüs, lähtekas* (Keskkonnaagentuur; "
        "edaspidi **lähtekas**, nõuded K1–K10). Lähteülesanne hõlmab ka kvalitatiivset osa; lähtekas on "
        "selle kvantitatiivse osa täpsustus.",
        "",
        "## Kokkuvõte",
        "",
        " · ".join(f"{icon[s]} {s}: {cnt[s]}" for s in icon),
        "",
        "* **Täidetud** on kogu kvantitatiivne osa (tüüp × seisund, suured ökosüsteemid, pindala, nullid, ei paku, rannik) ning "
        "Excel-andmetabel ja veebileht.",
        "* **Ootel** on kõik, mis eeldab Kliimaministeeriumi kinnitatud meetmete nimekirja (tegevuspõhine tabel, "
        "otsese ja kaudse mõju eristus, meetmepõhine võrreldavus).",
        "* **Osaliselt** on kvalitatiivne osa: teenuste kaupa raamistik ja andmepõhine tõendus on olemas; ajaraam, ulatus, "
        "lävendid ja CICES rühmad on ettepanekud, mida eksperdid ei ole valideerinud.",
        "",
        "## Nõuete täitmine",
        "",
        _md_table(
            [
                [r["id"], r["nouue"], f"{icon[r['staatus']]} {r['staatus']}", r["kus"], r["kommentaar"]]
                for r in nouded.REQUIREMENTS
            ],
            ["", "Nõue", "Seis", "Kus", "Kommentaar"],
        ),
        "",
        "## Kriitilised tähelepanekud",
        "",
    ]
    for i, (t, tx) in enumerate(nouded.CRITIQUE, start=1):
        lines += [f"{i}. **{t}.** {tx}", ""]
    lines += ["## Avatud küsimused", ""]
    lines += [f"{i}. {q}" for i, q in enumerate(nouded.QUESTIONS, start=1)]
    lines += [
        "",
        "## Ajakava",
        "",
        "Lähteülesande järgi: KLIMi meetmete nimekiri augustis → esialgne versioon KLIMile tagasisideks → parandused → "
        "lõppraport ja andmetabel **4. novembril 2026**.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
