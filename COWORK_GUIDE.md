# 🤝 Cowork için Kullanım Kılavuzu

Bu doküman, **Claude Cowork** (veya benzer bir LLM/agent aracı) TechPark Hunter'ı kullanarak senin adına iş başvurusu araştırması ve iletişim yapması için gereken tüm bilgiyi içerir.

> ⚠️ **Önkoşul:** Backend'in çalışıyor olması gerekir:
> ```bash
> cd ~/Desktop/projects/techparkhunter
> make backend
> ```
> API `http://localhost:8000` üzerinde ayakta olmalı. `curl http://localhost:8000/health` ile kontrol edebilirsin.

---

## 1. Neden bu kılavuz var?

TechPark Hunter'ın backend'i **hiçbir LLM çağrısı yapmaz**. Şirket verisini toplar (scraping), filtreler, saklar ve "brief" (özet bağlam) hazırlar — ama e-posta içeriğini **üretmez**, "en doğru şirket hangisi" kararını **vermez**. Bu kararları, senin CV'ini okuyup değerlendirebilen Cowork gibi bir LLM aracı vermeli. Backend sadece veri ve altyapı sağlar.

---

## 2. API Referansı

### Şirket Arama & Listeleme

**`GET /api/companies/?search=<kelime>&sector=<sektör>&source=<kaynak>&status=<durum>&page=1&per_page=20`**
- Serbest metin araması `name` ve `description` alanlarında yapılır (`search`)
- `source`: `bilkent_cyberpark`, `depark`, `itu_ari`, `teknopark_ankara`, `antalya_teknokent`, `gosb_teknopark`
- `status`: `not_applied`, `applied`, `interview`, `rejected`, `accepted`
- Dönen her şirket objesi: `id`, `name`, `sector`, `sector_tags`, `description`, `website`, `contact_email`, `detail_url`, `application_status`, `notes`, `source`, `source_name`

**`GET /api/companies/{id}`** — Tek bir şirketin tüm detayını döner (404 if not found)

**`GET /api/companies/stats`** — Kaynak ve durum bazlı toplam sayılar

**`GET /api/companies/export?format=csv|json&...filtreler`** — Filtrelenmiş listeyi dosya olarak indirir

### Şirket Güncelleme

**`PATCH /api/companies/{id}`** — Body: `{"application_status": "applied", "notes": "..."}`
Başvuru durumunu ve notları günceller. **Her başvuru sonrası bu endpoint'i çağır** ki `not_applied` durumunda kalan şirketlere tekrar mail gitmesin.

**`DELETE /api/companies/{id}`** — Şirketi kalıcı olarak siler. Dikkatli kullan.

### İletişim E-postası Bulma

**`POST /api/companies/{id}/find-contact-email`**
- Şirketin DB kaydında `contact_email` zaten varsa → onu döner (`"source": "existing"`)
- Yoksa ve `website` alanı doluysa → siteyi ziyaret edip ana sayfa + yaygın iletişim sayfalarında (`/iletisim`, `/contact` vb.) `mailto:` linki arar (`"source": "website"`)
- Hiçbiri yoksa/bulunamazsa → `{"found": false, "reason": "..."}` döner. **Asla tahmini bir e-posta üretmez.**

Bu endpoint'in bulamadığı durumlarda (adım 4'e bak) **senin** (Cowork'ün) web araması yapman gerekiyor.

### Başvuru Brief'i (Bağlam Hazırlama)

**`POST /api/ai/generate-brief`** — Body: `{"company_id": "..."}`
Şirket verisini + `backend/app/ai/profile.yaml`'daki aday profilini birleştirip markdown bir "brief" üretir. **LLM çağrısı yapmaz** — sen bu brief'i okuyup e-posta/CV içeriğini kendin üreteceksin.

**`GET /api/ai/profile`** — Aday profilini (isim, unvan, yetenekler, öne çıkanlar, eğitim, diller) döner.

**`GET /api/ai/brief/{company_id}`** — Daha önce oluşturulmuş bir brief'i tekrar okur.

### E-posta Gönderme

**`POST /api/ai/send-email`** — Body: `{"company_id": "..."}`
Gmail SMTP (App Password ile) üzerinden `company.contact_email`'e mail gönderir.

> ⚠️ **Önemli kısıt:** Bu endpoint şu an **sabit bir şablon** kullanıyor (`ai/brief_template.py:build_email_subject_and_body`), senin/Cowork'ün yazdığı özel metni **göndermiyor**. Kişiye özel, senin onayladığın bir e-posta metni göndermek istiyorsan:
> - Ya bu endpoint'i özel konu/gövde kabul edecek şekilde genişletmemi iste (bana söyle, hemen yaparım),
> - Ya da Cowork sana e-posta taslağını göstersin, sen onayla, Cowork kendi Gmail/mail aracıyla göndersin.

### Scraping (yeni site taraması gerekirse)

**`GET /api/scrape/sites`** — Tanımlı teknopark config'lerini listeler
**`POST /api/scrape/{slug}`** — Taramayı başlatır, `job_id` döner
**`GET /api/scrape/status/{job_id}`** — Tarama durumunu takip eder

---

## 3. İletişim E-postası Bulma Stratejisi (öncelik sırası)

Cowork bir şirkete başvuru hazırlarken **şu sırayı** izlemeli:

1. **DB'de zaten var mı?** → `GET /api/companies/{id}` çağrısındaki `contact_email` alanına bak. Doluysa direkt kullan.
2. **Website üzerinden bul** → `POST /api/companies/{id}/find-contact-email` çağır. `found: true` dönerse kullan.
3. **Web'de ara** → 2. adım `found: false` dönerse, şirketin ismiyle web araması yap. En makul eşleşen resmi web sitesini bul, oraya git, `/iletisim`, `/contact`, `/hakkimizda` gibi sayfalarda veya footer'da bir e-posta adresi ara.
4. **Hiçbiri bulunamazsa** → o şirketi atla, kullanıcıya bildir. **Asla tahmini/uydurma bir adres kullanma.**

Her adımda bulunan e-posta adresi ve kaynağı (DB / website / web araması) kullanıcıya gösterilmeli ve **gönderim öncesi onay alınmalı**.

---

## 4. Örnek Cowork Promptu

Aşağıdaki promptu kendi CV'ine ve tercihlerine göre uyarlayarak Cowork'e verebilirsin:

```
Elimde TechPark Hunter adında yerel bir proje var (~/Desktop/projects/techparkhunter).
Backend http://localhost:8000 adresinde çalışıyor. API kılavuzu için
~/Desktop/projects/techparkhunter/COWORK_GUIDE.md dosyasını oku.

CV'im: ~/Desktop/projects/my-portfolio/cv.txt

Yapmanı istediğim:

1. GET /api/companies/?search=<kelime>&per_page=50 ile CV'imdeki teknolojilere
   uygun şirketleri ara (birden fazla arama terimiyle dene: "yazılım", "backend",
   "java", "spring", ".net" vb.). Bulduğun en alakalı 10-15 şirketi bana
   listele (isim, sektör, kaynak) ve hangilerine başvurmamı önerdiğini söyle.

2. Onayladığım her şirket için COWORK_GUIDE.md'deki "İletişim E-postası Bulma
   Stratejisi"ni takip ederek bir e-posta adresi bul. Bulduğun adresi ve
   kaynağını (DB / website / web araması) bana göster, ONAY ALMADAN DEVAM ETME.

3. Onaylarsam POST /api/ai/generate-brief ile o şirkete özel brief'i oluştur,
   bu brief'i ve CV'imi kullanarak kısa, samimi bir Türkçe iş başvuru e-postası
   taslağı yaz (konu + gövde, max 250 kelime). Taslağı bana göster, ONAY ALMADAN
   GÖNDERME.

4. Onaylarsam mail'i gönder ve PATCH /api/companies/{id} ile
   application_status: "applied" olarak işaretle.

5. Sonunda hangi şirkete, hangi e-postaya, ne zaman başvuru yaptığını
   özetleyen bir liste ver.

Kurallar:
- Aynı şirkete asla iki kez mail atma (application_status'a bak).
- Emin olmadığın e-posta adreslerine gönderme, önce bana sor.
- Her gönderimden önce onay al, toplu/otomatik gönderim yapma.
- Şüpheli bir eşleşme varsa (yanlış şirket, isim benzerliği vb.) atla ve bildir.
```

---

## 5. Aday Profili

`backend/app/ai/profile.yaml` dosyası brief'lerde kullanılan profildir. Kendi bilgilerinle güncel tutman, brief'lerin doğru kişiselleştirilmesini sağlar.
