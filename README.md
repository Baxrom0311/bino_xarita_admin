# University Navigation System — Backend (FastAPI)

Bu servis bino ichida navigatsiya (qavat → waypoint → connection → pathfinding) uchun API beradi.

## Tezkor tushuncha: `.env` vs `.env.compose`

- `.env` — **ilova sozlamalari** (SECRET_KEY, JWT_SECRET_KEY, ADMIN_TOKEN, CORS, va h.k.). API shu faylni o‘qiydi.
- `.env.compose` / `.env.prod.compose` — **docker-compose sozlamalari** (portlar, resurs limitlar). Compose shu faylni interpolation uchun ishlatadi.

## Talablar

- Docker Desktop + Docker Compose v2
- `make` (ixtiyoriy, lekin qulay)

Agar Docker ishlatmasangiz:
- Python 3.11+
- PostgreSQL 15+

## 1) Docker (DEV) — tavsiya etiladi

1) `.env` tayyorlang (API uchun):
```bash
cd bino_xarita_admin
cp .env.example .env
```

`.env` ichida production’da albatta o‘zgartiriladiganlar:
- `SECRET_KEY` (kamida 32 belgi)
- `JWT_SECRET_KEY` (kamida 32 belgi, `SECRET_KEY` dan farqli)
- `ADMIN_TOKEN` (kamida 32 belgi) — siz aytgandek, admin uchun doimiy token
- `ALLOWED_ORIGINS` (prod’da `*` bo‘lmasin)

Eslatma (DEV): agar `FRONTEND_PORT` ni `.env.compose` da o‘zgartirsangiz, `.env` ichida `ALLOWED_ORIGINS` ga shu portni ham qo‘shing (masalan `http://localhost:8081`).

2) Compose env (port/resurs) tayyorlang:
```bash
cp .env.compose.example .env.compose
```

3) Ishga tushiring:
```bash
make dev-d
make migrate
make test
```

Kirish:
- API: `http://localhost:${API_PORT}` (default `8000`)
- Swagger: `http://localhost:${API_PORT}/docs`
- Frontend (dev): `http://localhost:${FRONTEND_PORT}` (default `8080`)

## 2) Docker (PROD)

1) `.env` (ilova) production uchun tayyor bo‘lsin:
- `ENV=production`
- `DEBUG=false`
- kuchli `SECRET_KEY`, `JWT_SECRET_KEY`, `ADMIN_TOKEN`
- `ALLOWED_ORIGINS` ni faqat ishonchli domenlarga qo‘ying

2) Compose env:
```bash
cp .env.prod.compose.example .env.prod.compose
```

3) Ishga tushirish:
```bash
COMPOSE_ENV=.env.prod.compose make prod
COMPOSE_ENV=.env.prod.compose make migrate-prod
COMPOSE_ENV=.env.prod.compose make ps-prod
```

Kirish:
- Swagger: `http://localhost:${API_PORT}/docs`
- Frontend: `http://localhost:${FRONTEND_PORT}`

## 3) Lokal (Docker’siz)

1) Virtual env:
```bash
cd bino_xarita_admin
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Postgres ishga tushiring va `.env` ni moslang:
- `DATABASE_URL=postgresql://<user>:<pass>@localhost:5432/university_nav`

3) Migration + run:
```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Admin autentifikatsiya

Admin endpointlar uchun header:
`Authorization: Bearer <ADMIN_TOKEN>`

`/api/auth/login` (JWT) ixtiyoriy — siz doimiy `ADMIN_TOKEN` ishlataman deganingiz uchun shart emas.
Login endpointda rate limit + brute-force lockout bor, bu **faqat** `/api/auth/login` ga taalluqli.

## DevOps komandalar

```bash
make stop
make logs-api
make logs-db
make backup-db
make restore-db FILE=backups/db_YYYYmmdd_HHMMSS.sql
```

## Troubleshooting

DB auth/role xatolari (Docker volume eski bo‘lsa):
```bash
make reset-db
make dev-d
make migrate
```
