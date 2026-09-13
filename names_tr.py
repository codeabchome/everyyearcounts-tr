"""ISO3 -> Türkçe ülke adı. Sadece gerçek ülkeler (toplam/grup satırları YOK).

Bu sözlük aynı zamanda 'gerçek ülke' filtresidir: burada olmayan ISO3 kodu
(WLD, OED, EUU, IBT, TEC, ARB, ...) grafiğe hiç girmez. Silme.
"""

NAMES_TR = {
    "AFG": "Afganistan", "ALB": "Arnavutluk", "DZA": "Cezayir", "AGO": "Angola",
    "ARG": "Arjantin", "ARM": "Ermenistan", "AUS": "Avustralya", "AUT": "Avusturya",
    "AZE": "Azerbaycan", "BHS": "Bahamalar", "BHR": "Bahreyn", "BGD": "Bangladeş",
    "BRB": "Barbados", "BLR": "Belarus", "BEL": "Belçika", "BLZ": "Belize",
    "BEN": "Benin", "BTN": "Butan", "BOL": "Bolivya", "BIH": "Bosna-Hersek",
    "BWA": "Botsvana", "BRA": "Brezilya", "BRN": "Brunei", "BGR": "Bulgaristan",
    "BFA": "Burkina Faso", "BDI": "Burundi", "CPV": "Yeşil Burun", "KHM": "Kamboçya",
    "CMR": "Kamerun", "CAN": "Kanada", "CAF": "Orta Afrika Cum.", "TCD": "Çad",
    "CHL": "Şili", "CHN": "Çin", "COL": "Kolombiya", "COM": "Komorlar",
    "COD": "Kongo DC", "COG": "Kongo", "CRI": "Kosta Rika", "CIV": "Fildişi Sahili",
    "HRV": "Hırvatistan", "CUB": "Küba", "CYP": "Kıbrıs", "CZE": "Çekya",
    "DNK": "Danimarka", "DJI": "Cibuti", "DOM": "Dominik Cum.", "ECU": "Ekvador",
    "EGY": "Mısır", "SLV": "El Salvador", "GNQ": "Ekvator Ginesi", "ERI": "Eritre",
    "EST": "Estonya", "SWZ": "Esvatini", "ETH": "Etiyopya", "FJI": "Fiji",
    "FIN": "Finlandiya", "FRA": "Fransa", "GAB": "Gabon", "GMB": "Gambiya",
    "GEO": "Gürcistan", "DEU": "Almanya", "GHA": "Gana", "GRC": "Yunanistan",
    "GTM": "Guatemala", "GIN": "Gine", "GNB": "Gine-Bissau", "GUY": "Guyana",
    "HTI": "Haiti", "HND": "Honduras", "HKG": "Hong Kong", "HUN": "Macaristan",
    "ISL": "İzlanda", "IND": "Hindistan", "IDN": "Endonezya", "IRN": "İran",
    "IRQ": "Irak", "IRL": "İrlanda", "ISR": "İsrail", "ITA": "İtalya",
    "JAM": "Jamaika", "JPN": "Japonya", "JOR": "Ürdün", "KAZ": "Kazakistan",
    "KEN": "Kenya", "KOR": "Güney Kore", "PRK": "Kuzey Kore", "KWT": "Kuveyt",
    "KGZ": "Kırgızistan", "LAO": "Laos", "LVA": "Letonya", "LBN": "Lübnan",
    "LSO": "Lesotho", "LBR": "Liberya", "LBY": "Libya", "LTU": "Litvanya",
    "LUX": "Lüksemburg", "MAC": "Makao", "MDG": "Madagaskar", "MWI": "Malavi",
    "MYS": "Malezya", "MDV": "Maldivler", "MLI": "Mali", "MLT": "Malta",
    "MRT": "Moritanya", "MUS": "Mauritius", "MEX": "Meksika", "MDA": "Moldova",
    "MNG": "Moğolistan", "MNE": "Karadağ", "MAR": "Fas", "MOZ": "Mozambik",
    "MMR": "Myanmar", "NAM": "Namibya", "NPL": "Nepal", "NLD": "Hollanda",
    "NZL": "Yeni Zelanda", "NIC": "Nikaragua", "NER": "Nijer", "NGA": "Nijerya",
    "MKD": "Kuzey Makedonya", "NOR": "Norveç", "OMN": "Umman", "PAK": "Pakistan",
    "PAN": "Panama", "PNG": "Papua Yeni Gine", "PRY": "Paraguay", "PER": "Peru",
    "PHL": "Filipinler", "POL": "Polonya", "PRT": "Portekiz", "PRI": "Porto Riko",
    "QAT": "Katar", "ROU": "Romanya", "RUS": "Rusya", "RWA": "Ruanda",
    "SAU": "Suudi Arabistan", "SEN": "Senegal", "SRB": "Sırbistan", "SLE": "Sierra Leone",
    "SGP": "Singapur", "SVK": "Slovakya", "SVN": "Slovenya", "SOM": "Somali",
    "ZAF": "Güney Afrika", "SSD": "Güney Sudan", "ESP": "İspanya", "LKA": "Sri Lanka",
    "SDN": "Sudan", "SUR": "Surinam", "SWE": "İsveç", "CHE": "İsviçre",
    "SYR": "Suriye", "TJK": "Tacikistan", "TZA": "Tanzanya", "THA": "Tayland",
    "TLS": "Doğu Timor", "TGO": "Togo", "TTO": "Trinidad ve Tobago", "TUN": "Tunus",
    "TUR": "Türkiye", "TKM": "Türkmenistan", "UGA": "Uganda", "UKR": "Ukrayna",
    "ARE": "BAE", "GBR": "Birleşik Krallık", "USA": "ABD", "URY": "Uruguay",
    "UZB": "Özbekistan", "VEN": "Venezuela", "VNM": "Vietnam", "PSE": "Filistin",
    "YEM": "Yemen", "ZMB": "Zambiya", "ZWE": "Zimbabve", "XKX": "Kosova",
    "TWN": "Tayvan",
}

# Haritada gösterilecek ülke kümesi = sözlüğün anahtarları
REAL_COUNTRIES = frozenset(NAMES_TR)
