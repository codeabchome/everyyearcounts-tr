#!/usr/bin/env python3
"""Memleket matrisinden iki yönlü konu üretir (81 + 81 gösterge).

TÜİK "İkamet edilen ile göre nüfus kütüğüne kayıtlı olunan il" tablosu
81×81'lik bir matris. İki soruya da cevap veriyor:

  memleket_<il>  : "<İl>'de yaşayanlar nereli?"        (o ilde ikamet edenlerin memleketi)
  nereli_<il>    : "<İl>'liler en çok nerede yaşıyor?" (memleketi o il olanların ikameti)

Her iki yönde de öznenin kendi ili listeden çıkarılır — soru zaten "başka
nerede" sorusu, yoksa her videoda ilk sırada ilin kendisi çıkar.
"""
import json
import os

from data_sdmx import oku
from data_il import yaz

DOSYA = "İkamet edilen ile göre nüfus kütüğüne kayıtlı olunan il (TR,DF_ADNKS_T09,1.1).csv"
ADNKS = "TÜİK · Adrese Dayalı Nüfus Kayıt Sistemi"

VERI_IL = os.environ.get(
    "VERI_IL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "veri_il"))

# ASCII slug için Türkçe harf dönüşümü
_HARF = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                       "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s",
                       "Ü": "u", "â": "a"})


def slug(il):
    return il.replace("İ", "i").replace("I", "i").lower().translate(_HARF).replace(" ", "-")


SESLI = "aeıioöuü"
KALIN = "aıou"          # bu ünlülerden sonra -lar
_EK = {"a": "lı", "ı": "lı", "o": "lu", "u": "lu",
       "e": "li", "i": "li", "ö": "lü", "ü": "lü"}


def ilgi(il):
    """'Sivas' -> 'Sivaslılar',  'Rize' -> 'Rizeliler',  'Ordu' -> 'Ordulular'."""
    son = next((h for h in reversed(il.lower().translate(
        str.maketrans({"İ": "i", "I": "ı"}))) if h in SESLI), "a")
    ek = _EK[son]
    cogul = "lar" if ek[-1] in KALIN else "ler"
    return il + ek + cogul


def matris():
    """Dosyayı TEK geçişte okur -> {(ikamet, memleket): {yil: deger}}

    (14 MB'lık dosyayı 162 kez taramamak için; öyle yapınca dakikalarca sürüyor.)
    """
    import csv
    from data_sdmx import HAM, _sut, sayi
    yol = os.path.join(HAM, DOSYA)
    with open(yol, encoding="utf-8-sig") as f:
        rd = csv.reader(f, delimiter=";")
        hdr = next(rd)
        i_ik = hdr.index(_sut(hdr, "İkamet edilen yer"))
        i_me = hdr.index(_sut(hdr, "Nüfus kütüğüne kayıtlı"))
        i_yl = hdr.index(_sut(hdr, "Zaman"))
        i_dg = hdr.index(_sut(hdr, "Gözlem"))
        m, iller = {}, set()
        atla = {"Toplam", "Türkiye", ""}
        for row in rd:
            if len(row) <= max(i_ik, i_me, i_yl, i_dg):
                continue
            ik, me = row[i_ik].strip(), row[i_me].strip()
            if ik in atla or me in atla:
                continue
            try:
                yil = int(row[i_yl].strip())
            except ValueError:
                continue
            d = sayi(row[i_dg])
            if d is None:
                continue
            m.setdefault((ik, me), {})[yil] = d
            iller.add(ik)
            iller.add(me)
    return m, sorted(iller)


def main():
    m, iller = matris()
    print(f"{len(iller)} il, {len(m)} hücre")

    ozet = {}
    for il in iller:
        # 1) il'de yaşayanlar nereli
        d = {me: v for (ik, me), v in m.items() if ik == il and me != il}
        if d:
            yaz(f"{il} Nüfusunun Memleketi", "memleket_" + slug(il), d, "kişi", ADNKS,
                f"{il}'de ikamet edip nüfusa {il} dışında kayıtlı olanlar")

        # 2) memleketi il olanlar nerede yaşıyor
        t = {ik: v for (ik, me), v in m.items() if me == il and ik != il}
        icerde = m.get((il, il), {})
        if t:
            yaz(f"{il} Nüfusuna Kayıtlı Kişi Sayısı", "nereli_" + slug(il), t, "kişi", ADNKS,
                f"nüfusa {il}'e kayıtlı olup {il} dışında yaşayanlar")
            # diaspora oranı: dışarıda yaşayan / toplam kayıtlı  (kademe sırası için)
            sy = max(y for d2 in list(t.values()) + [icerde] if d2 for y in d2)
            dis = sum(d2.get(sy, 0) for d2 in t.values())
            ic = icerde.get(sy, 0)
            ozet[il] = {"disari": dis, "icerde": ic,
                        "oran": dis / (dis + ic) * 100 if dis + ic else 0}

    with open(os.path.join(VERI_IL, "_memleket_ozet.json"), "w", encoding="utf-8") as f:
        json.dump(ozet, f, ensure_ascii=False)
    print("özet yazıldı:", len(ozet))


if __name__ == "__main__":
    main()
