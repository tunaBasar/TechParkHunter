"""Domain relevance filtering for scraped companies.

TechPark Hunter'ın kullanıcısı bir bilgisayar mühendisi olduğu için, scraping
sırasında yalnızca yazılım/teknoloji/bilişim ve finans/bankacılık alanlarıyla
ilgili olduğu düşünülen şirketler tutulur. İsim, sektör ve açıklama alanlarının
hiçbirinde bu alanlara dair bir anahtar kelime geçmeyen şirketler tamamen
elenir (detay sayfası dahi çekilmez).
"""

# Yazılım / Teknoloji / Bilişim ile ilgili anahtar kelimeler (TR + EN)
TECH_KEYWORDS = [
    "yazılım", "yazilim", "software",
    "teknoloji", "technology", "tech",
    "bilişim", "bilisim", "bilgi teknolojileri", "information technology", " it ",
    "bilgisayar", "computer",
    "yapay zeka", "yapay zekâ", "artificial intelligence", " ai ",
    "makine öğrenmesi", "machine learning", "derin öğrenme", "deep learning",
    "veri bilimi", "data science", "büyük veri", "big data", "veri analitiği",
    "bulut", "cloud",
    "siber güvenlik", "siber", "cyber security", "cybersecurity",
    "blockchain", "kripto para", "crypto",
    "oyun teknolojileri", "oyun geliştirme", "game development", "game studio",
    "mobil uygulama", "mobile app", "web uygulama", "web geliştirme",
    "elektronik", "electronics",
    "gömülü sistem", "embedded system",
    "nesnelerin interneti", "iot",
    "robotik", "robotics", "robot teknolojileri",
    "otomasyon", "automation",
    "mekatronik", "mechatronics",
    "ar-ge", "arge", "r&d", "araştırma geliştirme",
    "sistem entegrasyon", "network teknolojileri", "ağ teknolojileri",
    "sunucu teknolojileri", "server",
    "veritabanı", "database",
    "dijital dönüşüm", "digital transformation", "dijital",
    "sensör teknolojileri", "sensor technology",
    "savunma sanayi", "defense industry", "defence industry",
    "havacılık", "aerospace", "uzay teknolojileri", "space technology",
    "drone", "İha", "insansız hava aracı",
    "telekomünikasyon", "telecom", "telco",
    "e-ticaret", "e-commerce",
    "lojistik", "logistics", "tedarik zinciri", "supply chain",
    "mühendislik yazılımı", "engineering software",
    "simülasyon", "simulation",
    "medikal teknoloji", "medical technology", "sağlık teknolojisi", "health tech",
    "biyoteknoloji", "biotechnology",
    "nanoteknoloji", "nanotechnology",
    "olay tabanlı mimari", "event-driven", "event driven",
    "dağıtık sistemler", "distributed systems",
    "mikroservis", "microservice", "microservices",
]

# Finans / Bankacılık ile ilgili anahtar kelimeler
FINANCE_KEYWORDS = [
    "finans", "finance", "fintech",
    "bankacılık", "banking", "banka",
    "ödeme sistemleri", "ödeme", "payment",
    "sigorta", "insurance",
    "yatırım", "investment",
    "borsa", "stock exchange",
    "sermaye", "capital",
]

RELEVANCE_KEYWORDS = [kw.lower() for kw in (*TECH_KEYWORDS, *FINANCE_KEYWORDS)]

# Python'ın varsayılan str.lower() metodu Türkçe büyük "İ" harfini "i" + birleşik
# nokta işaretine (U+0307) çeviriyor, bu da "BİLİŞİM" gibi kelimelerin "bilişim"
# ile eşleşmemesine yol açıyor. Türkçe kurallara uygun küçük harfe çevirme için
# önce büyük İ/I harflerini doğru karşılıklarına eşleyip sonra lower() çağırıyoruz.
_TURKISH_UPPER_MAP = str.maketrans({"İ": "i", "I": "ı"})


def _turkish_lower(text: str) -> str:
    return text.translate(_TURKISH_UPPER_MAP).lower()


def is_relevant_company(
    name: str | None,
    sector: str | None = None,
    description: str | None = None,
    full_description: str | None = None,
) -> bool:
    """Şirket isim/sektör/açıklama alanlarından herhangi birinde yazılım,
    teknoloji, bilişim veya finans/bankacılık ile ilgili bir anahtar kelime
    geçiyor mu kontrol eder."""

    haystack = " ".join(
        f" {_turkish_lower(part)} " for part in (name, sector, description, full_description) if part
    )
    if not haystack.strip():
        # Yeterli veri yoksa güvenli tarafta kal: eleme yapma.
        return True

    return any(keyword in haystack for keyword in RELEVANCE_KEYWORDS)
