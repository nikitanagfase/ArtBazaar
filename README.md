# ArtBazaar 🎨

> A full-stack handmade art marketplace connecting independent artists with collectors.

---

## 🗂 Project Structure

```
artbazaar/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # App entry point
│   ├── database.py           # SQLAlchemy engine & session
│   ├── models.py             # ORM models (User, Artwork, Order…)
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── auth.py               # JWT + password hashing
│   ├── routers/
│   │   ├── users.py          # Auth, register, profile
│   │   ├── artworks.py       # CRUD, image upload, reviews
│   │   ├── orders.py         # Order placement & status
│   │   ├── custom_orders.py  # Commission system
│   │   ├── ai.py             # Recommendations, description gen, similarity
│   │   └── analytics.py      # Artist dashboard analytics
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/                 # Pure HTML/CSS/JS frontend
    ├── index.html            # Landing page
    ├── css/
    │   ├── style.css         # Global styles
    │   └── dashboard.css     # Dashboard-specific styles
    ├── js/
    │   ├── api.js            # API client, Auth, Cart utilities
    │   ├── main.js           # Homepage controller
    │   ├── marketplace.js    # Marketplace page
    │   └── artist-dashboard.js
    └── pages/
        ├── login.html
        ├── register.html
        ├── marketplace.html
        ├── artwork-detail.html
        ├── artist-dashboard.html
        ├── buyer-dashboard.html
        ├── cart.html
        └── custom-order.html
```

---

## ⚡ Quick Start

### 1. Database Setup (MySQL)

```sql
CREATE DATABASE artbazaar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env        # Edit with your DB credentials
pip install -r requirements.txt
python main.py              # Runs on http://localhost:8000
```

API docs: http://localhost:8000/api/docs

### 3. Frontend Setup

Open `frontend/index.html` using Live Server (VS Code extension) on port 5500, or:

```bash
cd frontend
npx serve .                 # http://localhost:3000
```

---

## 🛠 Tech Stack

| Layer       | Technology                                |
|-------------|-------------------------------------------|
| Backend     | FastAPI (Python 3.11+)                    |
| Database    | MySQL 8 + SQLAlchemy ORM                  |
| Auth        | JWT (python-jose + passlib bcrypt)        |
| Frontend    | HTML5 + CSS3 + Vanilla JavaScript         |
| AI          | OpenAI GPT-4o (description) + CLIP (similarity) |
| Charts      | Chart.js                                  |
| Storage     | Local filesystem / Cloudinary             |

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in:

- `DB_*` – MySQL connection details
- `SECRET_KEY` – Random string for JWT signing
- `OPENAI_API_KEY` – For AI description generation (optional)
- `CLOUDINARY_*` – For cloud image storage (optional)

---

## 🚀 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| GET  | `/api/artworks` | List/search artworks |
| POST | `/api/artworks` | Create artwork (artist) |
| POST | `/api/orders` | Place order |
| GET  | `/api/orders/my` | Buyer's orders |
| POST | `/api/custom-orders` | Commission request |
| GET  | `/api/ai/recommendations` | AI recommendations |
| POST | `/api/ai/generate-description` | AI description from image |
| POST | `/api/ai/similar` | Image similarity search |
| GET  | `/api/analytics/artist` | Artist analytics |

Full Swagger docs at `/api/docs`

---

## 📄 License

MIT – free to use and modify.
