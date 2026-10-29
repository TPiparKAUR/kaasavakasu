"""Excel-andmetabel Kliimaministeeriumile (lähteülesande „andmetabel“): kvantitatiivsed tulemused,
kvalitatiivne raamistik ja tegevuste koondtabeli mall.

Kasutab ``xlsxwriter`` (ainult kirjutamiseks; pakett on pure-Python ja ainus uus sõltuvus Exceli väljundiks).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import xlsxwriter
from xlsxwriter.format import Format
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from . import kaasnev

#: Tegevuste koondtabeli veerud (lähteülesanne, „Töö vormistatakse raporti ning andmetabeli kujul“).
ACTIVITY_COLUMNS: list[tuple[str, str, list[str] | None]] = [
    ("Meede või tegevus", "Kliimaministeeriumi kinnitatud nimekirja kood ja nimetus", None),
    (
        "Mõjutatav ökosüsteem",
        "Maismaa / mere / linna / jõed ja järved; täpsemalt ELME2 ökosüsteemitüüp",
        None,
    ),
    (
        "Mõjutatav loodushüve või ökosüsteemiteenus",
        "CICES v5.1 hierarhia järgi (varustav / reguleeriv ja säilitav / kultuuriline)",
        None,
    ),
    (
        "Mõju suund",
        "Positiivne, negatiivne, neutraalne või ebaselge",
        ["positiivne", "negatiivne", "neutraalne", "ebaselge"],
    ),
    ("Mõju tugevus", "Nõrk, keskmine, tugev (lävendid kokku leppida)", ["nõrk", "keskmine", "tugev"]),
    (
        "Ajaline avaldumine",
        "Lühiajaline, keskpikk, pikaajaline (aastapiirid kokku leppida)",
        ["lühiajaline", "keskpikk", "pikaajaline"],
    ),
    ("Mõju ulatus", "Lokaalne, regionaalne, üleriigiline", ["lokaalne", "regionaalne", "üleriigiline"]),
    ("Biofüüsikaline näitaja", "Väärtus ja ühik (nt Δ t C/ha tüübi kohta)", None),
    (
        "Rahaline väärtus",
        "Ainult kui metoodiliselt põhjendatav; EUR/ha ja ajaühik (varu või aastane voog)",
        None,
    ),
    (
        "Kasutatavus otseses kulu-kasu võrdluses",
        "Jah / osaliselt / ei (põhjendus märkuses)",
        ["jah", "osaliselt", "ei"],
    ),
    (
        "Kasutatud meetod ja andmeallikas",
        "nt ELME maastikuandmete analüüs (kihi id), teaduskirjandus, eksperthinnang",
        None,
    ),
    ("Topeltarvestuse risk", "Madal / keskmine / kõrge ja millega kattub", ["madal", "keskmine", "kõrge"]),
    (
        "Ebakindlus",
        "Andmete, mudeli ja eelduste ebakindlus (sh seisundi ja teenuse definitsiooniline seos)",
        None,
    ),
    ("Märkus sotsiaalmajandusliku mõju hindajale", "Mida tuleb arvestada võrdlemisel ja summeerimisel", None),
]


def _fmt(wb: Workbook) -> dict[str, Format]:
    return {
        "h": wb.add_format(
            {
                "bold": True,
                "bg_color": "#22303c",
                "font_color": "#ffffff",
                "text_wrap": True,
                "valign": "top",
                "border": 1,
            }
        ),
        "h2": wb.add_format(
            {"bold": True, "bg_color": "#e8edf1", "text_wrap": True, "valign": "top", "border": 1}
        ),
        "u": wb.add_format(
            {"italic": True, "bg_color": "#f4f6f8", "font_color": "#52514e", "border": 1, "text_wrap": True}
        ),
        "txt": wb.add_format({"text_wrap": True, "valign": "top"}),
        "b": wb.add_format({"bold": True}),
        "num": wb.add_format({"num_format": "#,##0.0##"}),
        "int": wb.add_format({"num_format": "#,##0"}),
        "part": wb.add_format({"num_format": "#,##0.0##", "italic": True, "bg_color": "#f8f1da"}),
        "mix": wb.add_format({"num_format": "#,##0.0##", "bg_color": "#e9e7f4"}),
        "none": wb.add_format({"font_color": "#8b8a84", "align": "center"}),
        "hea": wb.add_format({"bg_color": "#cfe3d3"}),
        "keskmine": wb.add_format({"bg_color": "#f3e7b8"}),
        "vilets": wb.add_format({"bg_color": "#efc9c5"}),
        "grey": wb.add_format({"bg_color": "#eceae5"}),
        "title": wb.add_format({"bold": True, "font_size": 14}),
    }


def _state_fmt(f: dict[str, Format], state: str) -> Format | None:
    return (
        f.get(state)
        if state in ("hea", "keskmine", "vilets")
        else (f["grey"] if state in ("määramata", "hindamata") else None)
    )


def _wide(
    ws: Worksheet, f: dict[str, Format], data: dict[str, Any], rows: list[list[Any]], kind: str
) -> None:
    layers = data["kihid"]
    inds = {i["key"]: i for i in data["indikaatorid"]}
    first = 4 if kind == "tuubid" else 3
    ws.freeze_panes(3, first)
    heads = (
        ["Ökosüsteem", "Tüüp", "Seisund", "Pindala (ha)"]
        if kind == "tuubid"
        else ["Ökosüsteem", "Seisund", "Pindala (ha)"]
    )
    for c, t in enumerate(heads):
        ws.merge_range(0, c, 2, c, t, f["h"])
    c = first
    k = 0
    while k < len(layers):
        j = k
        while j + 1 < len(layers) and layers[j + 1]["ind"] == layers[k]["ind"]:
            j += 1
        name = inds[layers[k]["ind"]]["nimi"]
        if j > k:
            ws.merge_range(0, c + k, 0, c + j, name, f["h"])
        else:
            ws.write(0, c + k, name, f["h"])
        for m in range(k, j + 1):
            lay = layers[m]
            roll = {"bio": "biofüüsikaline", "raha": "rahaline", "lisa": "lisakiht"}[lay["roll"]]
            flags = (
                (" ‡ madalam lahutusvõime" if lay["madal_lahutus"] else "")
                + (" § erandkiht" if lay["nodata_valja"] else "")
                + (" † definitsiooniline" if lay["definitsiooniline"] else "")
            )
            ws.write(1, c + m, f"{lay['nimi']} [{roll}]{flags}", f["h2"])
            ws.write(2, c + m, lay["uhik"] or "ühik dokumenteerimata", f["u"])
        k = j + 1
    ws.set_row(0, 30)
    ws.set_row(1, 92)
    for r, row in enumerate(rows, start=3):
        if kind == "tuubid":
            ok, _alam, tuup, _uld, seis, area, cells = row
            vals: list[Any] = [data["eco"][str(ok)], tuup, seis, area]
        else:
            ok, seis, area, cells = row
            vals = [data["suured_nimed"].get(str(ok), data["eco"].get(str(ok), "")), seis, area]
        sf = _state_fmt(f, seis)
        for c, v in enumerate(vals):
            if c == len(vals) - 1:
                ws.write_number(r, c, v or 0, f["int"])
            else:
                ws.write(r, c, v, sf if c == len(vals) - 2 else None)
        for m, cell in enumerate(cells):
            col = first + m
            if cell is None:
                continue
            med, mean, kate, _esineb, st = cell[:5]
            status = data["staatused"][st]
            if status == kaasnev.STATUS_NONE:
                ws.write(r, col, "ei paku", f["none"])
            elif status == kaasnev.STATUS_MISSING or med is None:
                ws.write(r, col, "–", f["none"])
            elif status == kaasnev.STATUS_PARTIAL:
                ws.write_number(r, col, med, f["part"])
                ws.write_comment(
                    r,
                    col,
                    f"Osaline kate: kehtivaid pikslitest {kate * 100:.0f} %; mediaan kehtib katvale osale. Keskmine {mean}.",
                )
            else:
                ws.write_number(r, col, med, f["num"])
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 36 if kind == "tuubid" else 22)
    ws.set_column(2, 2, 12 if kind == "tuubid" else 14)
    ws.set_column(3, 3, 13)
    ws.set_column(first, first + len(layers), 17)
    ws.autofilter(2, 0, 2 + len(rows), first + len(layers) - 1)


def write(
    path: Path,
    data: dict[str, Any],
    tuup_long: pl.DataFrame,
    suured_long: pl.DataFrame,
    evidence: pl.DataFrame,
    params: dict[str, Any],
    koostatud: str,
) -> Path:
    """Kirjuta Exceli andmetabel.

    Parameters
    ----------
    path
        Sihtfail (``.xlsx``).
    data
        ``kaasnev_export.build_json`` tulemus (``kaasnev.json`` sisu).
    tuup_long, suured_long
        Pikad tabelid (``kaasnev.type_state``/``big_classes``).
    evidence
        ``kaasnev_export.evidence`` tulemus.
    params
        Analüüsi parameetrid (``parameetrid.csv``).
    koostatud
        Koostamise kuupäev (ISO 8601).
    """
    wb = xlsxwriter.Workbook(str(path), {"nan_inf_to_errors": False})
    f = _fmt(wb)

    ws = wb.add_worksheet("Loe mind")
    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 110)
    ws.write(0, 0, "LTK kaasneva kasu analüüs: kvantitatiivne andmetabel", f["title"])
    lines = [
        (
            "Koostatud",
            f"{koostatud}; töövahend: https://github.com/TPiparKAUR/kaasavakasu (kood, andmed, dokumentatsioon)",
        ),
        (
            "Staatus",
            "ESIALGNE versioon KLIMi tagasisideks; ekspertide kinnitus puudub. Hinnangulised veerud on ettepanekud.",
        ),
        (
            "Päritolu",
            "Kõik väärtused on ELME/ELME2 kaardikihtide (modelleeritud kihid, mitte mõõtmised) pikslitaseme mediaanid ökosüsteemitüübi ja seisundiklassi kaupa (metoodika v2). Keskmised on lehtedel „Pikk tabel“. Seisund: ELME2 baaskaart (2022, 5 m; originaal, mitte metsaseisundi parandatud versioon).",
        ),
        (
            "Mediaani määratlus",
            "Väärtus on täpne pikslimediaan KOGU klassi pindala kohta, nullid kaasa arvatud: pooled pikslid on sellest väiksemad, pooled suuremad. Iga piksel on üks vaatlus. Kihi NoData loetakse nulliks, kui all on baaskaardi ökosüsteem; erandid on mustikate-pohlade, pohlade ja kasemahla kihid, kus NoData tähendab puuduvat hinnangut ja jäetakse välja. Põllukihtides on põldudest väljas olev ala 0. Keskmine (pindalaga summeerimiseks) on lehtedel „Pikk tabel“.",
        ),
        (
            "„ei paku“",
            f"Teenus on tüübis nii väike (nullist erinevaid piksleid alla {params['positiivse_osa_lävi'] * 100:.0f} % kehtivatest), et loetakse mitte pakkuvaks (lähtekas: „väga-väga vähe“). Lävi on parameeter.",
        ),
        (
            "„–“",
            f"Teenust ei hinnatud: kehtivaid piksleid alla {params['kate_min'] * 100:.0f} % klassi pikslitest (kiht ei kata seda tüüpi).",
        ),
        (
            "Kaldkiri ja kollane",
            f"Osaline kate: kehtivaid piksleid alla {params['kate_taielik'] * 100:.0f} %; väärtus kehtib katvale osale.",
        ),
        (
            "‡ madalam lahutusvõime",
            "Kihi lahutusvõime on 930 m või 1 km. Arvutuseks on see viidud baaskaardi 10 m lahutusvõimele; seisundite erinevus tuleb ainult algsete ruutude vahelistest erinevustest.",
        ),
        (
            "† definitsiooniline",
            "Kihi väärtus on tuletatud seisundist või baaskaardi klassist; seisundite erinevus on osaliselt definitsiooniline ega ole iseseisev tõend.",
        ),
        (
            "Pindala",
            "Baaskaardi pindala (5 m piksel = 25 m²) hektarites; suurte ökosüsteemide mediaan on arvutatud kõigi nende pikslite pealt korraga. Mets on jagatud ka kuivadeks (salu-, palu-, laane-, loo-, nõmmemets) ja märjaks metsaks (soovikumets, sambla-, rohu-, kõdusoomets, rabastuv mets).",
        ),
        (
            "Seisundid",
            "hea / keskmine / vilets: ELME2 seisund_uldine 1/2/3 (kinnitatud lähtekasus); määramata = 4 (soo, niit, mets, põld, kus seisundit ei määratud); hindamata = 5 (rannikud, asustus ja muu). „Asustus ja muu“ ei ole liidetud.",
        ),
        (
            "Rahalised väärtused",
            "Ära summeeri teenuseid: osa rahalisi kihte on riigi aastase kogusumma ruumiline jaotus (virgestus, loodusturism, õhusaaste), osa on varu (süsinik) ja osa aastane voog. Vt lehti „Teenuste kirjeldus“ ja „Kvalitatiivne“.",
        ),
        (
            "Litsents",
            "ELME/KAUR andmete kasutustingimused tuleb enne taasavaldamist kontrollida (selles töös ei ole litsentsi kinnitatud).",
        ),
    ]
    for i, (a, b) in enumerate(lines, start=2):
        ws.write(i, 0, a, f["b"])
        ws.write(i, 1, b, f["txt"])

    _wide(wb.add_worksheet("Tüübid × seisund"), f, data, data["tuubid"], "tuubid")
    _wide(wb.add_worksheet("Suured ökosüsteemid"), f, data, data["suured"], "suured")

    ws = wb.add_worksheet("Pikk tabel (tüübid)")
    _long(
        ws,
        f,
        tuup_long,
        [
            "okosusteem",
            "tuup",
            "seisund_nimi",
            "pindala_ha",
            "layer_id",
            "n_valid",
            "n_total",
            "kate",
            "esineb_osa",
            "median",
            "median_nz",
            "mean",
            "sd",
            "staatus",
        ],
    )
    ws = wb.add_worksheet("Pikk tabel (suured)")
    _long(
        ws,
        f,
        suured_long,
        [
            "okosusteem",
            "seisund_nimi",
            "pindala_ha",
            "layer_id",
            "n_valid",
            "n_total",
            "kate",
            "esineb_osa",
            "median",
            "median_nz",
            "mean",
            "sd",
            "staatus",
        ],
    )

    ws = wb.add_worksheet("Teenuste kirjeldus")
    heads = [
        "Indikaator",
        "Kiht (id)",
        "Nimi",
        "Roll",
        "Ühik",
        "Omadus",
        "Eraldusvõime (m)",
        "Aasta",
        "Märkus",
        "Tabeli märkus",
        "Definitsiooniline",
        "Madalam lahutusvõime",
        "Erandkiht (NoData välja)",
        "Lisakiht",
    ]
    for c, t in enumerate(heads):
        ws.write(0, c, t, f["h"])
    ind_name = {i["key"]: i["nimi"] for i in data["indikaatorid"]}
    for r, x in enumerate(data["kihid"], start=1):
        for c, v in enumerate(
            [
                ind_name[x["ind"]],
                x["id"],
                x["nimi"],
                x["roll"],
                x["uhik"],
                x["omadus"],
                x["res"],
                x["aasta"],
                x["markus"],
                x["tabeli_markus"],
                "jah" if x["definitsiooniline"] else "",
                "jah" if x["madal_lahutus"] else "",
                "jah" if x["nodata_valja"] else "",
                "jah" if x["lisakiht"] else "",
            ]
        ):
            ws.write(r, c, v if v is not None else "", f["txt"])
    ws.set_column(0, 2, 34)
    ws.set_column(3, 7, 14)
    ws.set_column(8, 9, 60)
    ws.freeze_panes(1, 3)

    ws = wb.add_worksheet("Kvalitatiivne (ettepanek)")
    heads = [
        "Indikaator",
        "CICES sektsioon",
        "CICES rühm (ettepanek)",
        "Väärtuse tüüp",
        "Suund",
        "Ajaline raamistik (ettepanek)",
        "Ulatus (ettepanek)",
        "Äärmuslikud ilmastikunähtused",
        "Rahalise väärtuse meetod",
        "Kasutatavus kulu-kasu võrdluses",
        "Topeltarvestuse risk",
        "Ebakindlus",
        "Märkus sotsiaalmajandusliku mõju hindajale",
        "Kihid",
    ]
    for c, t in enumerate(heads):
        ws.write(0, c, t, f["h"])
    for r, i in enumerate(data["indikaatorid"], start=1):
        suund = (
            "suurem väärtus = suurem hüve"
            if i["suund"] == "suurem_parem"
            else "VÄIKSEM väärtus = suurem hüve"
        )
        for c, v in enumerate(
            [
                i["nimi"],
                i["sektsioon"],
                i["grupp"],
                i["tuup"],
                suund,
                i["ajaraam"],
                i["ulatus"],
                i["ekstreem"],
                i["raha_meetod"],
                i["kulukasu"],
                i["topelt"],
                i["ebakindlus"],
                i["markus"],
                ", ".join(i["kihid"]),
            ]
        ):
            ws.write(r, c, v, f["txt"])
    ws.set_column(0, 0, 34)
    ws.set_column(1, 13, 28)
    ws.set_row(0, 30)
    ws.freeze_panes(1, 1)

    ws = wb.add_worksheet("Tõendusbaas (Δ)")
    cols = [
        "tase",
        "uksus",
        "indikaator",
        "kiht",
        "paar",
        "hinnang",
        "delta",
        "rel",
        "oluline",
        "q",
        "hyve_suund",
        "tugevus",
        "paare",
    ]
    _long(
        ws,
        f,
        evidence.select([c for c in cols if c in evidence.columns]) if not evidence.is_empty() else evidence,
        cols,
    )

    ws = wb.add_worksheet("Tegevuste koondtabel (mall)")
    for c, (name, hint, opts) in enumerate(ACTIVITY_COLUMNS):
        ws.write(0, c, name, f["h"])
        ws.write(1, c, hint, f["u"])
        if opts:
            ws.data_validation(2, c, 500, c, {"validate": "list", "source": opts})
    ws.set_column(0, len(ACTIVITY_COLUMNS) - 1, 26)
    ws.set_row(0, 48)
    ws.set_row(1, 76)
    ws.freeze_panes(2, 1)
    ws.write(
        3,
        0,
        "Täitmist ootab Kliimaministeeriumi kinnitatud meetmete ja tegevuste nimekiri (lähteülesanne: augustis). Tõendusbaas on lehtedel „Tõendusbaas (Δ)“ ja „Kvalitatiivne (ettepanek)“.",
        f["txt"],
    )
    wb.close()
    return path


def _long(ws: Worksheet, f: dict[str, Format], df: pl.DataFrame, cols: list[str]) -> None:
    cols = [c for c in cols if c in df.columns]
    for c, name in enumerate(cols):
        ws.write(0, c, name, f["h"])
    for r, row in enumerate(df.select(cols).iter_rows(), start=1):
        for c, v in enumerate(row):
            if v is None:
                continue
            if isinstance(v, bool):
                ws.write(r, c, "jah" if v else "ei")
            elif isinstance(v, float) and v != v:
                continue
            else:
                ws.write(r, c, v)
    ws.set_column(0, len(cols) - 1, 18)
    ws.freeze_panes(1, 0)
    if cols:
        ws.autofilter(0, 0, max(1, df.height), len(cols) - 1)
