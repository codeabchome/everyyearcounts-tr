#!/usr/bin/env python3
"""Türkiye Kaçıncı? — bar chart race renderer (stil C).

Kilitli görsel kararlar (kullanıcı onayladı, dokunma):
  - Koyu lacivert zemin + yumuşak ışıma
  - Barlar: sol kenar düz (ortak eksen), sağ uç yuvarlak
  - Öne çıkan bar KIRMIZI #E30A17
  - İl/ülke adları solda sabit sütunda, barın içinde DEĞİL
  - Üstte logo + "TÜRKİYE KAÇINCI?", altta kaynak satırı + @turkiyekacinci
  - Dev yıl rakamı YOK; sağ üstte küçük yıl + ince kırmızı zaman çizgisi

Kullanım:
    python renderer_tr.py veri_il/nufus.json cikti.mp4 \
        --baslik1 "EN KALABALIK" --baslik2 "10 İL" --altbaslik NÜFUS
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.environ.get("EYC_FONTS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
W, H = 1080, 1920
FPS = 30
BARS = 10

RED = (227, 10, 23)
INK = (255, 255, 255)
MUT = (142, 154, 178)
DIM = (92, 104, 128)
BAR = (38, 47, 68)
LINE = (32, 40, 58)

_fc = {}
def fnt(w, s):
    k = (w, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(FONT_DIR, f"Inter-{w}.ttf"), s)
    return _fc[k]


def tr_buyuk(s):
    """Türkçe büyük harf: i -> İ, ı -> I (Python'un upper()'ı bunu bilmiyor)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_sayi(v, birim):
    if birim in ("%", "‰"):
        return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(v) >= 1_000_000_000:
        return f"{v/1_000_000_000:,.1f}".replace(".", ",") + " milyar"
    if abs(v) >= 1_000_000 and birim == "TL":
        return f"{v/1_000_000:,.1f}".replace(".", ",") + " milyon"
    return f"{int(round(v)):,}".replace(",", ".")


# ---------------------------------------------------------------- interpolasyon
def pchip_tangents(xs, ys):
    """Fritsch–Carlson: monoton kübik türevler (aşma yok, sahte tepe yok)."""
    n = len(xs)
    if n == 1:
        return [0.0]
    d = [(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(n-1)]
    m = [0.0]*n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n-1):
        if d[i-1]*d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2*(xs[i+1]-xs[i]) + (xs[i]-xs[i-1])
            w2 = (xs[i+1]-xs[i]) + 2*(xs[i]-xs[i-1])
            m[i] = (w1+w2)/(w1/d[i-1] + w2/d[i])
    return m


class Seri:
    def __init__(self, xs, ys):
        self.xs, self.ys = xs, ys
        self.m = pchip_tangents(xs, ys)

    def __call__(self, x):
        xs = self.xs
        if x <= xs[0]:
            return self.ys[0]
        if x >= xs[-1]:
            return self.ys[-1]
        lo, hi = 0, len(xs)-1
        while hi - lo > 1:
            mid = (lo+hi)//2
            if xs[mid] <= x: lo = mid
            else: hi = mid
        h = xs[hi]-xs[lo]
        t = (x-xs[lo])/h
        y0, y1, m0, m1 = self.ys[lo], self.ys[hi], self.m[lo], self.m[hi]
        t2, t3 = t*t, t*t*t
        return ((2*t3-3*t2+1)*y0 + (t3-2*t2+t)*h*m0 +
                (-2*t3+3*t2)*y1 + (t3-t2)*h*m1)


# ---------------------------------------------------------------- çizim
def zemin():
    img = Image.new("RGB", (W, H), (12, 16, 26))
    g = Image.new("RGB", (W, H), (12, 16, 26))
    gd = ImageDraw.Draw(g)
    gd.ellipse([-260, -340, 820, 420], fill=(42, 20, 32))
    gd.ellipse([420, 1560, 1480, 2260], fill=(24, 22, 42))
    return Image.blend(img, g.filter(ImageFilter.GaussianBlur(200)), 0.92)


def bar(d, x, y, w, h, fill, r=12):
    w = max(2, int(w))
    r = min(r, max(1, w//2))
    d.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill)
    d.rectangle([x, y, x+r, y+h], fill=fill)


def logo(d, x, y, s=1.25):
    h = int(10*s); g = int(6*s)
    d.rounded_rectangle([x, y, x+int(46*s), y+h], radius=h//2, fill=INK)
    d.rounded_rectangle([x, y+h+g, x+int(32*s), y+2*h+g], radius=h//2, fill=RED)
    d.rounded_rectangle([x, y+2*(h+g), x+int(20*s), y+3*h+2*g], radius=h//2, fill=(118,128,150))
    return x+int(64*s)


TOP, BH, GAP = 648, 92, 15
LX, LW = 70, 236
BX = LX + LW + 26
MAXW = W - BX - 70


def sabitler(cfg):
    """Her karede aynı kalan katman — bir kez çizilir."""
    img = zemin()
    d = ImageDraw.Draw(img)
    x = logo(d, 70, 92)
    d.text((x, 92), "TÜRKİYE", font=fnt("ExtraBold", 34), fill=INK)
    d.text((x, 130), "KAÇINCI?", font=fnt("ExtraBold", 34), fill=RED)
    d.text((70, 262), cfg["baslik1"], font=fnt("ExtraBold", 88), fill=INK)
    d.text((70, 358), cfg["baslik2"], font=fnt("ExtraBold", 88), fill=RED)
    d.line([70, 500, W-70, 500], fill=LINE, width=2)
    d.text((70, 526), cfg["altbaslik"], font=fnt("Bold", 32), fill=MUT)
    d.line([70, H-152, W-70, H-152], fill=LINE, width=2)
    d.text((70, H-116), "KAYNAK: " + cfg["kaynak"], font=fnt("SemiBold", 27), fill=DIM)
    d.text((W-70, H-116), "@turkiyekacinci", font=fnt("Bold", 27), fill=MUT, anchor="rt")
    return img


def kare(base, cfg, yil, degerler, poz, maxv):
    """degerler: {ad: deger}, poz: {ad: yumuşatılmış sıra}"""
    img = base.copy()
    d = ImageDraw.Draw(img)

    d.text((W-70, 520), str(int(yil)), font=fnt("ExtraBold", 44), fill=INK, anchor="rt")
    ty = 606
    d.line([70, ty, W-70, ty], fill=LINE, width=3)
    prog = (yil - cfg["y0"]) / max(1e-9, cfg["y1"] - cfg["y0"])
    px = 70 + int((W-140) * min(1.0, max(0.0, prog)))
    d.line([70, ty, px, ty], fill=RED, width=3)
    d.ellipse([px-8, ty-8, px+8, ty+8], fill=RED)

    f_ad = fnt("Bold", 40)
    f_dg = fnt("Bold", 36)
    for ad, p in sorted(poz.items(), key=lambda kv: kv[1]):
        if p > BARS - 0.4:
            continue
        v = degerler.get(ad)
        if v is None:
            continue
        y = TOP + p * (BH + GAP)
        w = max(4, MAXW * (v / maxv if maxv else 0))
        hot = p < 0.5
        renk = RED if hot else BAR
        d.text((LX+LW, y+BH/2-2), ad, font=f_ad,
               fill=INK if hot else (206, 214, 228), anchor="rm")
        bar(d, BX, y, w, BH, renk)
        etiket = tr_sayi(v, cfg["birim"])
        tw = d.textlength(etiket, font=f_dg)
        if w > tw + 56:
            d.text((BX+w-26, y+BH/2-2), etiket, font=f_dg, fill=INK, anchor="rm")
        else:
            d.text((BX+w+22, y+BH/2-2), etiket, font=f_dg, fill=MUT, anchor="lm")
    return img


# ---------------------------------------------------------------- ana
def render(veri_yolu, cikti, cfg_ek, yil_sn=None, tut_sn=2.5, ters=False,
           hedef_sure=38.0):
    veri = json.load(open(veri_yolu, encoding="utf-8"))
    baz = veri["y0"]

    seriler, y0, y1 = {}, None, None
    for ad, dizi in veri["iller"].items():
        xs = [baz + i for i, v in enumerate(dizi) if v is not None]
        ys = [float(v) for v in dizi if v is not None]
        if len(xs) < 3:
            continue
        seriler[ad] = Seri(xs, ys)
        y0 = xs[0] if y0 is None else min(y0, xs[0])
        y1 = xs[-1] if y1 is None else max(y1, xs[-1])

    cfg = {"baslik1": "EN YÜKSEK", "baslik2": "10 İL",
           "altbaslik": tr_buyuk(veri["ad"]), "kaynak": veri["kaynak"],
           "birim": veri["birim"], "y0": y0, "y1": y1}
    cfg.update(cfg_ek)

    # seri kisaysa yil basina sure uzar; her video ~hedef_sure saniye olsun
    if yil_sn is None:
        yil_sn = max(0.9, min(3.0, hedef_sure / max(1, y1 - y0)))
    base = sabitler(cfg)
    toplam_kare = int((y1 - y0) * yil_sn * FPS)
    tut_kare = int(tut_sn * FPS)

    poz = {}
    ffmpeg = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-preset", "medium", "-crf", "20", cikti],
        stdin=subprocess.PIPE)

    def bir_kare(yil, ilk=False):
        deg = {}
        for ad, s in seriler.items():
            if s.xs[0] <= yil <= s.xs[-1]:
                deg[ad] = s(yil)
        if not deg:
            return None
        sirali = sorted(deg.items(), key=lambda kv: kv[1], reverse=not ters)
        hedef = {ad: i for i, (ad, _) in enumerate(sirali)}
        k = 0.19
        for ad, h in hedef.items():
            if ad not in poz or ilk:
                poz[ad] = float(h)
            else:
                poz[ad] += (h - poz[ad]) * k
        for ad in list(poz):
            if ad not in hedef:
                poz[ad] += (BARS + 2 - poz[ad]) * k
        gor = [ad for ad, p in poz.items() if p < BARS + 0.6]
        maxv = max((deg[a] for a in gor if a in deg), default=1) or 1
        return kare(base, cfg, yil, deg, {a: poz[a] for a in gor}, maxv)

    for i in range(toplam_kare):
        yil = y0 + (y1 - y0) * i / max(1, toplam_kare - 1)
        im = bir_kare(yil, ilk=(i == 0))
        if im is None:
            continue
        ffmpeg.stdin.write(im.tobytes())
        if i % 150 == 0:
            print(f"  kare {i}/{toplam_kare}", flush=True)

    son = bir_kare(y1)
    for _ in range(tut_kare):
        ffmpeg.stdin.write(son.tobytes())

    ffmpeg.stdin.close()
    ffmpeg.wait()
    sure = (toplam_kare + tut_kare) / FPS
    print(f"bitti: {cikti}  ({sure:.1f} sn)")
    return cikti


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("veri"); ap.add_argument("cikti")
    ap.add_argument("--baslik1", default="EN YÜKSEK")
    ap.add_argument("--baslik2", default="10 İL")
    ap.add_argument("--altbaslik", default=None)
    ap.add_argument("--yil-sn", type=float, default=None)
    ap.add_argument("--ters", action="store_true")
    a = ap.parse_args()
    ek = {"baslik1": a.baslik1, "baslik2": a.baslik2}
    if a.altbaslik:
        ek["altbaslik"] = a.altbaslik
    render(a.veri, a.cikti, ek, yil_sn=a.yil_sn, ters=a.ters)
