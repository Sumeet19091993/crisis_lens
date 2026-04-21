# CrisisLens API

A FastAPI-based crisis-reporting backend with geospatial support (PostGIS), real-time pub/sub (Redis), JWT authentication, and Prometheus metrics.

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 + PostGIS |
| Cache / Streams | Redis 7 |
| Auth | JWT (HS256), bcrypt |
| Migrations | Alembic |
| Monitoring | Prometheus (`/metrics`) |

---

## Project Structure

```
crisislens/
├── .gitignore
├── README.md
└── packages/
    └── api/
        ├── Dockerfile
        ├── requirements.txt
        ├── alembic.ini
        ├── .env.example
        ├── alembic/
        │   ├── env.py
        │   ├── script.py.mako
        │   └── versions/
        │       ├── 0001_init_postgis.py
        │       └── 0002_users_audit.py
        └── app/
            ├── main.py
            ├── config.py
            ├── db.py
            ├── models.py
            ├── schemas.py
            ├── crud.py
            ├── security.py
            ├── anti_spam.py
            ├── rate_limit.py
            ├── middleware.py
            ├── logging_setup.py
            └── routers/
                ├── health.py
                ├── auth.py
                ├── reports.py
                ├── live.py
                └── analytics.py
```

---

## Local Development

### 1. Clone & setup env

```bash
git clone <your-repo-url>
cd crisislens/packages/api
cp .env.example .env
# Edit .env with your local credentials
```

### 2. Start dependencies (Docker)

```bash
# PostgreSQL with PostGIS
docker run -d --name crisislens-pg \
  -e POSTGRES_DB=crisislens \
  -e POSTGRES_USER=crisislens \
  -e POSTGRES_PASSWORD=crisislens \
  -p 5432:5432 postgis/postgis:15-3.4

# Redis
docker run -d --name crisislens-redis -p 6379:6379 redis:7
```

### 3. Install & migrate

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### 4. Run

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/health` | No | Liveness check |
| GET | `/api/v1/ready` | No | Readiness (DB + Redis) |
| POST | `/api/v1/auth/register` | No | Register user |
| POST | `/api/v1/auth/token` | No | Login → JWT pair |
| POST | `/api/v1/auth/refresh` | No | Refresh access token |
| POST | `/api/v1/auth/logout` | No | Revoke token |
| POST | `/api/v1/reports` | No | Submit a report |
| GET | `/api/v1/reports` | No | List reports |
| GET | `/api/v1/reports/{id}` | No | Get single report |
| PATCH | `/api/v1/reports/{id}/status` | verifier/admin | Update report status |
| GET | `/api/v1/map/clusters` | No | Geohash clusters |
| GET | `/api/v1/analytics/timeline` | No | Hourly timeline |
| GET | `/api/v1/analytics/severity` | No | Severity distribution |
| WS | `/ws/live` | No | Real-time report stream |
| GET | `/metrics` | No | Prometheus metrics |

---

## Deploy on Render

See the **Render Deployment Guide** section below or follow the README in `packages/api/`.

### Required Environment Variables on Render

```
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
REDIS_HOST
REDIS_PORT
JWT_SECRET           ← generate with: openssl rand -hex 32
APP_ENV=production
```

The `Dockerfile` automatically runs `alembic upgrade head` before starting Uvicorn.
