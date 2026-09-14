#!/usr/bin/env python3
"""Konu kuyruğunun ihtiyaç duyduğu saf yardımcılar ve tablolar.

YAN ETKİSİZ: dosya okumaz, klasör açmaz, ağa çıkmaz. topics_tr.py bunu
import eder; veri üretme betikleri (data_memleket.py, data_degisim.py) de
aynı kaynaktan beslenir.

Neden ayrı dosya: topics_tr.py önce doğrudan data_memleket/data_degisim'i
import ediyordu, onlar da data_il.py'yi çekiyordu ve data_il import anında
`os.makedirs(OUT)` çalıştırıyordu. Actions runner'da o yol yazılabilir
olmadığı için yayın işi daha ilk satırda patlıyordu (PermissionError).
Yayın yolunun veri üretme yoluna hiç dokunmaması gerekiyor.
"""

# ---------------------------------------------------------------- il adı ekleri
_SESLI = "aeıioöuü"
_KALIN = "aıou"
_EK = {"a": "lı", "ı": "lı", "o": "lu", "u": "lu",
       "e": "li", "i": "li", "ö": "lü", "ü": "lü"}

_KUCUK = str.maketrans({"İ": "i", "I": "ı"})
_HARF = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                       "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s",
                       "Ü": "u", "â": "a"})


def slug(il):
    """'Şanlıurfa' -> 'sanliurfa' (dosya adı için ASCII)."""
    return il.replace("İ", "i").replace("I", "i").lower().translate(_HARF).replace(" ", "-")


def ilgi(il):
    """'Sivas' -> 'Sivaslılar',  'Rize' -> 'Rizeliler',  'Ordu' -> 'Ordulular'."""
    son = next((h for h in reversed(il.lower().translate(_KUCUK)) if h in _SESLI), "a")
    ek = _EK[son]
    return il + ek + ("lar" if ek[-1] in _KALIN else "ler")


def bulunma(il):
    """'İstanbul' -> \"İstanbul'da\" ; ünlü/ünsüz uyumuna göre -da/-de/-ta/-te."""
    ad = il.lower().translate(_KUCUK)
    son_sesli = next((h for h in reversed(ad) if h in _SESLI), "a")
    ek = "d" if ad[-1] not in "fstkçşhp" else "t"
    ek += "a" if son_sesli in "aıou" else "e"
    return f"{il}'{ek}"


def tr_buyuk(s):
    """Türkçe büyük harf: i -> İ, ı -> I (Python'un upper()'ı bunu bilmiyor)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


# ---------------------------------------------------------------- yıl ekleri
_SON = {1: "den", 2: "den", 3: "ten", 4: "ten", 5: "ten",
        6: "dan", 7: "den", 8: "den", 9: "dan"}
_ONLAR = {0: "den", 1: "dan", 2: "den", 3: "dan", 4: "tan",
          5: "den", 6: "tan", 7: "ten", 8: "den", 9: "dan"}


def yil_eki(y):
    """Sayıdan sonraki ayrılma eki okunuşa göre: 2015'ten, 2009'dan, 2000'den."""
    y = int(y)
    return _SON[y % 10] if y % 10 else _ONLAR[(y // 10) % 10]


# ---------------------------------------------------------------- değişim tablosu
# (kaynak slug, yön, baslik1, baslik2, tema, kademe)
#   yön: "artis" | "dusus" | "oranartis"
DEGISIM = [
    # --- nüfus
    ("nufus",             "artis",     "NÜFUSU EN ÇOK",        "ARTAN 10 İL",            "nufus",   1),
    ("nufus",             "dusus",     "NÜFUSU EN ÇOK",        "AZALAN 10 İL",           "nufus",   1),
    ("nufus",             "oranartis", "ORANSAL OLARAK EN ÇOK","BÜYÜYEN 10 İL",          "nufus",   2),
    ("ortanca_yas",       "artis",     "EN HIZLI",             "YAŞLANAN 10 İL",         "nufus",   1),
    ("yasli_orani",       "artis",     "YAŞLI ORANI EN ÇOK",   "ARTAN 10 İL",            "nufus",   2),
    ("cocuk_orani",       "dusus",     "ÇOCUK ORANI EN ÇOK",   "AZALAN 10 İL",           "nufus",   2),
    ("yabanci_nufus",     "artis",     "YABANCI NÜFUSU",       "EN ÇOK ARTAN 10 İL",     "nufus",   2),
    ("nufus_yogunlugu",   "artis",     "EN ÇOK SIKIŞAN",       "10 İL",                  "nufus",   3),
    ("yasli_nufus",       "artis",     "YAŞLI SAYISI EN ÇOK",  "ARTAN 10 İL",            "nufus",   3),
    ("yasli_bagimlilik",  "artis",     "YAŞLI BAĞIMLILIĞI",    "EN ÇOK ARTAN 10 İL",     "nufus",   3),

    # --- aile
    ("dogurganlik",       "dusus",     "DOĞURGANLIĞI EN ÇOK",  "DÜŞEN 10 İL",            "aile",    1),
    ("akraba_evlilik",    "dusus",     "AKRABA EVLİLİĞİ",      "EN ÇOK AZALAN 10 İL",    "aile",    1),
    ("bosanma_hizi",      "artis",     "BOŞANMA ORANI",        "EN ÇOK ARTAN 10 İL",     "aile",    1),
    ("evlenme_hizi",      "dusus",     "EVLENME ORANI",        "EN ÇOK DÜŞEN 10 İL",     "aile",    2),
    ("ilk_evlenme_kadin", "artis",     "KADINLARIN EVLİLİK",   "YAŞI EN ÇOK ARTAN 10 İL","aile",    2),
    ("ilk_evlenme_erkek", "artis",     "ERKEKLERİN EVLİLİK",   "YAŞI EN ÇOK ARTAN 10 İL","aile",    3),
    ("ilk_anne_yasi",     "artis",     "İLK ANNELİK YAŞI",     "EN ÇOK ARTAN 10 İL",     "aile",    2),
    ("anne_yasi",         "artis",     "ANNE YAŞI EN ÇOK",     "ARTAN 10 İL",            "aile",    3),
    ("dogum_hizi",        "dusus",     "DOĞUM ORANI EN ÇOK",   "DÜŞEN 10 İL",            "aile",    2),
    ("hanehalki",         "dusus",     "AİLELERİ EN ÇOK",      "KÜÇÜLEN 10 İL",          "aile",    2),

    # --- sağlık
    ("bebek_olum",        "dusus",     "BEBEK ÖLÜMLERİNİ",     "EN ÇOK AZALTAN 10 İL",   "saglik",  1),
    ("hekim_10bin",       "artis",     "DOKTOR SAYISI",        "EN ÇOK ARTAN 10 İL",     "saglik",  2),
    ("yatak_10bin",       "artis",     "HASTANE YATAĞI",       "EN ÇOK ARTAN 10 İL",     "saglik",  2),
    ("hekim",             "oranartis", "DOKTOR SAYISI",        "KATLANAN 10 İL",         "saglik",  3),
    ("hastane_yatak",     "artis",     "EN ÇOK HASTANE YATAĞI","EKLENEN 10 İL",          "saglik",  3),
    ("hemsire_10bin",     "artis",     "HEMŞİRE SAYISI",       "EN ÇOK ARTAN 10 İL",     "saglik",  3),

    # --- yaşam
    ("otomobil_1000",     "artis",     "ARABALAŞMASI EN HIZLI","ARTAN 10 İL",            "yasam",   1),
    ("otomobil",          "oranartis", "OTOMOBİL SAYISI",      "KATLANAN 10 İL",         "yasam",   2),
    ("motosiklet",        "oranartis", "MOTOSİKLET SAYISI",    "KATLANAN 10 İL",         "yasam",   3),
    ("traktor",           "artis",     "EN ÇOK TRAKTÖR",       "EKLENEN 10 İL",          "yasam",   3),
    ("trafik_kaza_10bin", "artis",     "TRAFİK KAZASI",        "EN ÇOK ARTAN 10 İL",     "yasam",   2),

    # --- ekonomi
    ("gsyh_tarim_payi",   "dusus",     "TARIMDAN EN ÇOK",      "KOPAN 10 İL",            "ekonomi", 2),
    ("gsyh_sanayi_payi",  "artis",     "SANAYİLEŞMESİ EN ÇOK", "ARTAN 10 İL",            "ekonomi", 2),
]
