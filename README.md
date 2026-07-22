# 🏗️ TechPark Hunter

Türkiye'deki teknoparklardaki şirketleri otomatik tarayan, filtreleyen ve iş başvurusu için düzenli bir "brief" hazırlayan yerel web uygulaması.

## ✨ Özellikler

- **Config-driven scraping** — Playwright tabanlı, YAML config ile sıfır kod değişikliğiyle yeni teknopark sitesi eklenebilir
- **Hata toleranslı tarama** — otomatik retry (exponential backoff), rate limiting, partial success desteği
- **Şirket listesi & filtreleme** — sektör, kaynak, başvuru durumu ve serbest metin aramasıyla filtreleme
- **Başvuru takibi** — her şirket için durum (başvurulmadı / başvuruldu / mülakat / reddedildi / kabul edildi) ve notlar
- **Başvuru Brief'i** — şirket verisi + aday profilini birleştiren markdown belge üretir (bkz. aşağıdaki not — **LLM kullanmaz**)
- **CSV / JSON export** — mevcut filtrelerle, UTF-8 destekli dışa aktarma
- **Toast bildirimleri, loading skeleton'ları, boş durum yönlendirmeleri** — cilalı, karanlık temalı arayüz

<!-- Ekran görüntüsü eklenecek -->

## 🤖 Başvuru Brief Sistemi Hakkında Önemli Not

TechPark Hunter'ın "AI" paneli **hiçbir LLM'e bağlanmaz** ve **hiçbir metin üretmez**. Bunun yerine:

1. Seçtiğiniz şirketin verisini (sektör, açıklama, iletişim bilgisi vb.) ve `backend/app/ai/profile.yaml` içindeki aday profilinizi birleştirip
2. Cowork'e (veya tercih ettiğiniz herhangi bir LLM aracına) verilecek eksiksiz bir **markdown brief** hazırlar.

Bu tasarım bilinçli bir tercihtir: yerel LLM (Ollama) her makinede çalıştırılamıyor, cloud LLM API'leri (OpenAI/Anthropic) ise gereksiz maliyet ve bağımlılık getiriyor. Bunun yerine hazırlanan brief'i kopyalayıp **Claude Cowork** (veya başka bir LLM sohbeti) içine yapıştırarak e-posta taslağını ve CV önerilerini orada, siz kontrol ederek ürettirmeniz önerilir.

> 🤝 Cowork ile bu projeyi nasıl kullanacağınız (API referansı, iletişim e-postası bulma stratejisi, örnek prompt) için **[COWORK_GUIDE.md](./COWORK_GUIDE.md)** dosyasına bakın.

## 🚀 Kurulum

```bash
make install
```

Bu komut:
- Backend bağımlılıklarını kurar (`uv sync`)
- Playwright'ın Chromium tarayıcısını indirir
- Frontend bağımlılıklarını kurar (`npm install`)

> Ollama veya başka bir LLM kurulumuna **gerek yoktur** — proje LLM çağrısı yapmaz.

## ▶️ Kullanım

```bash
make dev
```

Bu, backend'i (`localhost:8000`) ve frontend'i (`localhost:5173`) aynı anda başlatır. Tarayıcıda **http://localhost:5173** adresini açın.

Sadece backend veya frontend'i ayrı ayrı çalıştırmak için:

```bash
make backend   # sadece FastAPI (localhost:8000)
make frontend  # sadece Vite dev server (localhost:5173)
```

## 🛠️ CLI Komutları

| Komut | Açıklama |
|-------|----------|
| `make install` | Tüm bağımlılıkları kurar (backend + frontend + Playwright) |
| `make dev` | Backend + frontend'i birlikte başlatır |
| `make backend` | Sadece FastAPI backend'i başlatır |
| `make frontend` | Sadece Vite frontend'i başlatır |
| `make scrape SITE=<slug>` | Belirtilen tek bir siteyi scrape eder (örn. `make scrape SITE=itu_ari`) |
| `make scrape-all` | Tanımlı tüm siteleri sırayla scrape eder |
| `make clean` | `__pycache__`, SQLite DB ve scraped JSON dosyalarını temizler |

## 🧩 Yeni Site Ekleme

Yeni bir teknopark sitesi eklemek için **kod yazmanıza gerek yok** — sadece bir YAML dosyası:

1. `backend/app/scraping/sites/` altına `{slug}.yaml` dosyası oluşturun
2. Mevcut config'lerden birini (örn. `itu_ari.yaml`) şablon olarak kullanın:
   - `site`: isim, slug, base_url, company_list_url
   - `navigation`: `pagination` | `infinite_scroll` | `load_more` tipini ve ilgili selector'ları tanımlayın
   - `selectors`: şirket kartı ve alan selector'larını (`name`, `sector`, `description`, `website`, `logo`) tanımlayın; opsiyonel `detail_page` ile detay sayfası alanlarını ekleyin
   - `filters.sector_keywords`: sektör etiketleme için anahtar kelimeler
3. `GET /api/scrape/sites` endpoint'i otomatik olarak yeni siteyi listeler, `POST /api/scrape/{slug}` ile tarama başlatılabilir

Detaylı format için `architecture_plan.md` Bölüm 4'e bakın.

## 🧱 Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3.12+, FastAPI, Pydantic |
| Scraping | Playwright (async), YAML config |
| Veri Depolama | JSON (kaynak veri) + SQLite (arama indeksi) |
| Frontend | Vite 6, React 19, React Router |
| UI | Vanilla CSS (tasarım sistemi), Lucide Icons |
| Başvuru İçeriği | Brief Template (LLM yok) + Claude Cowork (manuel, backend dışı) |
| Paket Yönetimi | uv (backend), npm (frontend) |

## 📁 Proje Yapısı

```
techparkhunter/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI giriş noktası
│   │   ├── config.py                # Ayarlar
│   │   ├── api/routes/              # companies, scrape, ai endpoint'leri
│   │   ├── scraping/                # engine, parser, config_loader, sites/*.yaml
│   │   ├── ai/                      # profile.yaml, brief_template.py, service.py
│   │   ├── storage/                 # json_store, db, models
│   │   └── utils/
│   └── data/
│       ├── companies/               # Scrape edilmiş JSON dosyaları
│       └── applications/            # Üretilen brief'ler ({company_id}/brief.md)
├── frontend/
│   └── src/
│       ├── pages/                   # Dashboard, Companies, CompanyDetail, ScrapingPanel
│       ├── components/              # CompanyCard, FilterBar, AIGeneratorPanel, Toast, ...
│       └── services/api.js
├── architecture_plan.md
└── Makefile
```

## 📄 Lisans

MIT
