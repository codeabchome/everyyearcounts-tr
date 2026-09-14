#!/usr/bin/env python3
"""veri_il/ klasörünü SDMX kaynaklı göstergelerle genişletir.

data_il.py (nüfus, göç, GSYH) çalıştıktan SONRA çalıştırılır.
"""
import json
import os

from data_sdmx import oku, oran
from data_il import yaz

ADNKS = "TÜİK · Adrese Dayalı Nüfus Kayıt Sistemi"
TASIT = "TÜİK · Motorlu Kara Taşıtları"
TRAFIK = "TÜİK · Trafik Kaza İstatistikleri"

F = {
 "ortanca":   "İllere ve Cinsiyete Göre Ortanca Yaş (TR,DF_ADNKS_T23,1.1).csv",
 "yabanci":   "İllere ve cinsiyete göre yabancı nüfus (TR,DF_ADNKS_T12,1.1).csv",
 "yogunluk":  "İllere Göre Nüfus Yoğunluğu (TR,DF_ADNKS_T20,1.1).csv",
 "artis":     "Yıllara Göre İllerin Yıllık Nüfus Artış Hızı ve Nüfus Yoğunluğu (TR,DF_ADNKS_T29,1.1).csv",
 "bagimlilik":"İllere Göre Yaş Bağımlılık Oranı (TR,DF_ADNKS_T24,1.1).csv",
 "yasgrubu":  "Geniş Yaş Gruplarına Göre İl Nüfusları (TR,DF_ADNKS_T35,1.1).csv",
 "kentkir":   "Kent-kır sınıflaması ve cinsiyete göre il nüfusları (TR,DF_ADNKS_T37,1.1).csv",
 "hanehalki": "İllere Göre Ortalama Hanehalkı Büyüklüğü (TR,DF_ADNKS_T25,1.1).csv",
 "tasit":     "İllere Göre Motorlu Kara Taşıtları Sayısı (TR,DF_MOTORLU_KARA_TASIT_ILLER_V3,1.0).csv",
 "kaza":      "İllere Göre Trafik Kaza, Ölü ve Yaralı Sayısı (TR,DF_TRAFIK_KAZA_OLU_YARALI_V2,1.0).csv",
 "memleket":  "İkamet edilen ile göre nüfus kütüğüne kayıtlı olunan il (TR,DF_ADNKS_T09,1.1).csv",
}

VERI_IL = os.environ.get("VERI_IL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri_il"))


def nufus_serisi():
    j = json.load(open(os.path.join(VERI_IL, "nufus.json"), encoding="utf-8"))
    y0 = j["y0"]
    return {il: {y0 + i: v for i, v in enumerate(a) if v is not None}
            for il, a in j["iller"].items()}


def main():
    nuf = nufus_serisi()

    # --- yaş yapısı
    yaz("Ortanca Yaş", "ortanca_yas",
        oku(F["ortanca"], filtre={"Cinsiyet": "Toplam"}), "yaş", ADNKS)

    yaz("Yabancı Nüfus", "yabanci_nufus",
        oku(F["yabanci"], filtre={"Cinsiyet": "Toplam"}), "kişi", ADNKS)

    yaz("Nüfus Yoğunluğu", "nufus_yogunlugu",
        oku(F["yogunluk"]), "kişi/km²", ADNKS)

    yaz("Yıllık Nüfus Artış Hızı", "nufus_artis_hizi",
        oku(F["artis"], filtre={"ADNKS Gösterge": lambda v: v.startswith("Yıllık nüfus artış")}),
        "‰", ADNKS)

    yaz("Yaşlı Bağımlılık Oranı", "yasli_bagimlilik",
        oku(F["bagimlilik"], filtre={"ADNKS Gösterge": lambda v: v.startswith("Yaşlı")}),
        "%", ADNKS)

    # yaş gruplarından oran türet
    toplam = oku(F["yasgrubu"], filtre={"Yaş Grubu": "Toplam"})
    yasli = oku(F["yasgrubu"], filtre={"Yaş Grubu": "65+"})
    cocuk = oku(F["yasgrubu"], filtre={"Yaş Grubu": "< 14"})
    yaz("65 Yaş Üstü Nüfus Oranı", "yasli_orani", oran(yasli, toplam), "%", ADNKS)
    yaz("Çocuk Nüfus Oranı", "cocuk_orani", oran(cocuk, toplam), "%", ADNKS)
    yaz("65 Yaş Üstü Nüfus", "yasli_nufus", yasli, "kişi", ADNKS)

    # kent-kır
    kir = oku(F["kentkir"], filtre={"Cinsiyet": "Toplam", "ADNKS Gösterge": "Kır nüfusu"})
    yogun = oku(F["kentkir"], filtre={"Cinsiyet": "Toplam", "ADNKS Gösterge": "Yoğun kent nüfus"})
    orta = oku(F["kentkir"], filtre={"Cinsiyet": "Toplam", "ADNKS Gösterge": "Orta kent nüfusu"})
    top_kk = {}
    for kaynak in (kir, yogun, orta):
        for il, d in kaynak.items():
            for y, v in d.items():
                top_kk.setdefault(il, {})[y] = top_kk.setdefault(il, {}).get(y, 0) + v
    yaz("Kırda Yaşayan Nüfus Oranı", "kir_orani", oran(kir, top_kk), "%", ADNKS)

    yaz("Ortalama Hanehalkı Büyüklüğü", "hanehalki",
        oku(F["hanehalki"]), "kişi", ADNKS, ondalik=2)

    # --- taşıtlar (yıl sonu = Aralık)
    def tasit(tur):
        return oku(F["tasit"], varlik_sutunu="Coğrafi Kapsam",
                   filtre={"Araç Türü": tur, "Ölçü Birimi": "Sayı", "Ay": "Aralık"},
                   yil_don=lambda z: int(z.split("-")[0]))
    oto = tasit("Otomobil")
    yaz("Otomobil Sayısı", "otomobil", oto, "adet", TASIT)
    yaz("Traktör Sayısı", "traktor", tasit("Traktör"), "adet", TASIT)
    yaz("Motosiklet Sayısı", "motosiklet", tasit("Motosiklet"), "adet", TASIT)
    yaz("Kamyon Sayısı", "kamyon", tasit("Kamyon"), "adet", TASIT)
    yaz("1000 Kişiye Düşen Otomobil", "otomobil_1000",
        oran(oto, nuf, carpan=1000.0), "adet", TASIT,
        "otomobil sayısı / nüfus × 1000", ondalik=1)

    # --- trafik
    kaza = oku(F["kaza"], varlik_sutunu="Coğrafi Kapsam",
               filtre={"Trafik Kaza Gösterge": "Toplam Kaza Sayısı"})
    yaz("Trafik Kazası Sayısı", "trafik_kaza", kaza, "adet", TRAFIK)
    yaz("10 Bin Kişiye Düşen Trafik Kazası", "trafik_kaza_10bin",
        oran(kaza, nuf, carpan=10000.0), "adet", TRAFIK,
        "kaza sayısı / nüfus × 10.000", ondalik=1)

    # --- memleket: büyük şehirlerde kimler yaşıyor
    SLUG = {"İstanbul": "istanbul", "Ankara": "ankara", "İzmir": "izmir",
            "Bursa": "bursa", "Antalya": "antalya", "Kocaeli": "kocaeli",
            "Adana": "adana", "Mersin": "mersin"}
    for sehir in SLUG:
        d = oku(F["memleket"], varlik_sutunu="Nüfus kütüğüne kayıtlı",
                filtre={"İkamet edilen yer": sehir})
        d.pop(sehir, None)          # kendi ili hariç — "nereli" sorusu bu
        if d:
            yaz(f"{sehir} Nüfusunun Memleketi", "memleket_" + SLUG[sehir],
                d, "kişi", ADNKS, f"{sehir} nüfus kütüğüne kayıtlı olanlar hariç")


if __name__ == "__main__":
    main()
