#!/usr/bin/env python3
"""TÜİK klasik XLS tabloları için okuyucu.

Kalıp: üstte 2-5 satır başlık, sonra yılların olduğu bir satır,
ardından her satırda bir il. LibreOffice ile CSV'ye çevrilir.
"""
import csv
import glob
import os
import re
import subprocess

HAM = os.environ.get("TUIK_HAM", "/mnt/user-data/uploads/İSTATİSTİK YOUTUBE CLAUDE PROJELER/EveryYearCounts-TR/tuik-ham")
TMP = "/tmp/tuik_csv2"
os.makedirs(TMP, exist_ok=True)

ATLA = {"", "Türkiye", "Türkiye - Turkiye", "Toplam-Total", "Toplam - Total",
        "Toplam", "Total", "Türkiye-Turkiye"}
YIL = re.compile(r"^\s*((?:19|20)\d{2})")


ONBELLEK = [TMP, "/tmp/x2"]


def csvye(dosya):
    yol = os.path.join(HAM, dosya)
    kok = os.path.splitext(os.path.basename(dosya))[0]
    for d in ONBELLEK:                      # daha önce çevrilmişse tekrar çevirme
        h = os.path.join(d, kok + ".csv")
        if os.path.exists(h):
            return h
    hedef = os.path.join(TMP, kok)
    os.makedirs(hedef, exist_ok=True)
    if not glob.glob(hedef + "/*.csv"):
        subprocess.run(["soffice", "--headless", "--convert-to", "csv",
                        "--outdir", hedef, yol],
                       check=False, capture_output=True, timeout=300)
    c = sorted(glob.glob(hedef + "/*.csv"))
    return c[0] if c else None


def sayi(s):
    if s is None:
        return None
    s = s.replace("\xa0", " ").strip()
    if s in ("", "-", "–", ".", ":", "...", "r", "(r)"):
        return None
    neg = s.startswith("-")
    s = s.lstrip("-").strip().replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    elif s.count(",") and s.count("."):
        s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _il_temiz(s):
    s = s.strip()
    s = re.sub(r"\s*-\s*[A-Za-z].*$", "", s)      # "Adana - Adana" -> "Adana"
    s = re.sub(r"\(\d+\)$", "", s).strip()
    return s


def genis(dosya, alt_kaydir=0):
    """Yıllar satırda başlık, iller satırlarda.  -> {il: {yil: deger}}"""
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    bas, yil_sut = None, {}
    for i, r in enumerate(rows[:14]):
        bul = {}
        for j, c in enumerate(r):
            m = YIL.match(c or "")
            if m:
                bul[j] = int(m.group(1))
        if len(bul) >= 5:
            bas, yil_sut = i, bul
            break
    if bas is None:
        return {}
    out = {}
    for r in rows[bas + 1 + alt_kaydir:]:
        if not r:
            continue
        ad = _il_temiz(r[0] if r[0].strip() else "")
        if not ad or ad in ATLA:
            continue
        for j, y in yil_sut.items():
            if j < len(r):
                v = sayi(r[j])
                if v is not None:
                    out.setdefault(ad, {})[y] = v
    return out


def iki_kademeli(dosya, alt_etiket):
    """Üstte yıl, altta 'Erkek/Kadın' gibi ikinci kademe olan tablolar."""
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    yil_satiri = alt_satiri = None
    for i, r in enumerate(rows[:12]):
        bul = sum(1 for c in r if YIL.match(c or ""))
        if bul >= 3 and yil_satiri is None:
            yil_satiri = i
        elif yil_satiri is not None and any(alt_etiket in (c or "") for c in r):
            alt_satiri = i
            break
    if yil_satiri is None or alt_satiri is None:
        return {}
    yillar = {}
    son = None
    for j, c in enumerate(rows[yil_satiri]):
        m = YIL.match(c or "")
        if m:
            son = int(m.group(1))
        yillar[j] = son
    out = {}
    for r in rows[alt_satiri + 1:]:
        if not r:
            continue
        ad = _il_temiz(r[0])
        if not ad or ad in ATLA:
            continue
        for j, c in enumerate(rows[alt_satiri]):
            if alt_etiket in (c or "") and j < len(r) and yillar.get(j):
                v = sayi(r[j])
                if v is not None:
                    out.setdefault(ad, {})[yillar[j]] = v
    return out


def devrik(dosya, satir_filtre=None, yil_sut=1):
    """İller SÜTUNLARDA, yıllar satırlarda olan tablolar (yapı belgesi gibi)."""
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    bas = None
    for i, r in enumerate(rows[:10]):
        if sum(1 for c in r if c.strip() in ("Adana", "Adıyaman", "Ankara")) >= 2:
            bas = i
            break
    if bas is None:
        return {}
    iller = {j: _il_temiz(c) for j, c in enumerate(rows[bas])
             if c.strip() and c.strip() not in ATLA and not YIL.match(c)}
    out = {}
    etiket = None
    for r in rows[bas + 1:]:
        if not r or len(r) <= yil_sut:
            continue
        if r[0].strip():
            etiket = r[0].strip()
        if satir_filtre and (etiket or "") != satir_filtre:
            continue
        m = YIL.match(r[yil_sut] or "")
        if not m:
            continue
        yil = int(m.group(1))
        for j, il in iller.items():
            if j < len(r):
                v = sayi(r[j])
                if v is not None:
                    out.setdefault(il, {})[yil] = v
    return out


def blok_devrik(dosya, baslik_satiri, ilk_il_sutunu, bas, son,
                yil_sut=1, ceyrek_sut=2):
    """İller SÜTUNDA, satırlar (belge, yıl, çeyrek).  [bas, son) satır aralığı.

    Çeyrek sütunu boş olan satırlar = yıllık toplam.
    """
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    hdr = rows[baslik_satiri]
    iller = {j: _il_temiz(c) for j, c in enumerate(hdr)
             if j >= ilk_il_sutunu and c.strip() and _il_temiz(c) not in ATLA}
    out = {}
    for r in rows[bas:son]:
        if len(r) <= ceyrek_sut or r[ceyrek_sut].strip():
            continue
        m = YIL.match(r[yil_sut] or "")
        if not m:
            continue
        yil = int(m.group(1))
        for j, il in iller.items():
            if j < len(r):
                v = sayi(r[j])
                if v is not None:
                    out.setdefault(il, {})[yil] = v
    return out


def sutun_basligi(dosya, baslik_satiri, etiket, il_sut=1, yil_sut=0,
                  bas_satir=None, esit=False):
    """Yıl sütunu ileri doldurmalı, iller satırda, sütun başlığıyla seçim.

    (göç nedeni tablosu: satır = (yıl, il), sütun = göç nedeni)
    """
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    hdr = rows[baslik_satiri]
    sec = None
    for j, c in enumerate(hdr):
        t = " ".join((c or "").split())
        if (t == etiket) if esit else t.startswith(etiket):
            sec = j
            break
    if sec is None:
        raise KeyError(f"{etiket} sütunu yok: {[' '.join(c.split())[:30] for c in hdr]}")
    out, yil = {}, None
    for r in rows[(bas_satir if bas_satir is not None else baslik_satiri + 1):]:
        if len(r) <= max(sec, il_sut):
            continue
        if r[yil_sut].strip():
            m = re.findall(r"(\d{4})", r[yil_sut])
            yil = int(m[-1]) if m else yil
        ad = _il_temiz(r[il_sut])
        if yil is None or not ad or ad in ATLA:
            continue
        v = sayi(r[sec])
        if v is not None:
            out.setdefault(ad, {})[yil] = v
    return out


def il_ileri_kategori(dosya, baslik_satiri, kategori, il_sut=0, kat_sut=1,
                      ilk_deger_sutunu=3):
    """İl adı ileri doldurmalı, alt satırlarda kategori olan tablolar.

    (sağlık personeli: 'Adana' satırı boş, altındaki 'Toplam hekim' satırında
     yıllara göre değerler var.)
    """
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    yil_sut = {}
    for j, c in enumerate(rows[baslik_satiri]):
        if j >= ilk_deger_sutunu:
            m = YIL.match(c or "")
            if m:
                yil_sut[j] = int(m.group(1))
    out, il = {}, None
    for r in rows[baslik_satiri + 1:]:
        if not r:
            continue
        if len(r) > il_sut and r[il_sut].strip():
            il = _il_temiz(r[il_sut])
        if not il or il in ATLA:
            continue
        if len(r) <= kat_sut or kategori not in (r[kat_sut] or ""):
            continue
        for j, y in yil_sut.items():
            if j < len(r):
                v = sayi(r[j])
                if v is not None:
                    out.setdefault(il, {})[y] = v
    return out


def yil_ileri_doldur(dosya, il_sut=1, deger_sut=2, yil_sut=0, bas_satir=3):
    """Yıl sütunu ileri doldurmalı, iller satırda (göç nedeni tablosu gibi)."""
    p = csvye(dosya)
    if not p:
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8")))
    out, yil = {}, None
    for r in rows[bas_satir:]:
        if len(r) <= max(il_sut, deger_sut, yil_sut):
            continue
        if r[yil_sut].strip():
            m = re.findall(r"(\d{4})", r[yil_sut])
            yil = int(m[-1]) if m else None
        ad = _il_temiz(r[il_sut])
        if yil is None or not ad or ad in ATLA:
            continue
        v = sayi(r[deger_sut])
        if v is not None:
            out.setdefault(ad, {})[yil] = v
    return out
