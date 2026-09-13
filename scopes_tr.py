"""Türkçe kanal kapsamları. KURAL: her kapsamda Türkiye (TUR) vardır ve
kapsam en az 12 ülke içerir (10 bar dolsun diye).

'world' da var ama discover_tr.py Türkiye'nin ilk 10'a girmediği konuları
zaten eler; dünya kapsamı sadece Türkiye'nin gerçekten ilk 10'da olduğu
göstergelerde kalır.
"""

SCOPES_TR = {
    "world": {
        "label": "Dünyada",
        "title": "Dünyada {ind}: Türkiye Kaçıncı Sırada?",
        "iso": None,  # None = tüm gerçek ülkeler
    },
    "europe": {
        "label": "Avrupa'da",
        "title": "Avrupa'da {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "DEU", "FRA", "GBR", "ITA", "ESP", "POL", "NLD", "BEL", "SWE",
                "AUT", "CHE", "NOR", "DNK", "FIN", "IRL", "PRT", "GRC", "CZE", "ROU",
                "HUN", "UKR", "RUS", "BLR", "BGR", "SRB", "HRV", "SVK", "SVN", "LTU",
                "LVA", "EST", "BIH", "ALB", "MKD", "MNE", "MDA", "LUX", "ISL", "MLT",
                "CYP", "XKX"],
    },
    "eu_plus_tr": {
        "label": "AB ve Türkiye'de",
        "title": "AB Ülkeleri ile Türkiye'de {ind}",
        "iso": ["TUR", "DEU", "FRA", "ITA", "ESP", "POL", "NLD", "BEL", "SWE", "AUT",
                "DNK", "FIN", "IRL", "PRT", "GRC", "CZE", "ROU", "HUN", "BGR", "HRV",
                "SVK", "SVN", "LTU", "LVA", "EST", "LUX", "MLT", "CYP"],
    },
    "middle_east": {
        "label": "Ortadoğu'da",
        "title": "Ortadoğu'da {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "SAU", "IRN", "IRQ", "ISR", "ARE", "EGY", "QAT", "KWT", "OMN",
                "BHR", "JOR", "LBN", "SYR", "YEM", "PSE"],
    },
    "neighbors": {
        "label": "Türkiye ve Komşularında",
        "title": "Türkiye ve Komşularında {ind}",
        # kara + deniz komşuları + yakın çevre
        "iso": ["TUR", "GRC", "BGR", "GEO", "ARM", "AZE", "IRN", "IRQ", "SYR", "CYP",
                "RUS", "UKR", "ROU", "EGY", "ISR", "LBN"],
    },
    "balkans": {
        "label": "Balkanlar'da",
        "title": "Balkanlar'da {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "GRC", "BGR", "ROU", "SRB", "HRV", "BIH", "ALB", "MKD", "MNE",
                "SVN", "XKX", "MDA"],
    },
    "black_sea": {
        "label": "Karadeniz Havzasında",
        "title": "Karadeniz Ülkelerinde {ind}",
        "iso": ["TUR", "RUS", "UKR", "ROU", "BGR", "GEO", "MDA", "ARM", "AZE", "GRC",
                "SRB", "MKD", "ALB"],
    },
    "mediterranean": {
        "label": "Akdeniz'de",
        "title": "Akdeniz Ülkelerinde {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "ESP", "FRA", "ITA", "GRC", "EGY", "ISR", "LBN", "SYR", "CYP",
                "MLT", "HRV", "SVN", "BIH", "MNE", "ALB", "LBY", "TUN", "DZA", "MAR"],
    },
    "islamic": {
        "label": "İslam Ülkelerinde",
        "title": "İslam Ülkeleri Arasında {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "IDN", "PAK", "BGD", "EGY", "IRN", "SAU", "ARE", "QAT", "KWT",
                "MYS", "NGA", "DZA", "MAR", "TUN", "IRQ", "JOR", "LBN", "OMN", "BHR",
                "KAZ", "UZB", "AZE", "TKM", "KGZ", "TJK", "AFG", "SDN", "SEN", "MLI",
                "NER", "SOM", "LBY", "ALB", "BIH", "BRN", "MDV", "YEM", "SYR", "PSE"],
    },
    "turkic_caucasus_ca": {
        "label": "Türk Dünyası, Kafkasya ve Orta Asya'da",
        "title": "Türk Dünyası ve Orta Asya'da {ind}",
        "iso": ["TUR", "AZE", "KAZ", "UZB", "KGZ", "TKM", "TJK", "GEO", "ARM", "MNG",
                "AFG", "IRN", "RUS"],
    },
    "g20": {
        "label": "G20'de",
        "title": "G20 Ülkeleri Arasında {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "USA", "CHN", "JPN", "DEU", "GBR", "FRA", "ITA", "CAN", "BRA",
                "RUS", "IND", "AUS", "KOR", "MEX", "IDN", "SAU", "ZAF", "ARG"],
    },
    "emerging": {
        "label": "Gelişen Ekonomilerde",
        "title": "Gelişen Ekonomiler Arasında {ind}: Türkiye Kaçıncı?",
        "iso": ["TUR", "CHN", "IND", "BRA", "RUS", "MEX", "IDN", "SAU", "ZAF", "ARG",
                "POL", "THA", "MYS", "PHL", "VNM", "EGY", "NGA", "PAK", "BGD", "COL",
                "CHL", "PER", "KAZ", "ARE", "IRN"],
    },
}


def scope_members(scope_key, real_countries):
    iso = SCOPES_TR[scope_key]["iso"]
    return set(real_countries) if iso is None else set(iso) & set(real_countries)


def _check():
    for k, s in SCOPES_TR.items():
        if s["iso"] is None:
            continue
        assert "TUR" in s["iso"], k
        assert len(s["iso"]) >= 12, (k, len(s["iso"]))
        assert len(set(s["iso"])) == len(s["iso"]), ("duplicate in", k)


_check()
