#!/usr/bin/env python3
"""TÜİK ham dosyalarını ortak formata çevirir.

Çıktı: veri_il/<gosterge>.json  →  {"iller": {"Adana": {"2008": 2026319, ...}, ...},
                                    "ad": "...", "birim": "...", "kaynak": "..."}

TÜİK'in üç farklı dosya düzeni var, üçü de burada ele alınıyor:
  1. SDMX CSV   (nüfus)      — uzun format, ";" ayraçlı, BOM'lu
  2. Göç XLS    (göç)        — yıl sütunu ileri doldurmalı, iller satırda
  3. GSYH XLS   (gsyh)       — bölge kodu ileri doldurmalı, yıl sütunda, 81 il = 5 karakterli kod

XLS'ler LibreOffice ile CSV'ye çevriliyor (tek seferlik; sonuç repoya JSON olarak gömülür,
GitHub Actions'ta LibreOffice gerekmez).
"""
import csv
import glob
import json
import os
import re
import subprocess
import sys

HAM = os.environ.get("TUIK_HAM", "/mnt/user-data/uploads/İSTATİSTİK YOUTUBE CLAUDE PROJELER/EveryYearCounts-TR/tuik-ham")
OUT = os.environ.get("VERI_IL", "/home/claude/eyc-tr/veri_il")
TMP = "/tmp/tuik_csv"
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

ILLER = None  # names_il.py'dan doldurulur (81 il)


def sayi(s):
    """'  1 234 567 ' -> 1234567.0 ; '- 4 234' -> -4234 ; '-' / '' -> None"""
    if s is None:
        return None
    s = s.replace("\xa0", " ").strip()
    if s in ("", "-", "–", ".", ":", "..."):
        return None
    neg = s.startswith("-")
    s = s.lstrip("-").strip()
    s = s.replace(" ", "")
    # TUIK ondalik ayraci "." veya "," olabiliyor; binlik ayraci bosluk
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def xls2csv(path):
    """LibreOffice ile CSV'ye çevirir, üretilen dosyaların yollarını döner."""
    base = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(TMP, base)
    os.makedirs(out, exist_ok=True)
    if not glob.glob(out + "/*.csv"):
        subprocess.run(["soffice", "--headless", "--convert-to", "csv",
                        "--outdir", out, path],
                       check=False, capture_output=True, timeout=300)
    return sorted(glob.glob(out + "/*.csv"))


def yaz(ad, dosya, iller, birim, kaynak, not_="", ondalik=None):
    """Kompakt biçim: yıl anahtarları tekrar etmesin diye dizi olarak yazılır.
       {"y0": 2000, "iller": {"Adana": [v, v, null, ...]}}"""
    iller = {k: {int(y): v for y, v in d.items() if v is not None}
             for k, d in iller.items()}
    iller = {k: d for k, d in iller.items() if len(d) >= 3}
    yillar = sorted({y for d in iller.values() for y in d})
    y0, y1 = yillar[0], yillar[-1]
    if ondalik is None:
        ondalik = (2 if birim in ("%", "\u2030", "\u00e7ocuk")
                   else 1 if birim in ("TL", "ya\u015f") else 0)
    def yuvarla(v):
        return round(v, ondalik) if ondalik else int(round(v))
    diziler = {k: [yuvarla(d[y]) if y in d else None for y in range(y0, y1+1)]
               for k, d in iller.items()}
    payload = {"ad": ad, "birim": birim, "kaynak": kaynak, "not": not_,
               "y0": y0, "iller": diziler}
    p = os.path.join(OUT, dosya + ".json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"  {dosya:22s} {len(iller):3d} il  {y0}-{y1}  ({y1-y0+1} yıl)")
    return {"iller": iller, "y0": y0}


# ------------------------------------------------------------------ 1. NÜFUS
def nufus():
    p = os.path.join(HAM, "Yıllara Göre İl Nüfusları (TR,DF_ADNKS_T30,1.1).csv")
    iller = {}
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            il = r["İkamet edilen yer"].strip()
            if il in ("Toplam", "Türkiye", ""):
                continue
            v = sayi(r["Gözlem"])
            if v is None:
                continue
            iller.setdefault(il, {})[int(r["Zaman"])] = v
    return yaz("Nüfus", "nufus", iller, "kişi",
               "TÜİK · Adrese Dayalı Nüfus Kayıt Sistemi")


# ------------------------------------------------------------------ 2. GÖÇ
def goc():
    src = os.path.join(HAM, "İllerin Aldığı Göç, Verdiği Göç, Net Göç ve Net Göç Hızı.xls")
    csvs = xls2csv(src)
    if not csvs:
        print("  ! göç dosyası çevrilemedi"); return
    rows = list(csv.reader(open(csvs[0], encoding="utf-8")))
    # sutunlar: 0 yil, 1 il, 2 toplam nufus, 3 aldigi, 4 verdigi, 5 net, 6 net hizi
    alan, veren, net, hiz = {}, {}, {}, {}
    yil = None
    for r in rows[3:]:
        if len(r) < 7:
            continue
        if r[0].strip():
            m = re.findall(r"(\d{4})", r[0])
            yil = int(m[-1]) if m else None
        il = r[1].strip()
        if yil is None or not il or il.startswith("Toplam"):
            continue
        for hedef, idx in ((alan, 3), (veren, 4), (net, 5), (hiz, 6)):
            v = sayi(r[idx])
            if v is not None:
                hedef.setdefault(il, {})[yil] = v
    K = "TÜİK · İç Göç İstatistikleri"
    yaz("Aldığı Göç", "goc_alan", alan, "kişi", K)
    yaz("Verdiği Göç", "goc_veren", veren, "kişi", K)
    yaz("Net Göç", "goc_net", net, "kişi", K)
    yaz("Net Göç Hızı", "goc_net_hizi", hiz, "‰", K)


# ------------------------------------------------------------------ 3. GSYH
def gsyh():
    src = os.path.join(HAM, "İl bazında gayrisafi yurt içi hasıla, iktisadi faaliyet kollarına (A10) göre, cari fiyatlarla (değer).xls")
    csvs = xls2csv(src)
    if not csvs:
        print("  ! gsyh dosyası çevrilemedi"); return
    rows = list(csv.reader(open(csvs[0], encoding="utf-8")))
    GSYH_COL = 16          # "GSYH / GDP" sutunu
    TARIM, SANAYI = 3, 4
    kod = ad = None
    top, tarim, sanayi = {}, {}, {}
    for r in rows[4:]:
        if len(r) <= GSYH_COL:
            continue
        if r[0].strip():
            kod, ad = r[0].strip(), r[1].strip()
        if kod is None or len(kod) != 5:      # 5 karakterli kod = il (Düzey 3)
            continue
        y = sayi(r[2])
        if y is None:
            continue
        y = int(y)
        for hedef, idx in ((top, GSYH_COL), (tarim, TARIM), (sanayi, SANAYI)):
            v = sayi(r[idx])
            if v is not None:
                hedef.setdefault(ad, {})[y] = v * 1000     # bin TL -> TL
    K = "TÜİK · Bölgesel Hesaplar"
    p = yaz("Gayrisafi Yurt İçi Hasıla", "gsyh", top, "TL", K)

    # kisi basina gelir = gsyh / nufus
    nj = json.load(open(os.path.join(OUT, "nufus.json"), encoding="utf-8"))
    ny0 = nj["y0"]
    nuf = {il: {ny0+i: v for i, v in enumerate(a) if v is not None}
           for il, a in nj["iller"].items()}
    kb = {}
    for il, d in p["iller"].items():
        if il not in nuf:
            continue
        for y, v in d.items():
            n = nuf[il].get(y)
            if n:
                kb.setdefault(il, {})[y] = v / n
    yaz("Kişi Başına Gelir", "gsyh_kisi_basi", kb, "TL", K,
        "GSYH / nüfus olarak hesaplandı")

    # tarim ve sanayinin payi
    pay_t, pay_s = {}, {}
    for il, d in top.items():
        for y, v in d.items():
            if v:
                if il in tarim and y in tarim[il]:
                    pay_t.setdefault(il, {})[y] = tarim[il][y] / v * 100
                if il in sanayi and y in sanayi[il]:
                    pay_s.setdefault(il, {})[y] = sanayi[il][y] / v * 100
    yaz("Tarımın Ekonomideki Payı", "gsyh_tarim_payi", pay_t, "%", K)
    yaz("Sanayinin Ekonomideki Payı", "gsyh_sanayi_payi", pay_s, "%", K)


if __name__ == "__main__":
    print("TÜİK dönüştürücü")
    nufus()
    goc()
    gsyh()
    print("bitti ->", OUT)
