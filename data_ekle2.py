#!/usr/bin/env python3
"""veri_il/ klasörünü klasik XLS tablolarından gelen göstergelerle genişletir.

data_il.py ve data_ekle.py'den SONRA çalıştırılır (nüfus.json gerekiyor).
"""
import json
import os

from data_xls import genis, iki_kademeli, blok_devrik, sutun_basligi, il_ileri_kategori
from data_il import yaz
from data_sdmx import oran

DOG = "TÜİK · Doğum İstatistikleri"
EVL = "TÜİK · Evlenme ve Boşanma İstatistikleri"
OLU = "TÜİK · Ölüm ve Ölüm Nedeni İstatistikleri"
SAG = "TÜİK · Sağlık İstatistikleri"
YAPI = "TÜİK · Yapı İzin İstatistikleri"
GOC = "TÜİK · İç Göç İstatistikleri"

VERI_IL = os.environ.get(
    "VERI_IL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri_il"))


def seri(dosya):
    j = json.load(open(os.path.join(VERI_IL, dosya + ".json"), encoding="utf-8"))
    y0 = j["y0"]
    return {il: {y0 + i: v for i, v in enumerate(a) if v is not None}
            for il, a in j["iller"].items()}


def main():
    nuf = seri("nufus")

    # ---------------- doğum
    yaz("Toplam Doğurganlık Hızı", "dogurganlik",
        genis("İllere Göre Toplam Doğurganlık Hızı.xls"), "çocuk", DOG,
        "bir kadının doğurgan çağı boyunca doğuracağı ortalama çocuk sayısı")

    yaz("Kaba Doğum Hızı", "dogum_hizi",
        genis("İllere Göre Kaba Doğum Hızı.xls"), "‰", DOG,
        "bin kişiye düşen canlı doğum")

    yaz("Annenin Ortalama Yaşı", "anne_yasi",
        genis("İllere Göre Annenin Ortalama Yaşı.xls"), "yaş", DOG)

    yaz("İlk Doğumda Ortalama Anne Yaşı", "ilk_anne_yasi",
        genis("İllere Göre İlk Doğumdaki Ortalama Anne Yaşı.xls"), "yaş", DOG)

    yaz("Bebek Ölüm Hızı", "bebek_olum",
        genis("İllere göre bebek ölüm hızı.xls"), "‰", OLU,
        "bin canlı doğumda bir yaşına gelmeden ölen bebek sayısı")

    # ---------------- evlilik
    yaz("Kaba Evlenme Hızı", "evlenme_hizi",
        genis("İllere göre kaba evlenme hızı.xls"), "‰", EVL,
        "bin kişiye düşen evlenme")

    yaz("Kaba Boşanma Hızı", "bosanma_hizi",
        genis("İllere Göre Kaba Boşanma Hızı.xls"), "‰", EVL,
        "bin kişiye düşen boşanma")

    ev = "İllere Göre Ortalama İlk Evlenme Yaşı.xls"
    yaz("Erkeklerde İlk Evlenme Yaşı", "ilk_evlenme_erkek",
        iki_kademeli(ev, "Erkek"), "yaş", EVL)
    yaz("Kadınlarda İlk Evlenme Yaşı", "ilk_evlenme_kadin",
        iki_kademeli(ev, "Kadın"), "yaş", EVL)

    ak = "İllere göre evlenme sayısı ile akraba evliliği sayısı ve oranı.xls"
    yaz("Akraba Evliliği Oranı", "akraba_evlilik",
        iki_kademeli(ak, "oranı"), "%", EVL,
        "toplam evlenmeler içinde akraba evliliklerinin payı")
    yaz("Evlenme Sayısı", "evlenme_sayisi",
        iki_kademeli(ak, "Evlenme"), "adet", EVL)

    # ---------------- sağlık
    yatak = genis("Hastane Yatak Sayılarının İllere Göre Dağılımı .xls")
    yaz("Hastane Yatak Sayısı", "hastane_yatak", yatak, "adet", SAG)
    yaz("10 Bin Kişiye Düşen Hastane Yatağı", "yatak_10bin",
        oran(yatak, nuf, carpan=10000.0), "adet", SAG,
        "yatak sayısı / nüfus × 10.000", ondalik=1)

    sp = "Sağlık Personeli Sayılarının İllere Göre Dağılımı.xls"
    hekim = il_ileri_kategori(sp, 2, "Toplam hekim")
    yaz("Hekim Sayısı", "hekim", hekim, "kişi", SAG)
    yaz("10 Bin Kişiye Düşen Hekim", "hekim_10bin",
        oran(hekim, nuf, carpan=10000.0), "kişi", SAG,
        "hekim sayısı / nüfus × 10.000", ondalik=1)
    hem = il_ileri_kategori(sp, 2, "Hemşire")
    yaz("10 Bin Kişiye Düşen Hemşire", "hemsire_10bin",
        oran(hem, nuf, carpan=10000.0), "kişi", SAG, ondalik=1)
    dis = il_ileri_kategori(sp, 2, "Diş Hekimi")
    yaz("10 Bin Kişiye Düşen Diş Hekimi", "dis_hekimi_10bin",
        oran(dis, nuf, carpan=10000.0), "kişi", SAG, ondalik=1)
    ecz = il_ileri_kategori(sp, 2, "Eczacı")
    yaz("10 Bin Kişiye Düşen Eczacı", "eczaci_10bin",
        oran(ecz, nuf, carpan=10000.0), "kişi", SAG, ondalik=1)

    # ---------------- yapı / konut
    yp = "İllere göre yapı belgesi verilen daire sayısı.xls"
    ruhsat = blok_devrik(yp, 2, 4, 3, 85)
    yaz("Yapı Ruhsatı Verilen Daire Sayısı", "yapi_ruhsat", ruhsat, "adet", YAPI)
    yaz("10 Bin Kişiye Düşen Yeni Konut Ruhsatı", "yapi_ruhsat_10bin",
        oran(ruhsat, nuf, carpan=10000.0), "adet", YAPI,
        "ruhsat verilen daire / nüfus × 10.000", ondalik=1)
    yaz("Yapı Kullanma İzni Verilen Daire Sayısı", "yapi_izin",
        blok_devrik(yp, 2, 4, 85, 168), "adet", YAPI)

    # ---------------- göç nedeni
    gn = "Göç etme nedenine göre illerin aldığı göç.xls"
    NEDEN = [
        ("İşe başlamak", "goc_is", "İş İçin Göç Alan"),
        ("Eğitim", "goc_egitim", "Eğitim İçin Göç Alan"),
        ("Medeni durum", "goc_evlilik", "Evlilik Nedeniyle Göç Alan"),
        ("Daha iyi konut", "goc_konut", "Daha İyi Konut İçin Göç Alan"),
        ("Tayin", "goc_tayin", "Tayin/İş Değişikliğiyle Göç Alan"),
    ]
    for etiket, slug, ad in NEDEN:
        d = sutun_basligi(gn, 3, etiket, il_sut=1, yil_sut=0, bas_satir=4)
        if d:
            yaz(ad, slug, d, "kişi", GOC)

    print("bitti")


if __name__ == "__main__":
    main()
