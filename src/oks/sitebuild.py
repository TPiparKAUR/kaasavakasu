"""Veebilehe ehitus: ``site_src/`` + tulemused -> ``site/`` (kaustana ja ühe failina)."""

from __future__ import annotations

import base64
import json
import re
import shutil
from pathlib import Path

from . import andmetabel, config, export, kaasnev_export

#: ``site_src/sections`` failid ``app.js`` märgendi ``/*@@SECTIONS@@*/`` asemele (samas sulundis).
SECTION_FILES = ("common.js", "home.js", "results.js", "scenario.js", "quality.js", "brief.js", "compare.js")
DATA_FILES = (
    "meta",
    "paarid",
    "lahtrid",
    "klassid",
    "jaotused",
    "kaasnev",
    "tendus",
    "nouded",
    "algklassid",
    "segumudel",
    "vordlus",
)
XLSX_NAME = "andmetabel_kaasneva_kasu.xlsx"


def assemble_js(src: Path) -> str:
    """``app.js`` koos jaotiste failidega (üks sulundiga skript)."""
    core = (src / "app.js").read_text(encoding="utf-8")
    parts = [(src / "sections" / f).read_text(encoding="utf-8") for f in SECTION_FILES]
    return core.replace("/*@@SECTIONS@@*/", "\n".join(parts))


def build(out: Path, results: Path | None = None) -> Path:
    """Ehita staatiline sait ``out``-i.

    Loob ``out/index.html`` (+ ``styles.css``, ``app.js``, ``data/*.json``, Exceli andmetabel) ja ühefailse
    variandi ``out/oks-seisund.html``, mille andmed ja Excel on lehe sisse põimitud (avaneb ka ``file://`` kaudu).

    Parameters
    ----------
    out
        Väljundkaust.
    results
        Tulemuste kaust (vaikimisi ``data/tulemused``).
    """
    results = results or config.RESULTS
    src = config.ROOT / "site_src"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src / "index.html", out / "index.html")
    shutil.copyfile(src / "styles.css", out / "styles.css")
    js = assemble_js(src)
    (out / "app.js").write_text(js, encoding="utf-8")
    export.build_data(results, out / "data", results / "tundlikkus.csv")
    xlsx_uri: str | None = None
    if (results / "kaasnev_tuup_seisund.parquet").exists():
        kdata = kaasnev_export.build_json(results, out / "data")
        xlsx = _write_xlsx(results, out, kdata)
        xlsx_uri = (
            "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,"
            + base64.b64encode(xlsx.read_bytes()).decode("ascii")
        )
    data = {
        n: json.loads((out / "data" / f"{n}.json").read_text(encoding="utf-8"))
        for n in DATA_FILES
        if (out / "data" / f"{n}.json").exists()
    }
    html = (src / "index.html").read_text(encoding="utf-8")
    css = (src / "styles.css").read_text(encoding="utf-8")
    single = out / "oks-seisund.html"
    single.write_text(_inline(html, css, js, {**data, "xlsx": xlsx_uri or False}), encoding="utf-8")
    (out / "oks-seisund-artifact.html").write_text(
        _artifact_variant(_inline(html, css, js, {**data, "xlsx": False})), encoding="utf-8"
    )
    return single


def _inline(html: str, css: str, js: str, payload: dict[str, object]) -> str:
    """Põimi CSS, JS ja andmed ühte HTML-i."""
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    return html.replace(
        '<script src="app.js"></script>', f"<script>window.__OKS__={blob};</script>\n<script>{js}</script>"
    )


def _write_xlsx(results: Path, out: Path, kdata: dict[str, object]) -> Path:
    """Kirjuta Exceli andmetabel (``out/andmetabel_kaasneva_kasu.xlsx``)."""
    import polars as pl

    params = dict(kdata["parameetrid"])  # type: ignore[call-overload]
    meta = json.loads((out / "data" / "meta.json").read_text(encoding="utf-8"))
    return andmetabel.write(
        out / XLSX_NAME,
        kdata,
        pl.read_parquet(results / "kaasnev_tuup_seisund.parquet"),
        pl.read_parquet(results / "kaasnev_suured.parquet"),
        kaasnev_export.evidence(results),
        params,
        meta["koostatud"],
    )


def _artifact_variant(html: str) -> str:
    """Muuda ühefailne leht artefakti-platvormi sisuks (ilma ``html/head/body`` siltideta)."""
    title = re.search(r"<title>.*?</title>", html, re.S)
    head = re.search(r"<head>(.*?)</head>", html, re.S)
    body = re.search(r"<body>(.*?)</body>", html, re.S)
    if not (title and head and body):
        raise ValueError("Ootamatu HTML-struktuur")
    head_rest = re.sub(
        r"<title>.*?</title>|<meta charset[^>]*>|<meta name=\"viewport\"[^>]*>", "", head.group(1), flags=re.S
    ).strip()
    return f'{title.group(0)}\n<meta name="claude:viewport-fit-sides" content="cover">\n{head_rest}\n{body.group(1).strip()}\n'
