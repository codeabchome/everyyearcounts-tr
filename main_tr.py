#!/usr/bin/env python3
"""Türkiye Kaçıncı? — orkestratör.

Akış:  kuyruktan konu seç → render → müzik ekle → metadata → YouTube'a yükle
       → state.json güncelle

Elle test (yükleme yapmadan):
    python main_tr.py --kuru
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import date

import renderer_tr
import topics_tr

BURADA = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BURADA, "state_tr.json")
SES_DIR = os.path.join(BURADA, "ses")
CIKTI = os.path.join(BURADA, "cikti")
os.makedirs(CIKTI, exist_ok=True)

MAX_HATA = 3          # üst üste 3 kez patlayan konu kalıcı atlanır
DENEME = 6            # bir çalıştırmada en fazla kaç konu denensin


# ---------------------------------------------------------------- state
def state_oku():
    if os.path.exists(STATE):
        try:
            s = json.load(open(STATE, encoding="utf-8"))
        except Exception:
            s = {}
    else:
        s = {}
    s.setdefault("yayinlanan", [])
    s.setdefault("hatali", {})
    s.setdefault("tur", 0)
    s.setdefault("log", [])
    return s


def state_yaz(s):
    s["log"] = s["log"][-200:]
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def sonraki_konular(s):
    kuyruk = topics_tr.build()
    if not kuyruk:
        return []
    kalan = [k for k in kuyruk
             if k["id"] not in s["yayinlanan"]
             and s["hatali"].get(k["id"], 0) < MAX_HATA]
    if not kalan:
        # kuyruk bitti: sıfırla, yeni tura geç (veriler her yıl güncelleniyor)
        s["yayinlanan"] = []
        s["tur"] += 1
        kalan = [k for k in kuyruk if s["hatali"].get(k["id"], 0) < MAX_HATA]
    return kalan[:DENEME]


# ---------------------------------------------------------------- müzik
def muzik_ekle(video, konu_id):
    """ses/ altındaki parçalardan birini videoya bindirir.

    Parça yoksa video sessiz kalır — pipeline durmaz.
    Aynı konu hep aynı parçayı alır (id'den türetilen seçim).
    """
    parcalar = sorted(glob.glob(os.path.join(SES_DIR, "*.mp3")) +
                      glob.glob(os.path.join(SES_DIR, "*.m4a")) +
                      glob.glob(os.path.join(SES_DIR, "*.wav")))
    if not parcalar:
        print("  ses yok, video sessiz")
        return video
    h = int(hashlib.sha1(konu_id.encode()).hexdigest()[:8], 16)
    parca = parcalar[h % len(parcalar)]
    sure = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip())
    cikti = video.replace(".mp4", "_sesli.mp4")
    # parça kısaysa döngüye al; başta 1 sn açılış, sonda 2 sn kapanış
    filtre = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{sure:.2f},"
              f"afade=t=in:st=0:d=1,afade=t=out:st={max(0, sure-2):.2f}:d=2,"
              f"volume=-14dB[a]")
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", parca,
         "-filter_complex", filtre, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", cikti],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(cikti):
        print("  [uyarı] ses eklenemedi, sessiz devam:", r.stderr[:200])
        return video
    print(f"  ses eklendi: {os.path.basename(parca)}")
    return cikti


# ---------------------------------------------------------------- metadata
ETIKET = ["türkiye kaçıncı", "istatistik", "türkiye", "sıralama", "tüik",
          "iller", "81 il", "veri", "bar chart race", "rakamlarla türkiye"]


def metadata(konu, y0, y1):
    b = f"{konu['baslik1']} {konu['baslik2']}"
    baslik = f"{b} ({y0}-{y1})"
    if len(baslik) > 95:
        baslik = b[:95]
    aciklama = (
        f"{b}, {y0}'dan {y1}'e yıl yıl.\n\n"
        f"Gösterge: {konu['gosterge']}\n"
        f"Kaynak: {konu['kaynak']}\n\n"
        "Her gün 3 yeni sıralama — abone ol, Türkiye'nin yerini kaçırma.\n\n"
        "#türkiye #istatistik #sıralama #tüik"
    )
    return {"title": baslik, "description": aciklama,
            "tags": ETIKET + [konu["gosterge"].lower()]}


# ---------------------------------------------------------------- ana akış
def bir_video(konu, kuru=False, deneme=False):
    veri_yolu = os.path.join(BURADA, konu["veri"])
    veri = json.load(open(veri_yolu, encoding="utf-8"))
    y0 = veri["y0"]
    y1 = y0 + max(len(a) for a in veri["iller"].values()) - 1

    ad = konu["id"].replace(":", "_")
    ham = os.path.join(CIKTI, f"{ad}.mp4")
    renderer_tr.render(veri_yolu, ham,
                       {"baslik1": konu["baslik1"], "baslik2": konu["baslik2"]},
                       ters=konu["ters"])
    video = muzik_ekle(ham, konu["id"])
    meta = metadata(konu, y0, y1)
    print(f"  başlık: {meta['title']}")
    if kuru:
        print("  (kuru çalışma — yükleme yapılmadı)")
        return None, video
    import upload
    gizlilik = "private" if deneme else None      # None -> EYC_PRIVACY
    if deneme:
        meta["title"] = "[DENEME] " + meta["title"]
    vid = upload.upload_video(video, meta, category="27", privacy=gizlilik)
    print(f"  yüklendi: https://youtu.be/{vid}")
    return vid, video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuru", action="store_true", help="render et ama yükleme")
    ap.add_argument("--deneme", action="store_true",
                    help="GİZLİ yükle ve konuyu yayınlanmış SAYMA (deneme videosu)")
    ap.add_argument("--konu", help="belirli bir konu id'si")
    a = ap.parse_args()

    s = state_oku()
    adaylar = sonraki_konular(s)
    if a.konu:
        adaylar = [k for k in topics_tr.build() if k["id"] == a.konu]
    if not adaylar:
        print("kuyrukta konu yok"); return 1

    for konu in adaylar:
        print(f"\n== {konu['id']}  ({konu['baslik1']} {konu['baslik2']})")
        try:
            vid, yol = bir_video(konu, kuru=a.kuru, deneme=a.deneme)
        except Exception:
            traceback.print_exc()
            s["hatali"][konu["id"]] = s["hatali"].get(konu["id"], 0) + 1
            s["log"].append({"t": str(date.today()), "id": konu["id"],
                             "durum": "hata"})
            state_yaz(s)
            continue
        if a.deneme:
            # deneme videosu kuyruğu TÜKETMEZ: konu yayınlanmış sayılmaz,
            # ileride normal akışta herkese açık olarak tekrar yayınlanır
            s["log"].append({"t": str(date.today()), "id": konu["id"],
                             "durum": "deneme", "video": vid})
            state_yaz(s)
            print("  deneme: konu kuyrukta kaldı, sonra normal yayınlanacak")
        elif not a.kuru:
            s["yayinlanan"].append(konu["id"])
            s["hatali"].pop(konu["id"], None)
            s["log"].append({"t": str(date.today()), "id": konu["id"],
                             "durum": "yayin", "video": vid})
            state_yaz(s)
        print("tamam")
        return 0

    print("hiçbir konu üretilemedi")
    return 1


if __name__ == "__main__":
    sys.exit(main())
