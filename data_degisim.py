#!/usr/bin/env python3
"""Mevcut göstergelerden "ne kadar arttı / ne kadar azaldı" serileri türetir.

Yeni veri indirmeye gerek yok: elimizdeki seriden ilk yıla göre farkı alıyoruz.
Bar uzunluğu negatif olamayacağı için fark 0'ın altına düşmüyor — ters yönde
hareket eden il basitçe 0'da oturuyor.

  artis_<slug>      : v(t) - v(y0)        "en çok artan"
  dusus_<slug>      : v(y0) - v(t)        "en çok azalan"
  oranartis_<slug>  : (v(t)/v(y0)-1)*100  "oransal olarak en çok büyüyen"

`oranartis` sadece sayım göstergelerinde anlamlı ve mutlak artıştan FARKLI bir
sıralama veriyor (İstanbul mutlakta birinci, oranda Bilecik/Tekirdağ öne çıkıyor).
"""
import json
import os

VERI_IL = os.environ.get(
    "VERI_IL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri_il"))

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

_SON = {1: "den", 2: "den", 3: "ten", 4: "ten", 5: "ten",
        6: "dan", 7: "den", 8: "den", 9: "dan"}
_ONLAR = {0: "den", 1: "dan", 2: "den", 3: "dan", 4: "tan",
          5: "den", 6: "tan", 7: "ten", 8: "den", 9: "dan"}


def yil_eki(y):
    """Sayıdan sonraki ayrılma eki okunuşa göre: 2015'TEN, 2009'DAN, 2000'DEN."""
    y = int(y)
    return _SON[y % 10] if y % 10 else _ONLAR[(y // 10) % 10]



YON_AD = {"artis": "Artış", "dusus": "Azalış", "oranartis": "Oransal Artış"}


def turet(kaynak, yon):
    yol = os.path.join(VERI_IL, kaynak + ".json")
    if not os.path.exists(yol):
        return None
    j = json.load(open(yol, encoding="utf-8"))
    y0, birim = j["y0"], j["birim"]
    # Oransal artışta tabanı çok küçük iller saçma yüzdeler üretiyor
    # (Gümüşhane'de 1 yabancıdan 1318'e = %131.700). Medyan tabanın 1/20'sinin
    # altındaki iller bu modda hesaba katılmıyor.
    esik = 0.0
    if yon == "oranartis":
        tabanlar = sorted(
            d[next((i for i, v in enumerate(d) if v is not None), 0)] or 0
            for d in j["iller"].values())
        if tabanlar:
            esik = tabanlar[len(tabanlar) // 2] / 20.0

    out = {}
    for il, dizi in j["iller"].items():
        # ilk dolu yıl taban alınır; seri başı boşsa o il atlanır
        taban_i = next((i for i, v in enumerate(dizi) if v is not None), None)
        if taban_i is None:
            continue
        taban = dizi[taban_i]
        if yon == "oranartis" and (not taban or taban < esik):
            continue
        seri = {}
        for i, v in enumerate(dizi):
            if v is None or i < taban_i:
                continue
            if yon == "artis":
                d = v - taban
            elif yon == "dusus":
                d = taban - v
            else:
                d = (v / taban - 1) * 100
            seri[y0 + i] = max(0.0, d)       # negatif bar çizilemiyor
        if len(seri) >= 3:
            out[il] = seri
    if not out:
        return None
    return j, out, y0, birim


def main():
    from data_il import yaz
    n = 0
    for kaynak, yon, b1, b2, tema, kademe in DEGISIM:
        r = turet(kaynak, yon)
        if not r:
            print("  ATLANDI:", kaynak, yon)
            continue
        j, seri, y0, birim = r
        slug = f"{yon}_{kaynak}"
        yeni_birim = "%" if yon == "oranartis" else birim
        ondalik = 1 if yon == "oranartis" else None
        yaz(f"{j['ad']} — {y0}'{yil_eki(y0)} Beri {YON_AD[yon]}", slug, seri,
            yeni_birim, j["kaynak"],
            f"{y0} yılına göre fark; ters yönde hareket eden il 0'da gösterilir",
            ondalik=ondalik)
        n += 1
    print(f"{n} değişim göstergesi")


if __name__ == "__main__":
    main()
