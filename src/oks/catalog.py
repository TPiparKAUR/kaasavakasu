"""Teenuste kataloog: ametlik kihtide tabel (``eval``-lipp) + arhiivi failide inventuur.

Allikas on ``alusmaterjalid/metaandmed/layer_definition_checked_vrs2.xlsx`` (KAUR/ELME).
Analüüsitakse kihte, mille ``eval = TRUE``. Ühikud on loetud tabeli abstraktidest ja
pealkirjadest (veerg ``uhik_allikas``); kus tabel ühikut ei nimeta, on see tühi.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import polars as pl

log = logging.getLogger(__name__)

#: layer_name -> (ühik, tõlgendusmärkus). Ühik pärineb tabeli abstraktist/pealkirjast.
UNITS: dict[str, tuple[str, str]] = {
    "elupaigahuve_pakkumine_2022_10m": ("indeks 0-10", "0 madal, 10 kõrge"),
    "puitne_biomass_c_t_ha_kogu_eesti_sum_2022_5m": ("t C/ha", ""),
    "puitne_biomass_c_t_ha_niit_sum_2022_5m": (
        "t C/ha",
        "Tabeli märkus: 'Üle otsustada. Sõltub kihi metoodika sobivusest'",
    ),
    "puitne_biomass_c_t_ha_soo_sum_2022_5m": ("t C/ha", ""),
    "c_tonn_per_ha_final_2022_10m": (
        "t C/ha",
        "Mulla orgaanilise süsiniku varu; suuremad veekogud, linnad ja >6 m teed eemaldatud",
    ),
    "virgestuse_koondvaartus_eur_ha_2022_5m": (
        "EUR/ha",
        "Aastane kogukulu (320 mln EUR) jaotatud kaalude alusel; astmeline (11 taset)",
    ),
    "virgestuse_koondvaartus_2022_5m": ("skoor", "Ekspertkaalude summa"),
    "loodusturism_eur_ha_2022_5m": ("EUR/ha", "637 mln EUR jaotatud kaalude alusel; astmeline (11 taset)"),
    "loodusturism_kaalsum_2022_5m": ("skoor", "Ekspertkaalude summa"),
    "mustikad_pohlad_saagikus_2020_10m": ("kg/ha", ""),
    "pohlad_saagikus_2020_10m": (
        "kg/ha",
        "Diskreetne; väärtused -1..7, -1 on tabeli järgi kehtiv väärtus (has_negative=1)",
    ),
    "seened_saagikus_2020_10m": ("kg/ha", "58 liigi hinnanguline saagikus"),
    "seened_hind_2022_10m": ("EUR/ha/a", "Kokkuostuhind 4,5 EUR/kg (2022)"),
    "kasemahl_hind_2022_10m": ("EUR/ha", "Kokkuostuhind 0,3 EUR/l"),
    "mustikad_pohlad_hind_2022_10m": ("EUR/ha/a", "Kokkuostuhind 2,5 EUR/kg (2022)"),
    "kasemahl_saagikus_2020_10m": (
        "l/0,01 ha",
        "Soo- ja kõdusoometsades andmed puuduvad; avakooslused väärtusega 0",
    ),
    "kliimaregulatsioon_2022_5m": (
        "suhtarv (klassi põhine)",
        "VÄIKSEM väärtus = ühtlasem temperatuur = parem regulatsioon; arvutatud baaskaardi klassi kohta",
    ),
    "ohusaaste_puhverdusvoime_2022_5m": ("indeks 1-10", "Tabeli märkus: 255 käitub kui 0 (NoData)"),
    "ohusaaste_puhverdusvoime_eur_ha_2022_5m": (
        "EUR/ha",
        "Aastane ärahoitud tervisekulu 20,88 mln EUR jaotatud",
    ),
    "erosioon_p_kg_ha_a_2022_10m": ("kg/ha/a", "Fosfori ärakanne: suurem väärtus = suurem ärakanne"),
    "erosioon_c_kg_ha_a_2022_10m": (
        "kg/ha/a",
        "Orgaanilise süsiniku ärakanne: suurem väärtus = suurem ärakanne",
    ),
    "erosioon_p_eur_ha_a_2022_10m": ("EUR/ha/a", "Fosforikao kulu; suurem väärtus = suurem kulu"),
    "vee_reguleerimisvoime_vol_ha_linnalised_teed_veekogud_2022_10m": ("m3/ha", ""),
    "vee_reguleerimisvoime_eur_ha_linnalised_teed_veekogud_2022_10m": (
        "EUR/ha",
        "Tabeli märkus: 'Rahalise ühiku metoodika vananenud'",
    ),
    "vee_puhastamise_potentsiaal_p_eur_ha_2022_930m": ("EUR/ha", "Ainult kaldapuhvrid; eraldusvõime 930 m"),
    "vee_puhastamise_potentsiaal_p_kg_ha_a_2022_930m": ("kg/ha/a", "Ainult kaldapuhvrid; eraldusvõime 930 m"),
    "okosusteemide_tugi_tolmeldajatele_2022_10m": ("indeks 0-1", ""),
    "biotorje_2022": (
        "arvatavasti % (väli pestits_vahenemine)",
        "Kahjuritõrje vajaduse vähenemine põllumassiivil; arvutatud maastikuelementide katvusest ja põllu seisundiklassist (seos seisundiga on definitsiooniline). Tabeli märkus: 'Kasutada ühte. Eraldi käsitlus'; pestitshind_ha (EUR/ha) on sama muutuja rahas",
    ),
    "toiduteenus_2022": (
        "reaalboniteet (väli boniteet)",
        "RINGLUSE HOIATUS: põllukultuuride seisundiklass A-D langeb baaskaardil kokku selle kihi väärtusklassiga A-D (kontrollitud: keskmine väärtusklass klassides A/B/C/D = 1,0006 / 2,0000 / 3,0000 / 4,0000, SD ~ 0,01), mis on tuletatud samast reaalboniteedist; seos seisundi ja boniteedi vahel on seetõttu osaliselt definitsiooniline. Tabeli märkus: 'Eraldi käsitlus'",
    ),
    "lamm_grd1000_am_drained_2022": (
        "EUR (väli lammide_taastamise_kulu)",
        "1 km ruudustik, ainult lammiruudud (am_osa > 0); väärtus väheneb kuivendatud pindalaga, seos seisundiga kaudne. Uuriv segumudel",
    ),
}

#: Lisaks NoData-le välistatavad väärtused.
EXTRA_INVALID: dict[str, tuple[float, ...]] = {}

#: Väärtused, mis loetakse kehtivaks nulliks (mitte NoData-ks), kui tabelis deklareeritud NoData on 0.
#: Põhjus: lähtekasu loogikakontroll (100 ha palumetsa, millest 25 ha-l kasvavad mustikad: keskmine
#: arvutatakse kogu 100 ha kohta, 75 ha loetakse nulliks). Kihtides, kus tabeli NoData on 0, on 0 ühtlasi
#: „teenust ei ole“ ega ole eristatav puuduvast väärtusest; neist jäetakse teenust mitte pakkuvad
#: klassid välja positiivse osa läve alusel (``POSITIVE_MIN``). Lisaväärtused: tabeli märkus
#: ``ohusaaste_puhverdusvoime_2022_5m``: „255 käitub kui 0“.
ZERO_EXTRA: dict[str, tuple[float, ...]] = {
    "ohusaaste_puhverdusvoime_2022_5m": (255.0,),
}

#: Kihid, mille deklareeritud NoData jäetakse valimist välja. Kõigis teistes rastrites loetakse NoData
#: (ka 255, 65535, -1, -9999, float32 miinimum) kehtivaks nulliks, kui all on baaskaardi kood (metoodika v2).
NODATA_EXCLUDED: frozenset[str] = frozenset(
    {
        "mustikad_pohlad_saagikus_2020_10m",
        "mustikad_pohlad_hind_2022_10m",
        "pohlad_saagikus_2020_10m",
    }
)

#: Lähtekasu (``docs/lahteulesanne.md``) nõuab hindu ja ühte sidusust, mis ei ole tabelis ``eval = TRUE``:
#: mulla süsiniku varu ja puitse biomassi süsiniku rahaline väärtus ning loodusmaastiku sidusus 1 km raadiuses.
BRIEF_EXTRA: dict[str, dict[str, str]] = {
    "mullasusinik_aasta_keskmine_2022_10m": {
        "grupp": "Globaalne kliimaregulatsioon",
        "omadus": "rahaline",
        "uhik": "EUR/ha",
        "markus": "Mulla süsinikuvaru väärtus (varu, mitte aastane voog), ETS 2022 keskmine börsihind 80,68 EUR/t CO2; tabeli märkus: 'Hind kokku leppida'. Lisakiht lähtekasu alusel",
    },
    "mullasusinik_aasta_sotsiaalne_kulu_2022_10m": {
        "grupp": "Globaalne kliimaregulatsioon",
        "omadus": "rahaline",
        "uhik": "EUR/ha",
        "markus": "Mulla süsinikuvaru väärtus (varu, mitte aastane voog), sotsiaalse kulu hind 169,77 EUR/t CO2 (Rennert et al. 2022). Lisakiht lähtekasu alusel",
    },
    "puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m": {
        "grupp": "Globaalne kliimaregulatsioon",
        "omadus": "rahaline",
        "uhik": "EUR/ha",
        "markus": "Metsa puitse biomassi süsinikuvaru väärtus (varu, mitte aastane voog), ETS 80,68 EUR/t CO2. Lisakiht lähtekasu alusel",
    },
    "sidusus_1km_2022_10m": {
        "grupp": "Elupaikade säilitamine",
        "omadus": "muu",
        "uhik": "osakaal 0-100 (tõlgendus kinnitada)",
        "markus": "Loodusmaastiku sidusus 1 km raadiuses: heas seisundis looduslike ökosüsteemide osakaal maismaapikslitest 1 km raadiuses. Lähtekas: 'kasutame ühte sidusust (nt 1 km raadiusega loodusmaastik?)'; raadius ja skaala kinnitada. Tabeli märkus: 'Võib vajada teistsugust lähenemist'. Seos seisundiga on osaliselt definitsiooniline (sidusus arvutatud heas seisundis ökosüsteemide osakaalust)",
    },
}

#: Klass loetakse teenust mitte pakkuvaks, kui positiivse väärtusega pindala osa on väiksem kui see
#: (lähtekas: 'kui mõnda teenust jääb mõnda ökosüsteemitüüpi väga-väga vähe, siis järeldame, et see kooslus ei
#: paku vastavat teenust'). Parameeter, mitte fakt; tulemustabelis on osakaal eraldi veerus.
POSITIVE_MIN = 0.01

#: Kihid, mille seos seisundiga on definitsiooniline: ``toiduteenus_2022`` (põllukultuuride seisundiklass
#: langeb kokku väärtusklassiga, kontrollitud) ja ``biotorje_2022`` (kihi kirjelduse järgi arvutatud põllu
#: seisundiklassist).
DEFINITIONAL: frozenset[str] = frozenset({"toiduteenus_2022", "biotorje_2022"})

GROUP_NAMES: dict[str, str] = {
    "baaskaart": "Baaskaart",
    "bioloogiline_torje": "Bioloogiline tõrje",
    "elupaigahuve": "Elupaikade säilitamine",
    "globaalne_kliimaregulatsioon": "Globaalne kliimaregulatsioon",
    "kultuurilised_huved": "Kultuurilised hüved",
    "loodusannid": "Loodusannid",
    "mikrokliima_regulatsioon": "Mikrokliima reguleerimine",
    "puhverdavad_teenused": "Puhverdavad teenused",
    "toit_soot_pollult": "Toit ja sööt põllult",
    "tolmeldamine": "Tolmeldamine",
}


def build_catalogue(meta_csv: Path, inventory_csv: Path) -> pl.DataFrame:
    """Ühenda ametlik kihtide tabel arhiivi inventuuriga.

    Parameters
    ----------
    meta_csv
        ``layer_definition_checked_vrs2.csv`` (xlsx-i CSV-eksport).
    inventory_csv
        ``data/arhiiv_failid.csv`` (``inventory.write_inventory`` tulemus).

    Returns
    -------
    pl.DataFrame
        Üks rida kihi kohta: ``id`` (= ``layer_name`` väiketähtedena), ``layer_name``,
        ``eval``, ``fail`` (arhiivi tee või null), ``tyyp`` (raster/vektor/puudub) jne.
    """
    meta = pl.read_csv(meta_csv, infer_schema_length=None)
    inv = pl.read_csv(inventory_csv)
    files = inv.filter(~pl.col("tee").str.ends_with(".aux.xml"))
    stem_map: dict[str, str] = {}
    for tee in files["tee"]:
        stem = re.sub(r"\.(tif|gpkg|fgb)$", "", tee.rsplit("/", 1)[-1])
        stem_map.setdefault(stem, tee)
    out = (
        meta.with_columns(
            pl.col("layer_name").str.to_lowercase().alias("id"),
            pl.col("layer_name")
            .map_elements(lambda n: stem_map.get(n), return_dtype=pl.String)
            .alias("fail"),
            pl.col("layer_group").str.strip_suffix("_taiendavad").alias("grupp_kood"),
        )
        .with_columns(
            pl.col("fail").str.ends_with(".tif").alias("_r"),
            pl.col("fail").str.ends_with(".gpkg").alias("_v"),
        )
        .with_columns(
            pl.when(pl.col("_r"))
            .then(pl.lit("raster"))
            .when(pl.col("_v"))
            .then(pl.lit("vektor"))
            .otherwise(pl.lit("puudub"))
            .alias("tyyp"),
            pl.col("grupp_kood")
            .replace_strict(GROUP_NAMES, default=pl.col("grupp_kood"), return_dtype=pl.String)
            .alias("grupp"),
            pl.col("title_unchangeable").str.strip_chars().alias("nimi"),
            pl.col("data_type").alias("vaartuse_tuup"),
            pl.col("properties")
            .str.replace("biofüüsikalinefüüsikaline", "biofüüsikaline")
            .alias("omadus"),  # allikas: kirjaviga
        )
        .drop("_r", "_v")
    )
    units = {k.lower(): v for k, v in UNITS.items()}
    out = out.with_columns(
        pl.col("id").map_elements(lambda i: units.get(i, ("", ""))[0], return_dtype=pl.String).alias("uhik"),
        pl.col("id")
        .map_elements(lambda i: units.get(i, ("", ""))[1], return_dtype=pl.String)
        .alias("markus"),
    )
    extra = BRIEF_EXTRA
    return out.with_columns(
        pl.when(pl.col("id").is_in(list(extra)))
        .then(
            pl.col("id").replace_strict(
                {k: v["grupp"] for k, v in extra.items()}, default="", return_dtype=pl.String
            )
        )
        .otherwise(pl.col("grupp"))
        .alias("grupp"),
        pl.when(pl.col("id").is_in(list(extra)))
        .then(
            pl.col("id").replace_strict(
                {k: v["omadus"] for k, v in extra.items()}, default="", return_dtype=pl.String
            )
        )
        .otherwise(pl.col("omadus"))
        .alias("omadus"),
        pl.when(pl.col("id").is_in(list(extra)))
        .then(
            pl.col("id").replace_strict(
                {k: v["uhik"] for k, v in extra.items()}, default="", return_dtype=pl.String
            )
        )
        .otherwise(pl.col("uhik"))
        .alias("uhik"),
        pl.when(pl.col("id").is_in(list(extra)))
        .then(
            pl.col("id").replace_strict(
                {k: v["markus"] for k, v in extra.items()}, default="", return_dtype=pl.String
            )
        )
        .otherwise(pl.col("markus"))
        .alias("markus"),
    )


def evaluated(cat: pl.DataFrame) -> pl.DataFrame:
    """Kihid, mida tuleb analüüsida: ``eval = TRUE`` (v.a. baaskaart) ja lähtekasu lisakihid (``BRIEF_EXTRA``)."""
    return cat.filter(
        (pl.col("eval") & (pl.col("grupp_kood") != "baaskaart")) | pl.col("id").is_in(list(BRIEF_EXTRA))
    )


def zero_values(layer_id: str, nodata: float | None) -> tuple[float, ...]:
    """Väärtused, mis loetakse kehtivaks nulliks: deklareeritud NoData ja ``ZERO_EXTRA``.

    Erand: ``NODATA_EXCLUDED`` kihtides jääb NoData valimist välja (nulliks loetakse ainult NoData ``0``).

    Parameters
    ----------
    layer_id
        Kihi id.
    nodata
        Tabelis deklareeritud NoData.

    Returns
    -------
    tuple[float, ...]
        Tühi, kui NoData puudub (või on erandkihis nullist erinev) ja lisaväärtusi pole.
    """
    vals: list[float] = []
    if nodata is not None and (layer_id not in NODATA_EXCLUDED or float(nodata) == 0.0):
        vals.append(float(nodata))
    vals.extend(ZERO_EXTRA.get(layer_id, ()))
    return tuple(dict.fromkeys(vals))
