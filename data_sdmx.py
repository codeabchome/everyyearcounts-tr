#!/usr/bin/env python3
"""TÜİK SDMX CSV okuyucu — ";" ayraçlı, uzun format, BOM'lu.

Bütün SDMX dosyaları aynı iskelette: birkaç boyut sütunu + "Zaman" + "Gözlem".
Sütun adları bazen "(KOD)" ekiyle geliyor, o yüzden başlangıçla eşleştiriyoruz.
"""
import csv
import os

HAM = os.environ.get("TUIK_HAM", "/mnt/user-data/uploads/İSTATİSTİK YOUTUBE CLAUDE PROJELER/EveryYearCounts-TR/tuik-ham")


def sayi(s):
    if s is None:
        return None
    s = s.replace("\xa0", " ").strip()
    if s in ("", "-", "–", ".", ":", "...", "Uygulanabilir değil"):
        return None
    neg = s.startswith("-")
    s = s.lstrip("-").strip().replace(" ", "")
    if s.count(",") == 1:
        s = s.replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _sut(hdr, bas):
    """Sütun adını bulur. ÖNCE tam eşleşme, sonra 'bas (KOD)' biçimi.
       (Tam eşleşme şart: 'Gözlem' ile 'Gözlem Sıklığı' karışmasın.)"""
    for h in hdr:
        if h == bas:
            return h
    for h in hdr:
        if h.startswith(bas + " (") or h.startswith(bas + "("):
            return h
    for h in hdr:
        if h.startswith(bas):
            return h
    raise KeyError(f"{bas} sütunu yok; var olanlar: {hdr}")


def oku(dosya, varlik_sutunu="İkamet edilen yer", filtre=None, yil_sutunu="Zaman",
        yil_don=None, atla=("Toplam", "Türkiye", "")):
    """-> {varlik: {yil: deger}}

    filtre: {"sütun başlangıcı": "değer" | (lambda v: bool)}
    yil_don: "2005-12" gibi zamanları yıla çevirmek için fonksiyon; None -> int()
    """
    yol = os.path.join(HAM, dosya)
    out = {}
    with open(yol, encoding="utf-8-sig") as f:
        rd = csv.reader(f, delimiter=";")
        hdr = next(rd)
        i_var = hdr.index(_sut(hdr, varlik_sutunu))
        i_yil = hdr.index(_sut(hdr, yil_sutunu))
        i_deg = hdr.index(_sut(hdr, "Gözlem"))
        kontrol = []
        for bas, bek in (filtre or {}).items():
            kontrol.append((hdr.index(_sut(hdr, bas)), bek))
        for row in rd:
            if len(row) <= max(i_var, i_yil, i_deg):
                continue
            ok = True
            for idx, bek in kontrol:
                v = row[idx]
                if callable(bek):
                    if not bek(v):
                        ok = False; break
                elif v != bek:
                    ok = False; break
            if not ok:
                continue
            ad = row[i_var].strip()
            if ad in atla:
                continue
            z = row[i_yil].strip()
            try:
                yil = yil_don(z) if yil_don else int(z)
            except (ValueError, TypeError):
                continue
            if yil is None:
                continue
            d = sayi(row[i_deg])
            if d is None:
                continue
            out.setdefault(ad, {})[yil] = d
    return out


def oran(pay, payda, carpan=100.0):
    """İki seriyi bölüp yüzde/binde üretir."""
    out = {}
    for ad, d in pay.items():
        if ad not in payda:
            continue
        for y, v in d.items():
            t = payda[ad].get(y)
            if t:
                out.setdefault(ad, {})[y] = v / t * carpan
    return out
