#!/usr/bin/env python3
"""Konu kuyruğu — Türkiye Kaçıncı?

İki katman:
  IL_KONULARI    — 81 il, TÜİK verisi (veri_il/*.json). Kanalın omurgası.
  ULKE_KONULARI  — topics_tr.json varsa oradan (discover_tr.py üretir).

Sıralama:
  1) KADEME — merak sırası. 1 = en çok merak edilen, en tutucu konular;
     3 = uzun kuyruk. Kanal önce 1'leri yayınlar.
  2) Kademe içinde temalar arasında round-robin: aynı gösterge veya aynı
     konu ailesi arka arkaya gelmez.

Yeni gösterge eklemek: veri_il/<slug>.json üret, aşağıdaki listeye satır ekle.
"""
import json
import os

BURADA = os.path.dirname(os.path.abspath(__file__))


# (dosya, baslik1, baslik2, ters, tema, kademe)
#   ters=True  -> en DÜŞÜK 10
IL_KONULARI = [
    # ================= KADEME 1 — en çok merak edilenler =================
    ("nufus",             "EN KALABALIK",         "10 İL",                  False, "nufus",   1),
    ("gsyh_kisi_basi",    "KİŞİ BAŞINA GELİRİ",   "EN YÜKSEK 10 İL",        False, "ekonomi", 1),
    ("memleket_istanbul", "İSTANBUL'DA EN ÇOK",   "HANGİ İLDEN İNSAN VAR?", False, "memleket",1),
    ("akraba_evlilik",    "AKRABA EVLİLİĞİ",      "EN YÜKSEK 10 İL",        False, "aile",    1),
    ("goc_net",           "EN ÇOK NÜFUS",         "KAYBEDEN 10 İL",         True,  "goc",     1),
    ("otomobil_1000",     "1000 KİŞİYE DÜŞEN",    "EN ÇOK OTOMOBİL",        False, "yasam",   1),
    ("bosanma_hizi",      "BOŞANMA ORANI",        "EN YÜKSEK 10 İL",        False, "aile",    1),
    ("ortanca_yas",       "EN YAŞLI",             "10 İL",                  False, "nufus",   1),
    ("gsyh_kisi_basi",    "KİŞİ BAŞINA GELİRİ",   "EN DÜŞÜK 10 İL",         True,  "ekonomi", 1),
    ("hekim_10bin",       "DOKTORU EN AZ",        "OLAN 10 İL",             True,  "saglik",  1),
    ("dogurganlik",       "EN ÇOK ÇOCUK",         "YAPILAN 10 İL",          False, "aile",    1),
    ("memleket_ankara",   "ANKARA'DA EN ÇOK",     "HANGİ İLDEN İNSAN VAR?", False, "memleket",1),
    ("goc_egitim",        "EĞİTİM İÇİN",          "EN ÇOK GÖÇ ALAN 10 İL",  False, "goc",     1),
    ("trafik_kaza_10bin", "TRAFİK KAZASI",        "EN ÇOK OLAN 10 İL",      False, "yasam",   1),
    ("nufus_yogunlugu",   "EN SIKIŞIK",           "10 İL",                  False, "nufus",   1),
    ("gsyh",              "EKONOMİSİ EN BÜYÜK",   "10 İL",                  False, "ekonomi", 1),
    ("ilk_evlenme_kadin", "KADINLARIN EN GEÇ",    "EVLENDİĞİ 10 İL",        False, "aile",    1),
    ("yabanci_nufus",     "EN ÇOK YABANCI",       "YAŞAYAN 10 İL",          False, "nufus",   1),
    ("goc_alan",          "EN ÇOK GÖÇ ALAN",      "10 İL",                  False, "goc",     1),
    ("bebek_olum",        "BEBEK ÖLÜM ORANI",     "EN YÜKSEK 10 İL",        False, "saglik",  1),
    ("memleket_izmir",    "İZMİR'DE EN ÇOK",      "HANGİ İLDEN İNSAN VAR?", False, "memleket",1),
    ("dogurganlik",       "EN AZ ÇOCUK",          "YAPILAN 10 İL",          True,  "aile",    1),
    ("yapi_ruhsat",       "EN ÇOK KONUT",         "İZNİ VERİLEN 10 İL",     False, "yasam",   1),
    ("nufus",             "NÜFUSU EN AZ",         "10 İL",                  True,  "nufus",   1),

    # ================= KADEME 2 — güçlü ikinci halka =================
    ("goc_veren",         "EN ÇOK GÖÇ VEREN",     "10 İL",                  False, "goc",     2),
    ("gsyh_tarim_payi",   "EKONOMİSİ EN ÇOK",     "TARIMA DAYALI 10 İL",    False, "ekonomi", 2),
    ("akraba_evlilik",    "AKRABA EVLİLİĞİ",      "EN DÜŞÜK 10 İL",         True,  "aile",    2),
    ("yasli_orani",       "NÜFUSU EN YAŞLI",      "10 İL",                  False, "nufus",   2),
    ("hekim_10bin",       "DOKTORU EN ÇOK",       "OLAN 10 İL",             False, "saglik",  2),
    ("memleket_bursa",    "BURSA'DA EN ÇOK",      "HANGİ İLDEN İNSAN VAR?", False, "memleket",2),
    ("goc_is",            "İŞ İÇİN",              "EN ÇOK GÖÇ ALAN 10 İL",  False, "goc",     2),
    ("gsyh_sanayi_payi",  "EKONOMİSİ EN ÇOK",     "SANAYİYE DAYALI 10 İL",  False, "ekonomi", 2),
    ("evlenme_hizi",      "EN ÇOK EVLENİLEN",     "10 İL",                  False, "aile",    2),
    ("cocuk_orani",       "NÜFUSU EN GENÇ",       "10 İL",                  False, "nufus",   2),
    ("traktor",           "EN ÇOK TRAKTÖR",       "OLAN 10 İL",             False, "yasam",   2),
    ("yatak_10bin",       "HASTANE YATAĞI",       "EN ÇOK OLAN 10 İL",      False, "saglik",  2),
    ("memleket_antalya",  "ANTALYA'DA EN ÇOK",    "HANGİ İLDEN İNSAN VAR?", False, "memleket",2),
    ("goc_net_hizi",      "NET GÖÇ HIZI",         "EN YÜKSEK 10 İL",        False, "goc",     2),
    ("hanehalki",         "EN KALABALIK",         "AİLELERİN OLDUĞU 10 İL", False, "aile",    2),
    ("ortanca_yas",       "EN GENÇ",              "10 İL",                  True,  "nufus",   2),
    ("motosiklet",        "EN ÇOK MOTOSİKLET",    "OLAN 10 İL",             False, "yasam",   2),
    ("bosanma_hizi",      "BOŞANMA ORANI",        "EN DÜŞÜK 10 İL",         True,  "aile",    2),
    ("eczaci_10bin",      "ECZACISI EN ÇOK",      "OLAN 10 İL",             False, "saglik",  2),
    ("memleket_kocaeli",  "KOCAELİ'DE EN ÇOK",    "HANGİ İLDEN İNSAN VAR?", False, "memleket",2),
    ("goc_konut",         "DAHA İYİ KONUT İÇİN",  "EN ÇOK GÖÇ ALAN 10 İL",  False, "goc",     2),
    ("nufus_artis_hizi",  "NÜFUSU EN HIZLI",      "BÜYÜYEN 10 İL",          False, "nufus",   2),
    ("ilk_evlenme_erkek", "ERKEKLERİN EN GEÇ",    "EVLENDİĞİ 10 İL",        False, "aile",    2),
    ("yapi_ruhsat_10bin", "NÜFUSA GÖRE EN ÇOK",   "KONUT YAPILAN 10 İL",    False, "yasam",   2),
    ("bebek_olum",        "BEBEK ÖLÜM ORANI",     "EN DÜŞÜK 10 İL",         True,  "saglik",  2),
    ("memleket_adana",    "ADANA'DA EN ÇOK",      "HANGİ İLDEN İNSAN VAR?", False, "memleket",2),
    ("goc_evlilik",       "EVLİLİK NEDENİYLE",    "EN ÇOK GÖÇ ALAN 10 İL",  False, "goc",     2),
    ("yasli_bagimlilik",  "YAŞLI BAĞIMLILIK",     "ORANI EN YÜKSEK 10 İL",  False, "nufus",   2),
    ("dogum_hizi",        "DOĞUM ORANI",          "EN YÜKSEK 10 İL",        False, "aile",    2),
    ("kamyon",            "EN ÇOK KAMYON",        "OLAN 10 İL",             False, "yasam",   2),
    ("hemsire_10bin",     "HEMŞİRESİ EN ÇOK",     "OLAN 10 İL",             False, "saglik",  2),
    ("memleket_mersin",   "MERSİN'DE EN ÇOK",     "HANGİ İLDEN İNSAN VAR?", False, "memleket",2),
    ("goc_tayin",         "TAYİNLE EN ÇOK",       "GÖÇ ALAN 10 İL",         False, "goc",     2),
    ("nufus_yogunlugu",   "EN TENHA",             "10 İL",                  True,  "nufus",   2),
    ("ilk_anne_yasi",     "İLK ÇOCUĞUNU EN GEÇ",  "DOĞURAN 10 İL",          False, "aile",    2),
    ("otomobil",          "EN ÇOK OTOMOBİL",      "OLAN 10 İL",             False, "yasam",   2),
    ("dis_hekimi_10bin",  "DİŞ HEKİMİ EN ÇOK",    "OLAN 10 İL",             False, "saglik",  2),

    # ================= KADEME 3 — uzun kuyruk =================
    ("goc_net",           "NET GÖÇÜ EN YÜKSEK",   "10 İL",                  False, "goc",     3),
    ("yasli_nufus",       "EN ÇOK YAŞLI",         "YAŞAYAN 10 İL",          False, "nufus",   3),
    ("evlenme_sayisi",    "EN ÇOK EVLİLİK",       "YAPILAN 10 İL",          False, "aile",    3),
    ("yapi_izin",         "EN ÇOK OTURMA İZNİ",   "VERİLEN 10 İL",          False, "yasam",   3),
    ("hekim",             "EN ÇOK DOKTORU",       "OLAN 10 İL",             False, "saglik",  3),
    ("nufus_artis_hizi",  "NÜFUSU EN HIZLI",      "ERİYEN 10 İL",           True,  "nufus",   3),
    ("evlenme_hizi",      "EN AZ EVLENİLEN",      "10 İL",                  True,  "aile",    3),
    ("traktor",           "TRAKTÖRÜ EN AZ",       "OLAN 10 İL",             True,  "yasam",   3),
    ("yatak_10bin",       "HASTANE YATAĞI",       "EN AZ OLAN 10 İL",       True,  "saglik",  3),
    ("cocuk_orani",       "ÇOCUK NÜFUS ORANI",    "EN DÜŞÜK 10 İL",         True,  "nufus",   3),
    ("anne_yasi",         "ANNELERİN EN GENÇ",    "OLDUĞU 10 İL",           True,  "aile",    3),
    ("otomobil_1000",     "1000 KİŞİYE DÜŞEN",    "EN AZ OTOMOBİL",         True,  "yasam",   3),
    ("eczaci_10bin",      "ECZACISI EN AZ",       "OLAN 10 İL",             True,  "saglik",  3),
    ("yasli_orani",       "YAŞLI ORANI",          "EN DÜŞÜK 10 İL",         True,  "nufus",   3),
    ("ilk_evlenme_kadin", "KADINLARIN EN ERKEN",  "EVLENDİĞİ 10 İL",        True,  "aile",    3),
    ("hastane_yatak",     "EN ÇOK HASTANE",       "YATAĞI OLAN 10 İL",      False, "saglik",  3),
    ("yabanci_nufus",     "EN AZ YABANCI",        "YAŞAYAN 10 İL",          True,  "nufus",   3),
    ("dogum_hizi",        "DOĞUM ORANI",          "EN DÜŞÜK 10 İL",         True,  "aile",    3),
    ("motosiklet",        "MOTOSİKLETİ EN AZ",    "OLAN 10 İL",             True,  "yasam",   3),
    ("hemsire_10bin",     "HEMŞİRESİ EN AZ",      "OLAN 10 İL",             True,  "saglik",  3),
    ("hanehalki",         "EN KÜÇÜK",             "AİLELERİN OLDUĞU 10 İL", True,  "aile",    3),
    ("trafik_kaza",       "EN ÇOK TRAFİK KAZASI", "OLAN 10 İL",             False, "yasam",   3),
    ("dis_hekimi_10bin",  "DİŞ HEKİMİ EN AZ",     "OLAN 10 İL",             True,  "saglik",  3),
    ("yasli_bagimlilik",  "YAŞLI BAĞIMLILIK",     "ORANI EN DÜŞÜK 10 İL",   True,  "nufus",   3),
    ("ilk_evlenme_erkek", "ERKEKLERİN EN ERKEN",  "EVLENDİĞİ 10 İL",        True,  "aile",    3),
    ("yapi_ruhsat_10bin", "NÜFUSA GÖRE EN AZ",    "KONUT YAPILAN 10 İL",    True,  "yasam",   3),
    ("gsyh_tarim_payi",   "TARIMIN PAYI",         "EN DÜŞÜK 10 İL",         True,  "ekonomi", 3),
    ("ilk_anne_yasi",     "İLK ÇOCUĞUNU EN ERKEN","DOĞURAN 10 İL",          True,  "aile",    3),
    ("kir_orani",         "KIRDA YAŞAYANIN",      "EN ÇOK OLDUĞU 10 İL",    False, "nufus",   3),
    ("anne_yasi",         "ANNELERİN EN YAŞLI",   "OLDUĞU 10 İL",           False, "aile",    3),
    ("kamyon",            "KAMYONU EN AZ",        "OLAN 10 İL",             True,  "yasam",   3),
    ("gsyh_sanayi_payi",  "SANAYİNİN PAYI",       "EN DÜŞÜK 10 İL",         True,  "ekonomi", 3),
    ("trafik_kaza_10bin", "TRAFİK KAZASI",        "EN AZ OLAN 10 İL",       True,  "yasam",   3),
]

TEMA_SIRASI = ["nufus", "ekonomi", "aile", "goc", "yasam", "saglik", "memleket"]


def _serpistir(konular):
    """Aynı tema arka arkaya gelmesin — temalar arasında round-robin."""
    temalar = TEMA_SIRASI + [t for t in dict.fromkeys(k["tema"] for k in konular)
                             if t not in TEMA_SIRASI]
    kova = {t: [k for k in konular if k["tema"] == t] for t in temalar}
    sira = []
    while any(kova.values()):
        for t in temalar:
            if kova[t]:
                sira.append(kova[t].pop(0))
    return sira


def il_konulari():
    kademeler = {}
    gorulen = set()
    for satir in IL_KONULARI:
        dosya, b1, b2, ters, tema, kademe = satir
        anahtar = (dosya, ters)
        if anahtar in gorulen:      # aynı gösterge+yön iki kez yayınlanmasın
            raise ValueError(f"tekrar eden konu: {dosya} ters={ters}")
        gorulen.add(anahtar)
        yol = os.path.join(BURADA, "veri_il", dosya + ".json")
        if not os.path.exists(yol):
            raise FileNotFoundError(f"veri yok: {yol}")
        veri = json.load(open(yol, encoding="utf-8"))
        kademeler.setdefault(kademe, []).append({
            "id": f"il:{dosya}:{'dusuk' if ters else 'yuksek'}",
            "tur": "il",
            "veri": os.path.join("veri_il", dosya + ".json"),
            "baslik1": b1, "baslik2": b2, "ters": ters, "tema": tema,
            "kademe": kademe,
            "gosterge": veri["ad"], "kaynak": veri["kaynak"],
            "baslik": f"{b1} {b2}".title(),
        })
    ok = []
    for k in sorted(kademeler):
        ok += _serpistir(kademeler[k])
    return ok


def ulke_konulari():
    yol = os.path.join(BURADA, "topics_tr.json")
    if not os.path.exists(yol):
        return []
    out = []
    for t in json.load(open(yol, encoding="utf-8")):
        out.append({
            "id": t["id"], "tur": "ulke", "tema": t.get("scope", "dunya"),
            "baslik": t["title"], "kaynak": t["source_label"],
            "kod": t["code"], "source": t["source"], "scope": t["scope"],
            "ters": t["direction"] == "bottom", "kademe": 4,
        })
    return out


def build():
    """Tam kuyruk: önce il konuları (sınır içi öncelik), sonra ülke konuları."""
    return il_konulari() + ulke_konulari()


if __name__ == "__main__":
    k = build()
    print(f"{len(k)} konu\n")
    onceki = None
    for i, t in enumerate(k, 1):
        kd = t.get("kademe", "-")
        if kd != onceki:
            print(f"--- kademe {kd} ---")
            onceki = kd
        print(f"{i:3d}. [{t['tema']:8s}] {t.get('baslik1','')} {t.get('baslik2','')}".rstrip())
