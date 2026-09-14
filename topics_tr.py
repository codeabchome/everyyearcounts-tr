#!/usr/bin/env python3
"""Konu kuyruğu — Türkiye Kaçıncı?

İki katman:
  IL_KONULARI    — 81 il, TÜİK verisi (veri_il/*.json). Kanalın omurgası.
  ULKE_KONULARI  — topics_tr.json varsa oradan (discover_tr.py üretir).

Kuyruk merak sırasına göre; aynı gösterge arka arkaya gelmesin diye
konular tematik olarak serpiştirilir.
"""
import json
import os

BURADA = os.path.dirname(os.path.abspath(__file__))


# (dosya, baslik1, baslik2, ters, tema)
#   ters=True  -> en DÜŞÜK 10
IL_KONULARI = [
    # --- nüfus
    ("nufus",            "EN KALABALIK",        "10 İL",            False, "nufus"),
    ("nufus",            "NÜFUSU EN AZ",        "10 İL",            True,  "nufus"),
    # --- göç
    ("goc_alan",         "EN ÇOK GÖÇ ALAN",     "10 İL",            False, "goc"),
    ("goc_veren",        "EN ÇOK GÖÇ VEREN",    "10 İL",            False, "goc"),
    ("goc_net",          "NET GÖÇÜ EN YÜKSEK",  "10 İL",            False, "goc"),
    ("goc_net",          "EN ÇOK NÜFUS",        "KAYBEDEN 10 İL",   True,  "goc"),
    ("goc_net_hizi",     "NET GÖÇ HIZI",        "EN YÜKSEK 10 İL",  False, "goc"),
    # --- ekonomi
    ("gsyh",             "EKONOMİSİ EN BÜYÜK",  "10 İL",            False, "ekonomi"),
    ("gsyh_kisi_basi",   "KİŞİ BAŞINA GELİRİ",  "EN YÜKSEK 10 İL",  False, "ekonomi"),
    ("gsyh_kisi_basi",   "KİŞİ BAŞINA GELİRİ",  "EN DÜŞÜK 10 İL",   True,  "ekonomi"),
    ("gsyh_tarim_payi",  "EKONOMİSİ EN ÇOK",    "TARIMA DAYALI 10 İL", False, "ekonomi"),
    ("gsyh_sanayi_payi", "EKONOMİSİ EN ÇOK",    "SANAYİYE DAYALI 10 İL", False, "ekonomi"),
]

TEMA_SIRASI = ["nufus", "goc", "ekonomi"]


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
    ok = []
    for dosya, b1, b2, ters, tema in IL_KONULARI:
        yol = os.path.join(BURADA, "veri_il", dosya + ".json")
        if not os.path.exists(yol):
            continue
        veri = json.load(open(yol, encoding="utf-8"))
        ok.append({
            "id": f"il:{dosya}:{'dusuk' if ters else 'yuksek'}",
            "tur": "il",
            "veri": os.path.join("veri_il", dosya + ".json"),
            "baslik1": b1, "baslik2": b2, "ters": ters, "tema": tema,
            "gosterge": veri["ad"], "kaynak": veri["kaynak"],
        })
    return _serpistir(ok)


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
            "ters": t["direction"] == "bottom",
        })
    return out


def build():
    """Tam kuyruk: önce il konuları (sınır içi öncelik), sonra ülke konuları."""
    return il_konulari() + ulke_konulari()


if __name__ == "__main__":
    k = build()
    print(f"{len(k)} konu")
    for i, t in enumerate(k, 1):
        print(f"{i:3d}. [{t['tema']:8s}] {t.get('baslik1','')} {t.get('baslik2','')}".rstrip())
