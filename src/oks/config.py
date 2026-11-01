"""Projekti konstandid ja teed."""

from __future__ import annotations

from pathlib import Path

#: Metoodika versioon (v1 = commit 5aa4596, v2 = commit de7aca9, v3 = kuivad ja märjad metsad statistilises analüüsis).
METHOD_VERSION = "v3"

#: Arhiivi baas-URL (CloudFront). Kataloogilisting on HTML-indeks.
ARCHIVE_BASE = "https://d549q4t3lqrx1.cloudfront.net"
ARCHIVE_ROOT = "/arhiiv/"

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
DERIVED = ROOT / "data" / "derived"
BLOCKS = DERIVED / "plokid"
RESULTS = ROOT / "data" / "tulemused"
DOCS = ROOT / "docs"

#: Analüüsiploki külg meetrites (EPSG:3301, joondatud 1000 m ruudustikule).
BLOCK_M = 1000
#: Spatiaalse bootstrapi klastri külg plokkides (10 km).
CLUSTER_BLOCKS = 10

#: Baaskaardi failid (kõik 5 m, EPSG:3301, ühine ruudustik).
BAAS_DET = "Baaskaart/OS_det_seisund_det_2022_5m.tif"
BAAS_ALAM = "Baaskaart/OS_detailne_2022_5m.tif"
BAAS_UNI = "Baaskaart/seisund_uldine_2022_5m.tif"

#: seisund_uldine väärtused (tuletatud andmetest, vt docs/metoodika.md).
STATE_NAMES: dict[int, str] = {1: "hea", 2: "keskmine", 3: "vilets"}
