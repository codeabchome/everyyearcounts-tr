#!/usr/bin/env python3
"""Türkiye Kaçıncı? — konu keşfi.

Aday göstergeleri (candidates_tr.py) World Bank ve OWID'den çeker, her
kapsam için şu iki eleği uygular:

  1. TÜRKİYE ELEĞİ   — Türkiye yılların en az %50'sinde grafikte (ilk 10)
                       olmalı. Yoksa konu yok. (Kanal kuralı.)
  2. HAREKET ELEĞİ   — İlk 10'da yıllar boyunca yeterli sıra değişimi olmalı,
                       yoksa video sıkıcı.

Geçenleri topics_tr.json'a yazar; discover_report.md'de neyin neden
elendiğini gösterir. Bağımlılık yok (stdlib). GitHub Actions'ta
discover_tr.yml ile çalışır; elle: python discover_tr.py

Ortam değişkenleri (opsiyonel):
  EYC_MIN_TUR_SHARE  Türkiye'nin grafikte olması gereken yıl oranı (0.5)
  EYC_MIN_SWAPS      İlk 10'da toplam sıra değişimi alt sınırı (12)
  EYC_MIN_YEARS      En az veri yılı (15)
  EYC_LIMIT          Test için aday sayısını sınırla (0 = hepsi)
"""
import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

from candidates_tr import OWID, WB
from names_tr import NAMES_TR, REAL_COUNTRIES
from scopes_tr import SCOPES_TR, scope_members

BARS = 10
MIN_TUR_SHARE = float(os.environ.get("EYC_MIN_TUR_SHARE", "0.5"))
MIN_SWAPS = int(os.environ.get("EYC_MIN_SWAPS", "12"))
MIN_YEARS = int(os.environ.get("EYC_MIN_YEARS", "15"))
LIMIT = int(os.environ.get("EYC_LIMIT", "0"))
CACHE = "cache_discover"
os.makedirs(CACHE, exist_ok=True)

UA = {"User-Agent": "turkiyekacinci/1.0 (topic discovery)"}


# ----------------------------------------------------------------- fetch
def _get(url, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            last = e
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(2 * (i + 1))
    raise last


def _cached(key, url):
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    data = _get(url)
    with open(path, "wb") as f:
        f.write(data)
    return data


def fetch_wb(code):
    """-> {iso3: {year: value}} sadece gerçek ülkeler."""
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
           f"?format=json&per_page=20000&date=1960:2030")
    raw = _cached(f"wb_{code}.json", url)
    payload = json.loads(raw)
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        raise ValueError("boş cevap")
    series = defaultdict(dict)
    for row in payload[1]:
        iso = row.get("countryiso3code") or ""
        val = row.get("value")
        if iso in REAL_COUNTRIES and val is not None:
            series[iso][int(row["date"])] = float(val)
    return series


def fetch_owid(slug):
    """-> {iso3: {year: value}}. OWID CSV: Entity, Code, Year, <değer>."""
    url = (f"https://ourworldindata.org/grapher/{slug}.csv"
           f"?v=1&csvType=full&useColumnShortNames=true")
    raw = _cached(f"owid_{slug}.csv", url)
    text = raw.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    try:
        i_code, i_year = header.index("Code"), header.index("Year")
    except ValueError as e:
        raise ValueError(f"beklenmeyen başlık: {header[:5]}") from e
    value_cols = [i for i in range(len(header)) if i not in (0, i_code, i_year)]
    if not value_cols:
        raise ValueError("değer sütunu yok")
    i_val = value_cols[0]
    series = defaultdict(dict)
    for row in reader:
        if len(row) <= i_val:
            continue
        iso, v = row[i_code], row[i_val]
        if iso in REAL_COUNTRIES and v not in ("", "NA"):
            try:
                series[iso][int(row[i_year])] = float(v)
            except ValueError:
                continue
    return series, header[i_val], len(value_cols)


# ----------------------------------------------------------------- analiz
def analyse(series, members, direction):
    """Bir gösterge x kapsam x yön için metrikler.

    direction: 'top' (en yüksek 10) | 'bottom' (en düşük 10)
    """
    countries = [c for c in members if c in series]
    if len(countries) < BARS + 2:
        return None, f"kapsamda verisi olan ülke az ({len(countries)})"
    years = sorted({y for c in countries for y in series[c]})
    usable = []
    for y in years:
        vals = [(series[c][y], c) for c in countries if y in series[c]]
        if len(vals) >= BARS + 2:
            usable.append((y, vals))
    if len(usable) < MIN_YEARS:
        return None, f"yeterli yıl yok ({len(usable)})"
    rev = direction == "top"
    tur_in, ranks, swaps, prev = 0, [], 0, None
    for y, vals in usable:
        vals.sort(key=lambda t: t[0], reverse=rev)
        order = [c for _, c in vals]
        top = order[:BARS]
        if "TUR" in top:
            tur_in += 1
            ranks.append(order.index("TUR") + 1)
        if prev is not None:
            swaps += sum(1 for i, c in enumerate(top) if i >= len(prev) or prev[i] != c)
        prev = top
    share = tur_in / len(usable)
    if share < MIN_TUR_SHARE:
        return None, f"Türkiye grafikte yok (yılların %{share*100:.0f}'inde)"
    if swaps < MIN_SWAPS:
        return None, f"sıralama durgun ({swaps} değişim)"
    ranks.sort()
    med = ranks[len(ranks) // 2]
    return {
        "years": [usable[0][0], usable[-1][0]],
        "n_years": len(usable),
        "n_countries": len(countries),
        "tur_share": round(share, 2),
        "tur_median_rank": med,
        "tur_best_rank": ranks[0],
        "swaps": swaps,
    }, None


def make_title(scope_key, ind, direction):
    s = SCOPES_TR[scope_key]
    if direction == "top":
        return s["title"].format(ind=ind)
    return f"{s['label']} En Düşük {ind}: Türkiye Kaçıncı?"


# ----------------------------------------------------------------- main
def main():
    topics, report = [], {"ok": [], "failed": [], "eliminated": defaultdict(list)}
    candidates = [("wb", code, ind, bottom_ok) for code, ind, bottom_ok in WB if ind] + \
                 [("owid", slug, ind, False) for slug, ind in OWID]
    if LIMIT:
        candidates = candidates[:LIMIT]

    for n, (src, key, ind, bottom_ok) in enumerate(candidates, 1):
        print(f"[{n}/{len(candidates)}] {src} {key} — {ind}", flush=True)
        try:
            if src == "wb":
                series = fetch_wb(key)
                note = ""
            else:
                series, col, ncols = fetch_owid(key)
                note = f"sütun={col}" + (f" (+{ncols-1} sütun daha)" if ncols > 1 else "")
        except urllib.error.HTTPError as e:
            report["failed"].append(f"{src} {key}: HTTP {e.code} (slug/kod yanlış olabilir)")
            continue
        except Exception as e:  # noqa: BLE001
            report["failed"].append(f"{src} {key}: {e}")
            continue
        if "TUR" not in series:
            report["failed"].append(f"{src} {key}: Türkiye verisi yok")
            continue
        report["ok"].append(f"{src} {key} ({len(series)} ülke) {note}")

        for scope_key in SCOPES_TR:
            members = scope_members(scope_key, REAL_COUNTRIES)
            for direction in (["top", "bottom"] if bottom_ok else ["top"]):
                m, why = analyse(series, members, direction)
                if m is None:
                    report["eliminated"][why.split(" (")[0]].append(f"{key}/{scope_key}/{direction}")
                    continue
                topics.append({
                    "id": f"{src}:{key}:{scope_key}:{direction}",
                    "source": src, "code": key, "indicator_tr": ind,
                    "scope": scope_key, "direction": direction,
                    "title": make_title(scope_key, ind, direction),
                    "source_label": "World Bank" if src == "wb" else "Our World in Data",
                    **m,
                })

    # Merak skoru: Türkiye yüksek sırada + çok hareket = iyi.
    for t in topics:
        t["score"] = round(t["swaps"] * (1 + 3 / t["tur_median_rank"]) * t["tur_share"], 1)
    topics.sort(key=lambda t: -t["score"])

    with open("topics_tr.json", "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=1)

    per_scope = defaultdict(int)
    for t in topics:
        per_scope[t["scope"]] += 1
    lines = [
        "# discover_tr raporu", "",
        f"**Toplam konu: {len(topics)}**  (aday gösterge: {len(candidates)}, "
        f"çekilen: {len(report['ok'])}, başarısız: {len(report['failed'])})", "",
        "## Kapsam başına konu", "",
        *[f"- {k}: {per_scope.get(k, 0)}" for k in SCOPES_TR], "",
        "## Eleme sebepleri", "",
        *[f"- {why}: {len(v)}" for why, v in sorted(report["eliminated"].items(), key=lambda kv: -len(kv[1]))], "",
        "## Başarısız kaynaklar (düzelt veya sil)", "",
        *([f"- {x}" for x in report["failed"]] or ["- yok"]), "",
        "## İlk 40 konu (skor)", "",
        *[f"- {t['score']:>6} | {t['title']} | TR medyan sıra {t['tur_median_rank']}, "
          f"{t['years'][0]}-{t['years'][1]}" for t in topics[:40]], "",
        "## Çekilen kaynaklar", "",
        *[f"- {x}" for x in report["ok"]],
    ]
    with open("discover_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nKONU: {len(topics)}  |  rapor: discover_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
