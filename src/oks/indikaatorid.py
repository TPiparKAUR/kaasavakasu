"""Ökosüsteemiteenuste indikaatorid: kihtide rühmitus teenusteks ja kvalitatiivne kirjeldus.

Üks indikaator = üks loodushüve (nt „söögiseened“) koos biofüüsikalise kihi ja sellega seotud rahaliste
kihtidega. Sellest tulenevad lähtekasu tabelisammud (``kaasnev``) ja kvalitatiivne raamistik
(lähteülesanne: mõju suund, tugevus, ajaline raamistik, ulatus, topeltarvestuse risk, ebakindlus,
märkus sotsiaalmajandusliku mõju hindajale).

Kõik väited tuginevad ametliku kihitabeli (``layer_definition_checked_vrs2``) kihi kirjeldustele ja
tabeli märkustele. CICES-i lahter (``sektsioon``) on ainus, mida peab hindama kindlalt (CICES v5.1:
varustav, reguleeriv ja säilitav, kultuuriline); ``grupp`` ja kõik hinnangulised veerud on ETTEPANEK, mida
valdkonna ekspert kinnitab. CICES-i klasside koode siia ei kirjutata, sest neid ei ole lähteandmetes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

PROVISIONING = "Varustav"
REGULATING = "Reguleeriv ja säilitav"
CULTURAL = "Kultuuriline"

#: Mõju tugevuse ettepanek suhtelise muutuse (|Δ| / halvema seisundi mediaan; metoodika v2) järgi; lävendid on
#: kokkuleppeline ettepanek, mitte andmetest tulenev piir.
STRENGTH_BREAKS: tuple[float, float] = (0.10, 0.50)


@dataclass(frozen=True)
class Indicator:
    """Ühe loodushüve kirjeldus."""

    key: str
    nimi: str
    sektsioon: str
    grupp: str
    bio: str | None
    raha: tuple[str, ...] = ()
    tuup: Literal["varu", "voog", "indeks", "skoor"] = "indeks"
    suund: Literal["suurem_parem", "vaiksem_parem"] = "suurem_parem"
    ajaraam: str = ""
    ulatus: str = ""
    ekstreem: str = ""
    raha_meetod: str = ""
    kulukasu: str = ""
    topelt: str = ""
    ebakindlus: str = ""
    markus: str = ""
    laiendid: tuple[str, ...] = field(default_factory=tuple)

    @property
    def layers(self) -> tuple[str, ...]:
        """Kõik kihid (biofüüsikaline + rahalised + lisakihid) selles järjekorras."""
        return tuple(x for x in (self.bio, *self.raha, *self.laiendid) if x)


INDICATORS: tuple[Indicator, ...] = (
    Indicator(
        "mulla_c",
        "Mulla orgaanilise süsiniku varu",
        REGULATING,
        "Atmosfääri koostise reguleerimine (süsiniku säilitamine mullas)",
        "c_tonn_per_ha_final_2022_10m",
        ("mullasusinik_aasta_keskmine_2022_10m", "mullasusinik_aasta_sotsiaalne_kulu_2022_10m"),
        "varu",
        "suurem_parem",
        "pikaajaline (mulla süsiniku muutus on aeglane; ajaraam eksperdi hinnata)",
        "globaalne mõju, lokaalne rakendus",
        "",
        "varu × 3,67 × CO2 hind: ETS 2022 keskmine 80,68 EUR/t CO2 või sotsiaalse kulu hind 169,77 EUR/t CO2 (Rennert et al. 2022)",
        "osaliselt: väärtus on varu (EUR/ha), mitte aastane voog; kasutatav on varu muutus (Δ) ajas; tabeli märkus: 'Hind kokku leppida'",
        "mulla ja biomassi süsinik on eri reservuaarid; ära liida mulla süsiniku varu väärtust kasvuhoonegaaside heitmega samalt alalt; biofüüsikaline ja rahaline versioon on sama hüve",
        "mudel (EstSoil-EH põhjal); suured veekogud, linnalised alad ja >6 m teed on välja jäetud; ökosüsteemi keskmised on 700–1900 t C/ha (soodes kõrgeimad), mis viitab kogu mullaprofiilile või turbale: sügavus ja ühik kinnitada kihi autoriga; seisundite vahe on ruumiline, mitte ajaline",
        "kaks hinda (ETS vs sotsiaalne kulu) erinevad 2,1 korda; vali üks või näita mõlemat",
    ),
    Indicator(
        "puit_c_mets",
        "Metsa puitsesse biomassi seotud süsiniku varu",
        REGULATING,
        "Atmosfääri koostise reguleerimine (süsiniku sidumine biomassi)",
        "puitne_biomass_c_t_ha_kogu_eesti_sum_2022_5m",
        ("puitne_biomass_c_eur_ha_ets_borsihind_kogu_eesti_sum_2022_5m",),
        "varu",
        "suurem_parem",
        "pikaajaline (metsa kasv ja küpsemine)",
        "lokaalne kuni üleriigiline",
        "kaudselt (metsa tuule- ja tulekindlus ei ole kihis kajastatud)",
        "süsinikuvaru × ETS börsihind 80,68 EUR/t CO2 (aasta keskmine)",
        "osaliselt: varu, mitte voog; metsa raiumisel varu väheneb, seega ainult majandamata või kaitstava metsa puhul",
        "ei kattu mulla süsinikuga; kattub puidutoorainega (PUIDUTOORAINE on lähtekasu järgi analüüsist väljas), seega ära loe sama puitu korraga süsiniku ja toorainena",
        "mudel: puuliik, vanus, LiDAR-tagavara; arvestab lageraiete mõju",
    ),
    Indicator(
        "puit_c_niit",
        "Niidu puitsesse biomassi seotud süsiniku varu",
        REGULATING,
        "Atmosfääri koostise reguleerimine (süsiniku sidumine biomassi)",
        "puitne_biomass_c_t_ha_niit_sum_2022_5m",
        (),
        "varu",
        "suurem_parem",
        "pikaajaline",
        "lokaalne",
        "",
        "",
        "ei: rahaline kiht puudub",
        "puitsete taimede süsinik võib kattuda metsa kihiga niitude ja metsa piiril",
        "LiDAR-põhine nelja klassi hinnang; tabeli märkus: 'Üle otsustada. Sõltub kihi metoodika sobivusest'",
        "niitudel võib puitse biomassi suurenemine olla taastamise eesmärgiga vastuolus (võsastumine); suuna tõlgendus kinnitada eksperdiga",
    ),
    Indicator(
        "puit_c_soo",
        "Soo puitsesse biomassi seotud süsiniku varu",
        REGULATING,
        "Atmosfääri koostise reguleerimine (süsiniku sidumine biomassi)",
        "puitne_biomass_c_t_ha_soo_sum_2022_5m",
        (),
        "varu",
        "suurem_parem",
        "pikaajaline",
        "lokaalne",
        "",
        "",
        "ei: rahaline kiht puudub",
        "lagesoodes on puitse biomassi osa marginaalne võrreldes mulla süsinikuga; ära loe mulla süsiniku (turba) kõrval",
        "LiDAR-põhine taimkatte kõrgusmudel",
        "soode taastamisel (taasniisutamine) võib puitne biomass väheneda, kuid mulla süsiniku säilimine kasvab; vaata koos mulla süsinikuga",
    ),
    Indicator(
        "mikrokliima",
        "Mikrokliima reguleerimine (temperatuuri erinevuse määr)",
        REGULATING,
        "Temperatuuri ja niiskuse reguleerimine",
        "kliimaregulatsioon_2022_5m",
        (),
        "indeks",
        "vaiksem_parem",
        "lühi- kuni keskpikk (taimkatte taastumine)",
        "lokaalne",
        "kuumalained ja linnasaared (lokaalne leevendus)",
        "",
        "ei: rahaline kiht puudub",
        "",
        "väärtus on arvutatud baaskaardi klassi kohta (suvise pilvitu päeva maapinnatemperatuuri 10–90 % detsiilide vahe jagatud klassideülese mediaaniga); seos seisundiga on seetõttu definitsiooniline",
        "VÄIKSEM väärtus = ühtlasem temperatuur = parem; positiivne Δ tähendab hüve vähenemist",
    ),
    Indicator(
        "ohusaaste",
        "Õhusaaste puhverdamisvõime",
        REGULATING,
        "Õhu filtreerimine ja saasteainete sidumine",
        "ohusaaste_puhverdusvoime_2022_5m",
        ("ohusaaste_puhverdusvoime_eur_ha_2022_5m",),
        "voog",
        "suurem_parem",
        "lühi- kuni keskpikk (taimkatte taastumine)",
        "lokaalne (sõltub saastekoormusest ja asustustihedusest)",
        "",
        "ärahoitud PM2,5 tervisekulu ülekantud kulude meetodil; riigi aastane 20,88 mln EUR on jaotatud ökosüsteemide vahel biofüüsikalise panuse järgi",
        "piiratud: väärtus on riigi aastase kogusumma ruumiline jaotus; seisundi muutus ei muuda kogusummat, seega ei ole see piirkasu hinnang",
        "indeks (1–10) ja rahaline väärtus kirjeldavad sama hüve; ära liida",
        "indeks arvestab saaste hulka, puhverdusvõimet ja asustustihedust (nõudlust); tabeli märkus: '255 käitub kui 0'",
        "255 ja 0 on loetud nulliks (tabeli märkuse järgi); ekspert kinnitab",
    ),
    Indicator(
        "vee_regul",
        "Veevoogude reguleerimisvõime (maht)",
        REGULATING,
        "Veevoogude ja äärmuslike sündmuste reguleerimine",
        "vee_reguleerimisvoime_vol_ha_linnalised_teed_veekogud_2022_10m",
        ("vee_reguleerimisvoime_eur_ha_linnalised_teed_veekogud_2022_10m",),
        "varu",
        "suurem_parem",
        "keskpikk kuni pikaajaline (mulla struktuur ja taimkate)",
        "lokaalne kuni valgala",
        "üleujutuste ja põudade leevendus (vee hoidmine mullas)",
        "asenduskulu: eeldatav veehoidlas säilitamise maksumus",
        "osaliselt: asenduskulu; tabeli märkus: 'Rahalise ühiku metoodika vananenud'",
        "kattub fosfori ärakande ja vee puhastamisega ainult veekvaliteedi poolelt; üleujutuste ennetuse väärtust ära loe topelt (maht ja EUR)",
        "mulla veemahutavuse ja närbumisniiskuse vahe põhjal; linnalised teed ja veekogud välja jäetud",
    ),
    Indicator(
        "erosioon_p",
        "Fosfori ärakanne mullaerosiooniga",
        REGULATING,
        "Mullaerosiooni ja ainevoogude reguleerimine",
        "erosioon_p_kg_ha_a_2022_10m",
        ("erosioon_p_eur_ha_a_2022_10m",),
        "voog",
        "vaiksem_parem",
        "lühi- kuni keskpikk (taimkatte taastumine)",
        "lokaalne kuni valgala",
        "kaudselt (veekogude eutrofeerumine)",
        "fosforikao kulu: väetise asendus (715 EUR/t superfosfaati ≈ 4000 EUR/t P) ja eutrofeerumise kulu",
        "osaliselt: kahju-/asenduskulu; väärtus on ärakande KULU, seega hüve = ärakande vähenemine",
        "kattub vee puhastamise (kaldapuhvrid) fosforivooga; kg ja EUR on sama hüve; ära liida erosiooni C ärakandega",
        "väärtused põhinevad mullaerosiooni andmekihil ja mulla fosforisisaldusel; mudel",
        "SUUREM väärtus = suurem ärakanne = hüve väheneb; positiivne Δ on halvenemine",
    ),
    Indicator(
        "erosioon_c",
        "Orgaanilise süsiniku ärakanne",
        REGULATING,
        "Mullaerosiooni ja ainevoogude reguleerimine",
        "erosioon_c_kg_ha_a_2022_10m",
        (),
        "voog",
        "vaiksem_parem",
        "lühi- kuni keskpikk",
        "lokaalne",
        "",
        "",
        "ei: rahaline kiht puudub",
        "kattub mulla süsiniku varuga kaudselt (ärakandega kaob osa mulla süsinikust)",
        "mullaerosiooni andmekiht, ülemise mullahorisondi süsinik ja lasuvustihedus",
        "SUUREM väärtus = suurem ärakanne = hüve väheneb",
    ),
    Indicator(
        "vee_puhastus",
        "Vee puhastamise potentsiaal kaldapuhvrites (fosfor)",
        REGULATING,
        "Magevee keemilise seisundi reguleerimine",
        "vee_puhastamise_potentsiaal_p_kg_ha_a_2022_930m",
        ("vee_puhastamise_potentsiaal_p_eur_ha_2022_930m",),
        "voog",
        "suurem_parem",
        "lühi- kuni keskpikk",
        "lokaalne (kaldapuhvrid)",
        "",
        "ärahoitud kulu: superfosfaadi hind 715 EUR/t, ümberarvutatult puhta fosfori hind 4000 EUR/t",
        "osaliselt: ärahoitud kulu; ainult kaldapuhvrite tsoon",
        "kattub fosfori ärakandega erosioonist; kg ja EUR on sama hüve",
        "930 m eraldusvõime (madalam lahutusvõime): arvutuseks viidud baaskaardi 10 m lahutusvõimele; seisundite erinevus tuleb ainult 930 m ruutude vahelistest erinevustest; segumudel (uuriv) on võrdluseks",
        "madalama lahutusvõimega tulemus: tüüpide tasemel on väärtus 930 m ruudu väärtus",
    ),
    Indicator(
        "lamm",
        "Lammide veevoogude reguleerimine (taastamise kulu)",
        REGULATING,
        "Veevoogude ja äärmuslike sündmuste reguleerimine",
        "lamm_grd1000_am_drained_2022",
        (),
        "varu",
        "suurem_parem",
        "pikaajaline",
        "lokaalne (lammid)",
        "üleujutuste leevendus",
        "väärtuse ülekande meetod lammisoo taastamisväärtuse alusel; väheneb kuivendatud pindalaga",
        "osaliselt: taastamiskulu on kulu, mitte kasu",
        "kattub vee reguleerimisvõimega lammidel",
        "1 km ruudustik (madalam lahutusvõime), väli lammide_taastamise_kulu; arvutuseks viidud 10 m lahutusvõimele; segumudel (uuriv) on võrdluseks",
        "madalama lahutusvõimega tulemus: tüüpide tasemel on väärtus 1 km ruudu väärtus",
    ),
    Indicator(
        "biotorje",
        "Kahjuritõrje vajaduse vähenemine",
        REGULATING,
        "Kahjurite ja haiguste tõrje",
        "biotorje_2022",
        (),
        "indeks",
        "suurem_parem",
        "keskpikk (maastikuelementide taastamine)",
        "lokaalne (põllumassiivid)",
        "",
        "pestitsiidikulu vähenemine (maksimaalne kulu 98,02 EUR/ha; väli pestitshind_ha)",
        "osaliselt: rahaline versioon on samas vektorkihis (pestitshind_ha), eraldi rasterit ei ole",
        "rahaline ja biofüüsikaline versioon on sama muutuja; tabeli märkus: 'Kasutada ühte'",
        "arvutatud maastikuelementide katvusest ja põllu seisundiklassist: seos seisundiga on definitsiooniline",
        "ainult põllumaadel",
    ),
    Indicator(
        "tolmeldamine",
        "Ökosüsteemide tugi tolmeldajatele",
        REGULATING,
        "Tolmeldamine",
        "okosusteemide_tugi_tolmeldajatele_2022_10m",
        (),
        "indeks",
        "suurem_parem",
        "keskpikk",
        "lokaalne kuni regionaalne (doonoralad põldude jaoks)",
        "",
        "",
        "ei: suhteline indeks 0–1",
        "kattub elupaikade säilitamisega (sama ökosüsteemide sobivus)",
        "suhteline indeks; ei näita tolmeldamise rahalist väärtust põllukultuuridele",
    ),
    Indicator(
        "elupaik",
        "Elupaikade säilitamine looduslikele liikidele",
        REGULATING,
        "Elupaikade ja asurkondade säilitamine",
        "elupaigahuve_pakkumine_2022_10m",
        (),
        "indeks",
        "suurem_parem",
        "keskpikk kuni pikaajaline",
        "lokaalne kuni üleriigiline",
        "",
        "",
        "ei: suhteline indeks 0–10",
        "kattub tolmeldamise ja sidususega",
        "suhteline indeks; seisundi, sidususe ja unikaalsuse komponendikihte lähtekas ei nõua",
        "",
        laiendid=("sidusus_1km_2022_10m",),
    ),
    Indicator(
        "mustikad_pohlad",
        "Mustikate ja pohlade potentsiaalne saagikus",
        PROVISIONING,
        "Looduslikud taimed toiduks",
        "mustikad_pohlad_saagikus_2020_10m",
        ("mustikad_pohlad_hind_2022_10m",),
        "voog",
        "suurem_parem",
        "keskpikk (puistu täius ja kasvukohatüüp)",
        "lokaalne kuni üleriigiline",
        "",
        "kokkuostuhind 2,5 EUR/kg (2022)",
        "osaliselt: potentsiaalne, mitte realiseeritud tulu",
        "mustikate ja pohlade kiht sisaldab pohlad_saagikus kihi pohlad; ära liida neid",
        "2020. aasta ELME1 kiht (baaskaart 2022); mudel kasvukohatüübi ja täiuse põhjal; enamik pikslitest on null",
        "mediaan ja keskmine on arvutatud kogu klassi kehtiva pindala kohta, nullid kaasa arvatud; puuduvad andmed (NoData) on välja jäetud (erandkiht)",
        laiendid=("pohlad_saagikus_2020_10m",),
    ),
    Indicator(
        "seened",
        "Söögiseente potentsiaalne saagikus",
        PROVISIONING,
        "Looduslikud taimed ja seened toiduks",
        "seened_saagikus_2020_10m",
        ("seened_hind_2022_10m",),
        "voog",
        "suurem_parem",
        "keskpikk (puistu vanus)",
        "lokaalne kuni üleriigiline",
        "",
        "kokkuostuhind 4,5 EUR/kg (2022)",
        "osaliselt: potentsiaalne, mitte realiseeritud tulu",
        "kattub mustikate/pohlade ja kasemahlaga ainult siis, kui samale metsaalale arvestatakse korraga mitu kasutust ilma koristuse piiranguta",
        "58 liigi hinnanguline saagikus; 2020. aasta ELME1 kiht; mudel kasvukohatüübi ja puistu vanuse põhjal",
        "rahalise kihi NoData oli 0: nullid on loetud kehtivaks nulliks",
    ),
    Indicator(
        "kasemahl",
        "Kasemahla potentsiaalne saagikus",
        PROVISIONING,
        "Looduslikud taimed toiduks ja materjaliks",
        "kasemahl_saagikus_2020_10m",
        ("kasemahl_hind_2022_10m",),
        "voog",
        "suurem_parem",
        "keskpikk (puistu vanus)",
        "lokaalne",
        "",
        "kokkuostuhind 0,3 EUR/l",
        "osaliselt: potentsiaalne tulu",
        "kattub teiste metsast saadavate hüvedega ainult kasutusülekattes",
        "soo- ja kõdusoometsades andmed puuduvad; avakooslused on 0; ühik l/0,01 ha, rahaline kiht EUR/ha (teisendus 1 ha = 100 × 0,01 ha ei ole tehtud)",
        "ühikuid ei ole ühtlustatud; vaata ühikut",
    ),
    Indicator(
        "toit_pold",
        "Põllumajanduslike ökosüsteemide reaalboniteet",
        PROVISIONING,
        "Põllukultuurid toiduks",
        "toiduteenus_2022",
        (),
        "indeks",
        "suurem_parem",
        "lühi- kuni keskpikk",
        "lokaalne",
        "",
        "",
        "ei: indikaator, mitte rahaline",
        "",
        "põllukultuuride seisundiklass A–D langeb kokku kihi väärtusklassiga (kontrollitud); seos seisundi ja boniteedi vahel on definitsiooniline",
        "ainult põllumaad; tabeli märkus: 'Eraldi käsitlus'",
    ),
    Indicator(
        "virgestus",
        "Maismaaökosüsteemide virgestusväärtus",
        CULTURAL,
        "Füüsilised ja kogemuslikud koostoimed loodusega",
        "virgestuse_koondvaartus_2022_5m",
        ("virgestuse_koondvaartus_eur_ha_2022_5m",),
        "skoor",
        "suurem_parem",
        "keskpikk kuni pikaajaline",
        "lokaalne kuni üleriigiline",
        "",
        "Eesti täiskasvanud elanikkonna looduses puhkamise aastane kogukulu 320 mln EUR jaotatud kaalude alusel",
        "piiratud: kogusumma on ruumiliselt jaotatud (top-down); seisundi muutus ei muuda kogusummat; ei sobi piirkasu hinnanguks",
        "kattub loodusturismiga (sama kaalude baas osaliselt); ära liida virgestuse ja loodusturismi EUR väärtusi ilma kattuvuse kontrollita",
        "ekspertkaalud (ökosüsteemid, taristu, loodusobjektid, kaitstavad alad); astmeline 11 taset",
        "skoor on indeks (ühikuta)",
    ),
    Indicator(
        "loodusturism",
        "Loodusturismi hüve (looduslikkuse suhteline väärtus)",
        CULTURAL,
        "Füüsilised ja kogemuslikud koostoimed loodusega",
        "loodusturism_kaalsum_2022_5m",
        ("loodusturism_eur_ha_2022_5m",),
        "skoor",
        "suurem_parem",
        "keskpikk kuni pikaajaline",
        "regionaalne kuni üleriigiline",
        "",
        "välismaalt saabuvate loodusturistide tarbijakulu 637 mln EUR jaotatud kaalude alusel",
        "piiratud: kogusumma on ruumiliselt jaotatud (top-down); ei sobi piirkasu hinnanguks",
        "kattub virgestusega; ära liida ilma kattuvuse kontrollita",
        "ekspertkaalud; välistab inimmõjulised alad ja veekogud; kaalud sõltuvad seisundist (heas seisundis ökosüsteemid on kaaludes), seega seos on osaliselt definitsiooniline",
        "skoor on indeks (ühikuta)",
    ),
)

BY_KEY: dict[str, Indicator] = {i.key: i for i in INDICATORS}
LAYER_TO_INDICATOR: dict[str, str] = {lid: i.key for i in INDICATORS for lid in i.layers}


def all_layers() -> list[str]:
    """Kõik kihid indikaatorite järjekorras (biofüüsikaline, rahalised, lisakihid)."""
    return [lid for i in INDICATORS for lid in i.layers]


def strength(rel: float | None) -> str:
    """Mõju tugevuse ettepanek (``nõrk``, ``keskmine``, ``tugev``) suhtelise muutuse absoluutväärtuse järgi.

    Puuduv suhteline muutus (``None`` või ``NaN``, nt kui halvema seisundi mediaan on 0) ei anna tugevust.
    """
    if rel is None or not math.isfinite(rel):
        return ""
    a = abs(rel)
    lo, hi = STRENGTH_BREAKS
    return "nõrk" if a < lo else "keskmine" if a < hi else "tugev"
