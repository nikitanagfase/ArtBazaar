
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

# 🎨 ArtBazaar: Handmade Art Selling Platform

## Author

  Nikita Nagfase 

## Affiliation

Department of MCA
Suryodaya College Of Engineering And Technology, Nagpur 

---

##  Abstract

ArtBazaar is a full-stack web-based marketplace designed to establish a direct and efficient connection between independent artists and potential buyers. The platform enables artists to digitally showcase and sell their handmade artworks, while providing buyers with a seamless interface to explore, purchase, and request customized artistic products.

The system leverages FastAPI for backend development, MySQL for structured data management, and SQLAlchemy as the Object Relational Mapping (ORM) tool. Secure authentication is implemented using JSON Web Tokens (JWT). Additionally, the platform incorporates advanced functionalities such as a custom artwork request mechanism, review and rating system, and analytics dashboard for performance tracking.

The proposed solution aims to support independent artists, enhance user engagement, and create a scalable digital ecosystem for handmade art commerce.

---

##  1. Introduction

The rapid growth of digital marketplaces has transformed the way goods and services are exchanged; however, independent artists often face challenges in accessing dedicated platforms tailored to their specific needs. General-purpose e-commerce platforms do not adequately support the uniqueness and customization aspects of handmade artwork.

ArtBazaar addresses this limitation by providing a specialized online marketplace focused exclusively on handmade art. The platform facilitates direct interaction between artists and buyers, eliminating intermediaries and ensuring better transparency and profitability for creators.

A distinctive aspect of the system is its support for **custom artwork requests**, allowing buyers to commission personalized creations, thereby enhancing user satisfaction and platform engagement.

---

##  2. Literature Review

Existing systems in the domain of online commerce and art marketplaces exhibit partial solutions to the identified problem:

* **General E-commerce Platforms:**
  Platforms such as Amazon and Flipkart provide large-scale product distribution but lack specialization in handmade or artistic goods and do not support personalized artwork workflows.

* **Art-Specific Marketplaces:**
  Platforms like Etsy and Saatchi Art cater to artists but often involve complex onboarding processes and limited support for structured custom order management.

* **Social Media Platforms:**
  Platforms such as Instagram enable artists to showcase their work; however, they lack integrated transaction systems, order management, and secure payment mechanisms.

### Research Gap

* Lack of structured custom artwork request systems
* Absence of integrated analytics for artists
* No unified platform combining sales, personalization, and trust mechanisms

ArtBazaar addresses these gaps through a modular and scalable system design.

---

##  3. Methodology

### System Architecture

The system follows a **client-server architecture**, where the frontend interacts with backend services through RESTful APIs. The backend processes business logic and communicates with the database using an ORM layer.

### Development Approach

An **incremental development model** is adopted to ensure smooth implementation and continuous testing.

### Functional Modules

* Authentication Module
* Product Management Module
* Order Management Module
* Review and Rating Module
* Custom Order Management Module
* Analytics Module
* File Upload and Storage Module

---

##  4. Implementation

### Backend

* FastAPI (Python) for API development

### Database

* MySQL for relational data storage

### ORM

* SQLAlchemy for database interaction

### Authentication

* JWT (JSON Web Token) for secure login

### Frontend

* HTML, CSS, JavaScript for user interface

### Media Storage

* Cloudinary / Local storage for images

---

##  5. System Workflow

1. Users register as Artist or Buyer
2. Artists upload and manage artworks
3. Products are stored and displayed
4. Buyers browse using filters and search
5. Buyers place orders or request custom artwork
6. Artists respond to custom requests
7. Orders are processed and tracked
8. Buyers provide ratings and reviews
9. Artists analyze performance via dashboard

---

##  6. Results and Discussion

The system demonstrates effective implementation of a role-based marketplace supporting both artists and buyers. Core functionalities such as product management, order processing, and secure authentication ensure reliability.

The custom order feature enhances personalization and interaction, while the review system builds trust among users. Overall, the platform successfully meets its intended objectives.

---

##  7. Limitations

* No real-time chat functionality
* Payment gateway not integrated
* Limited scalability in local deployment
* Basic frontend design

---

##  8. Future Scope

* Integration of payment gateways (Razorpay/Stripe)
* Real-time chat system
* AI-based artwork recommendations
* Mobile application development
* Advanced analytics and visualization
* Multi-language support

---

##  9. Conclusion

ArtBazaar provides a scalable and efficient solution for the online sale of handmade artwork. It enables direct interaction between artists and buyers while supporting personalized services through custom orders.

The integration of modern technologies and user-centric features makes it a strong foundation for future expansion into a fully commercial platform.

---
