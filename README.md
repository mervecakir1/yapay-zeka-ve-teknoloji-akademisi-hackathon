# SMB E-Commerce AI Assistant

KOBİ'ler için yapay zeka destekli e-ticaret operasyon yönetim sistemi. Müşteri sorularını cevaplayan agent, sipariş/ürün takibi paneli, stok yönetimi ve tedarikçi maili otomasyonu.

## Çözülen Problem Alanları

Hackathon yönlendirme dokümanındaki 6 alandan **3'üne** odaklandık (1+ gereksinim):

| Alan | Karşılığı |
|------|-----------|
| **1. Müşteri İletişiminin Otomasyonu** | Tool calling tabanlı agent (AI takım üyesinin domain'i — `ai/agent.py`) |
| **2. Ürün ve Sipariş Takibi** | Dashboard + Orders sayfası + sabah özeti |
| **4. Stok ve Envanter Yönetimi** | Inventory sayfası + kritik stok uyarısı + Gemini ile tedarikçi mail taslağı |

## Mimari

```
┌────────────────────────────────────────────────────────────┐
│                  FastAPI Application                       │
│                                                            │
│  Frontend (HTML/CSS/JS)         Backend (JSON API)         │
│  ─────────────────────         ──────────────────          │
│  /index.html                    /auth (users, login, me)   │
│  /dashboard.html      ◀──CORS─▶ /products                  │
│  /products.html                 /orders                    │
│  /orders.html                   /inventory                 │
│  /inventory.html                /suppliers                 │
│  /suppliers.html                /dashboard                 │
│  /ai-assistant.html             /chat (AI domain)          │
│                                                            │
│           JWT Bearer Auth + Role-Based Access              │
└──────────────────────────┬─────────────────────────────────┘
                           │
                  ┌────────┴─────────┐
                  ▼                  ▼
           SQLAlchemy ORM     Gemini (AI stub)
              SQLite          services/ klasörü
```

### Proje yapısı

```
HackathonProject/
├── backend/                       # 👤 Onuralp domain'i
│   ├── main.py                    # FastAPI app + CORS + frontend static mount
│   ├── database.py                # SQLite engine + get_db dep
│   ├── models.py                  # SQLAlchemy ORM (7 tablo)
│   ├── schemas.py                 # Pydantic istek/yanıt modelleri
│   ├── seed.py                    # Örnek veri yükleyici
│   ├── routers/                   # JSON API endpoint'leri
│   │   ├── auth.py                # JWT + RBAC dependency
│   │   ├── products.py / orders.py / inventory.py
│   │   ├── suppliers.py / dashboard.py / chat.py
│   └── smb_app.db                 # SQLite (seed sonrası oluşur)
├── ai/                            # 🤖 AI takım üyesinin domain'i
│   ├── agent.py                   # Customer chat agent (Gemini + tool calling)
│   ├── supplier_email.py          # Mail taslağı (stub/Gemini)
│   └── dashboard_brief.py         # Sabah özeti (stub/Gemini)
├── frontend/                      # 🎨 FE takım üyesinin domain'i
│   ├── *.html (11 sayfa)
│   ├── css/style.css
│   └── js/script.js
├── .env / .env.example            # GOOGLE_API_KEY, AI_ENABLED
├── .gitignore
├── requirements.txt
└── README.md
```

Üç klasör, üç takım üyesi — net domain ayrımı.

## Auth + Role-Based Access Control

### JWT akışı

```
POST /login {email, password}
  ↓
{ access_token: "eyJ...", user: {user_id, name, email, role} }
  ↓
Frontend localStorage'a kaydeder.
Tüm sonraki isteklerde header:  Authorization: Bearer eyJ...
  ↓
Backend get_current_user decode eder, user'ı dependency olarak döner.
```

Token süresi: **60 dakika**. Expired olursa frontend 401 alır → otomatik logout.

### Rol matrisi

| Endpoint | Admin | Business Owner | Sales Manager | Inventory Staff |
|---|:-:|:-:|:-:|:-:|
| `GET` (her şey) | ✓ | ✓ | ✓ | ✓ |
| `POST/PUT/DELETE /products` | ✓ | ✓ | ✗ | ✗ |
| `POST /orders`, status, cancel | ✓ | ✓ | ✓ | ✗ |
| `PUT /inventory/{id}`, draft-email | ✓ | ✓ | ✗ | ✓ |
| `GET /users` | ✓ | ✓ | ✗ | ✗ |
| `DELETE /users` | ✓ | ✗ | ✗ | ✗ |

Frontend buna göre menüden bazı butonları (Add Product, Add Order) gizler; backend ayrıca her endpoint'te `require_roles(...)` ile doğrular.

## Hızlı Başlangıç

```powershell
# 1) Bağımlılıklar
cd C:\Users\onura\PycharmProjects\HackathonProject
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) .env oluştur (.env.example'dan kopyala)
# GOOGLE_API_KEY=...     # https://aistudio.google.com/apikey
# AI_ENABLED=false       # quota yakmamak için demo'ya kadar false

# 3) Veritabanı + örnek veri
python -m backend.seed

# 4) Çalıştır
python -m uvicorn backend.main:app --reload
```

Tarayıcıdan: **http://127.0.0.1:8000/** → Home sayfası (Login linki üst sağda)

Swagger: **http://127.0.0.1:8000/docs**

## Demo Kullanıcıları (hepsi `password123`)

| Email | Rol | Ne yapabilir |
|---|---|---|
| `owner@kobi.local` | Admin | Her şey |
| `biz@kobi.local` | Business Owner | Admin gibi (user silme hariç) |
| `sales@kobi.local` | Sales Manager | Sipariş ekle/düzenle, ürün ekleyemez |
| `inventory@kobi.local` | Inventory Staff | Stok güncelle, mail taslağı; sipariş yok |

## Demo Senaryoları

### Senaryo 1 — Yönetici sabah dashboard'ı (Alan 2)
1. Login: `owner@kobi.local`
2. Dashboard → metrikler + AI Morning Brief (kural-tabanlı; AI_ENABLED açılınca Gemini)
3. **7 ürün, 4 sipariş, 2'si pending, 2 kritik stok** görürsün

### Senaryo 2 — Stok yönetimi + tedarikçi mail (Alan 4)
1. Inventory → kritik stoktaki ürünleri (Organic Tomato + Linen Tablecloth) bul
2. **"Draft Email"** tıkla → AI servisinin ürettiği İngilizce mail taslağı modal'da
3. Yönetici onaylar (gerçek mail göndermez — demo amaçlı taslak)

### Senaryo 3 — Sipariş + kargo takibi (Alan 2 + 3)
1. Orders → "Add New Order"
2. Customer bilgileri + ürün + tarih → submit
3. Liste'de yeni sipariş + stok düşmüş + auto-computed estimated_delivery (order_date + 3 gün)
4. Satırdaki **"Update"** modal → status değiştir + tracking_no/carrier ekle
5. Müşteri sütununda hover → tooltip'te email/telefon görünür

### Senaryo 4 — Rol bazlı yetki (RBAC canlı demo)
1. Logout, `sales@kobi.local` ile gir
2. Navbar'da "Sales Rep [Sales Manager]" rozeti
3. Products'a git → liste görünür ama **"Add New Product" butonu gizli**
4. Inventory'ye git → **"Draft Email" butonu gizli** (Sales rolünün yetkisi yok)
5. Logout, `inventory@kobi.local` ile gir
6. Orders'a git → **"Update" butonu gizli** (Inventory rolünün sipariş yetkisi yok)

### Senaryo 5 — AI Assistant (gerçek Gemini, function calling)
1. AI Assistant sayfasına gir (Admin login'iyle)
2. "Which products are low in stock?" sor
3. Backend `POST /chat/` → `services/agent.py` → Gemini → `get_inventory` tool çağrılır → DB'den okur → cevap üretir
4. Cevabın altında **`[tools used: get_inventory]`** etiketi — jüriye "AI gerçekten DB'ye gitti" göstergesi

> ⚠ **Quota notu:** Gemini free tier dakikada ~5 istek, günde 20-1500 istek (modele göre). Demo öncesi `.env`'de `AI_ENABLED=false` tut, demo sırasında aç. Aksi takdirde 429 alabilirsin.

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI 0.115, Python 3.12 |
| ORM | SQLAlchemy 2.0 |
| DB | SQLite (demo); kolayca Postgres'e geçer |
| Auth | JWT (python-jose) + bcrypt (passlib) + RBAC |
| AI | Gemini 2.0 Flash (via `google-genai` SDK) + function calling — opsiyonel, `AI_ENABLED` flag'i |
| Frontend | Bootstrap 5 + vanilla JS |
| CORS | `fastapi.middleware.cors` |

## API Endpoint Listesi

### Auth
- `POST /users` — kayıt ol *(public)*
- `POST /login` — giriş *(public)*
- `GET /me` — mevcut kullanıcıyı dön *(token gerek)*
- `GET /users` — kullanıcı listesi *(Admin/Owner)*
- `DELETE /users/{id}` *(Admin)*

### Products
- `GET /products` *(her rol)*
- `POST /products` *(Admin/Owner)*
- `PUT /products/{id}` *(Admin/Owner)*
- `DELETE /products/{id}` *(Admin/Owner)*

### Orders
- `GET /orders` *(her rol)*
- `POST /orders` *(Admin/Owner/Sales)*
- `PUT /orders/{id}/status` *(Admin/Owner/Sales)*
- `PUT /orders/{id}/cancel` *(Admin/Owner/Sales)*

### Inventory
- `GET /inventory` *(her rol)*
- `PUT /inventory/{product_id}` *(Admin/Owner/Inventory)*
- `POST /inventory/products/{id}/draft-supplier-email` *(Admin/Owner/Inventory)*

### Suppliers
- `GET /suppliers` *(her rol)*
- `GET /suppliers/{id}` *(her rol)*

### Dashboard
- `GET /dashboard` *(her rol)*

### Chat (AI)
- `POST /chat/` — Gerçek Gemini agent + function calling *(public)*
  - 4 tool DB'den veri çeker: `get_orders`, `get_products`, `get_inventory`, `get_dashboard`
  - `customer_id` opsiyonel; verilirse konuşma geçmişi `chat_messages` tablosuna kaydedilir

## Takım İş Bölümü

| Alan | Sorumlu | Klasör |
|------|---------|--------|
| Backend (modeller, router, auth, RBAC, business logic) | **Onuralp** | `backend/` |
| AI / Agent | Takım üyesi 2 | `ai/` |
| Frontend | Takım üyesi 3 | `frontend/` |

### AI Servis Contract

`ai/` klasörü altında 3 AI fonksiyonu var. Hepsi `AI_ENABLED=false` iken stub/template/kural-tabanlı çalışır — backend testleri quota yakmadan yapılır.

| Dosya | Durum | İmza |
|---|---|---|
| `ai/agent.py` | ✅ **Gerçek Gemini entegre** (AI takım üyesinin kodundan uyarlandı) | `run_agent(customer_id, message) -> (reply, used_tools)` |
| `ai/supplier_email.py` | 🔲 Template (İngilizce iş maili) | `draft_supplier_email(product_id, ..., suggested_qty) -> SupplierEmailDraft` |
| `ai/dashboard_brief.py` | 🔲 Kural-tabanlı özet (şu an router bağlı değil) | `generate_brief(stats) -> str` |

İki stub servisi de Gemini'ye bağlamak isteyen takım üyesi `ai/agent.py`'deki örüntüyü taklit eder: `_ai_enabled()` kontrolü → `google.genai` client → tek `generate_content` call → text dön.

## Sınırlamalar (Demo Sürümü)

- Mail göndermez, taslak gösterir (gerçek SMTP entegrasyonu eklenebilir)
- Kargo entegrasyonu simüle: `Order.status` + `tracking_no` manuel set ediliyor (gerçek kargo API'si eklenebilir)
- Containerization yok — yerel uvicorn ile çalışır
- Production için ek olarak gerekenler: HTTPS + secret rotasyonu + rate limit + Postgres'e geçiş + Dockerfile
