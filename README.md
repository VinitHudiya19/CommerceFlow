# CommerceFlow - Asynchronous FastAPI Modular Monolith E-Commerce System

CommerceFlow is a full-featured e-commerce web application built using Python 3.12+, FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL, Redis, Celery, and a Vanilla JavaScript single-page application (SPA) frontend.

The project is structured as a **modular monolith**, organizing business logic into clean feature modules (`auth`, `products`, `cart`, `orders`, `inventory`, `payments`, `reviews`, `wishlist`, `admin`, `users`, `security`) within a single repository and deployment unit.

For an in-depth breakdown of system design, relationship loading, security, and sequence flows, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Technical Stack Overview

| Layer / Role | Technology | Description |
|---|---|---|
| **Language** | Python 3.12 / 3.13 | Core backend programming runtime |
| **Web Framework** | FastAPI 0.115 | High-performance async ASGI web framework |
| **ASGI Server** | Uvicorn | High-concurrency async web server |
| **Database ORM** | SQLAlchemy 2.0 (Async) | Type-safe asynchronous database access layer |
| **DB Driver** | asyncpg | Fast async PostgreSQL database driver |
| **Database** | PostgreSQL 16 | Relational database for ACID transactional safety |
| **Caching & Broker** | Redis 7 | In-memory cache and Celery message broker |
| **Background Tasks** | Celery 5.4 | Asynchronous background worker queue |
| **Authentication** | PyJWT + Bcrypt | Passlib password hashing & JWT token rotation |
| **Frontend** | HTML5, CSS3, Vanilla JS | SPA with client-side hash router hosted by FastAPI |

---

## Key Features

1. **Fully Asynchronous Database Pipeline**:
   Built using SQLAlchemy 2.0 Async Engine and `asyncpg`. All queries, updates, and relationship loads execute asynchronously without blocking main thread event loops.

2. **Background Order Processing (Celery + Redis)**:
   Order checkouts offload stock deduction, payment initialization, and notification logs to Celery background workers via Redis message queues, keeping API response times fast under heavy traffic.

3. **Refresh Token Rotation (RTR) & Security**:
   - Access tokens expire in 15 minutes.
   - Refresh tokens are rotated atomically upon use to prevent replay attacks.
   - Account locking temporarily locks user accounts after 5 failed login attempts.
   - Client IP rate limiting protects endpoints against brute-force attacks.

4. **Product Catalog & Redis Caching**:
   Product queries and categories are cached in Redis to speed up catalog browsing and search response times.

5. **AI Recommendation Engine & Review Summarizer**:
   - Recommendation engine suggests items based on purchase history co-occurrence and category preferences.
   - Review summarizer provides parsed rating highlights and key takeaway summaries.

6. **Admin Dashboard**:
   Aggregates system-wide metrics including total revenue, user count, order counts, pending status breakdowns, and low-stock inventory alerts.

---

## Project Structure

```
E-COMMERCE/
├── app/
│   ├── admin/          # Dashboard aggregate statistics
│   ├── auth/           # Login, registration, token rotation
│   ├── cart/           # Cart item operations & price snapshots
│   ├── common/         # Redis connection, database init, seed data
│   ├── config.py       # Application settings via Pydantic
│   ├── database.py     # Database engine and async session creation
│   ├── inventory/      # Stock control and refill management
│   ├── main.py         # App factory, middleware, static route serving
│   ├── orders/         # Order creation & Celery background tasks
│   ├── payments/       # Mock payment verification & transactions
│   ├── products/       # Product catalog, categories, search, caching
│   ├── reviews/        # Ratings, comments, AI review summarizer
│   ├── security/       # JWT helpers, rate limiting middleware
│   ├── users/          # Profiles and delivery address management
│   └── wishlist/       # Saved bookmarks
├── static/             # Frontend SPA assets (app.js, app.css, index.html)
├── tests/              # Automated unit and integration tests (pytest)
├── ARCHITECTURE.md     # In-depth system architecture documentation
├── docker-compose.yml  # Production multi-container orchestration file
├── Dockerfile          # Container build steps
└── requirements.txt    # Python package dependencies
```

---

## How to Run the Project

### Option 1: Quick Local Run (Development Mode)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start FastAPI application server**:
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

3. **Access the application**:
   - **Frontend App**: Open [http://localhost:8080/](http://localhost:8080/)
   - **Interactive API Documentation (Swagger)**: Open [http://localhost:8080/docs](http://localhost:8080/docs)

---

### Option 2: Full Docker Run (Production Containerization)

Spin up PostgreSQL database, Redis broker, Celery worker, and FastAPI application:

```bash
docker-compose up --build
```

Services started by Docker Compose:
- **FastAPI Application**: `http://localhost:8080`
- **PostgreSQL Database**: Port `5432`
- **Redis Cache & Broker**: Port `6379`
- **Celery Worker**: Background queue worker process

---

## Default Demo Credentials

On startup, the system automatically seeds initial product categories, products, inventory records, and demo accounts:

- **Admin Account**:
  - Email: `admin@commerceflow.com`
  - Password: `admin123`

- **Customer Account**:
  - Email: `customer@commerceflow.com`
  - Password: `customer123`

---

## Automated Test Suite

Run unit and service integration tests using `pytest`:

```bash
python -m pytest -v
```

Tests cover:
- User registration, duplicate email handling, and account locking rules (`tests/test_auth.py`).
- Empty cart validation, unverified email checks, and order checkout flows (`tests/test_orders.py`).

---

## System Architecture Reference

For detailed explanations of the modular monolith design pattern, async database greenlet handling, relationship loading choices (`selectinload` vs `noload`), and background processing sequence diagrams, read [ARCHITECTURE.md](ARCHITECTURE.md).
