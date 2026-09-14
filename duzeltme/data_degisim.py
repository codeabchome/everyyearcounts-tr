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

from ortak_tr import DEGISIM, yil_eki

VERI_IL = os.environ.get(
    "VERI_IL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri_il"))





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
