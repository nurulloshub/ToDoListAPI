# Todo List API

A RESTful Todo List API built with **FastAPI**, **PostgreSQL**, and **async SQLAlchemy**. Includes JWT authentication, per-user authorization, pagination, filtering, sorting, rate limiting, and a zero-build-step frontend served by the same process.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- 🔐 **JWT authentication** — access + refresh tokens, bcrypt password hashing
- 👤 **Per-user authorization** — users can only see/modify their own todos
- 📄 **Pagination, filtering, sorting** — `page`, `limit`, `completed`, `search`, `sort_by`, `order`
- 🚦 **Rate limiting** — 10 req/min on `/register` and `/login` via `slowapi`
- 🧪 **Unit tests** — pytest + httpx async client (8 tests, in-memory SQLite)
- 🖥️ **Built-in frontend** — vanilla HTML/CSS/JS SPA, no build step
- 🐘 **Async SQLAlchemy 2.0** — non-blocking DB access via `asyncpg`
- ✅ **Pydantic v2 validation** — strict request/response schemas
- 📚 **Auto-generated docs** — Swagger UI at `/docs`, ReDoc at `/redoc`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL 15+ (async via `asyncpg`) |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | PyJWT (HS256) + bcrypt |
| Validation | Pydantic v2 + `email-validator` |
| Rate limiting | slowapi |
| Testing | pytest + pytest-asyncio + httpx |
| Frontend | Vanilla HTML / CSS / JavaScript |

---

## Project Structure

```
TodoListAPI/
├── app/
│   ├── main.py              # FastAPI app, lifespan, rate-limit middleware
│   ├── config.py            # Pydantic settings loaded from .env
│   ├── database.py          # Async engine + session factory
│   ├── models.py            # SQLAlchemy ORM models (User, Todo)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── security.py          # Password hashing + JWT helpers
│   ├── dependencies.py      # get_current_user dependency
│   ├── rate_limit.py        # Shared slowapi limiter
│   ├── routers/
│   │   ├── auth.py          # /register, /login, /refresh
│   │   └── todos.py         # CRUD + pagination/filter/sort
│   └── static/              # Frontend (HTML/CSS/JS)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_todos.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python **3.11+**
- PostgreSQL **15+**
- `git`

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/todo-list-api.git
cd todo-list-api
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

```bash
# Switch to the postgres OS user (Linux)
sudo -u postgres psql
```

Inside `psql`:

```sql
CREATE DATABASE tododb;
CREATE USER todo_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE tododb TO todo_user;
\c tododb
GRANT ALL ON SCHEMA public TO todo_user;
ALTER DATABASE tododb OWNER TO todo_user;
\q
```

### 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://todo_user:your_strong_password@localhost:5432/tododb
SECRET_KEY=replace-with-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Generate a strong secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 6. Run the app

```bash
uvicorn app.main:app --reload
```

Open:

- **Frontend:** <http://127.0.0.1:8000>
- **Swagger UI:** <http://127.0.0.1:8000/docs>
- **ReDoc:** <http://127.0.0.1:8000/redoc>

Tables are created automatically on first startup.

---

## Running Tests

```bash
pytest -q
```

Expected:

```
........                                    [100%]
8 passed in ~4s
```

Tests use an **in-memory SQLite** database — they don't touch your PostgreSQL instance.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Create a new user, returns tokens |
| `POST` | `/login` | Authenticate, returns tokens |
| `POST` | `/refresh` | Exchange refresh token for new pair |

**Register body:**

```json
{ "name": "John Doe", "email": "john@doe.com", "password": "password1" }
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Todos

All endpoints require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/todos` | Create a todo |
| `GET` | `/todos` | List (paginated, filterable, sortable) |
| `PUT` | `/todos/{id}` | Update (owner only) |
| `DELETE` | `/todos/{id}` | Delete (owner only) |

**GET `/todos` query parameters:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | int ≥ 1 | `1` | |
| `limit` | int 1–100 | `10` | |
| `completed` | bool | – | Filter by status |
| `search` | string | – | Case-insensitive match on title/description |
| `sort_by` | `created_at` \| `title` \| `completed` | `created_at` | |
| `order` | `asc` \| `desc` | `desc` | |

**Example response:**

```json
{
  "data": [
    { "id": 1, "title": "Buy groceries", "description": "Milk, eggs, bread", "completed": false, "created_at": "2024-11-24T10:15:00Z" }
  ],
  "page": 1,
  "limit": 10,
  "total": 1
}
```

### Error responses

| Code | Meaning |
|---|---|
| `400` | Email already registered |
| `401` | Missing/invalid token, or bad credentials |
| `403` | Not the owner of this todo |
| `404` | Todo not found |
| `422` | Validation error (Pydantic) |
| `429` | Rate limit exceeded |

---

## Quick cURL walkthrough

```bash
# Register
curl -s -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@doe.com","password":"password1"}' > /tmp/reg.json

TOKEN=$(python -c "import json;print(json.load(open('/tmp/reg.json'))['access_token'])")

# Create
curl -s -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Buy groceries","description":"Milk, eggs, bread"}'

# List, filtered & sorted
curl -s "http://127.0.0.1:8000/todos?page=1&limit=10&completed=false&sort_by=title&order=asc" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Security Notes

- Passwords are hashed with **bcrypt**; never stored or returned in plaintext.
- Access tokens are short-lived (30 min by default); refresh tokens last 7 days.
- Rate limiting protects `/register` and `/login` from brute-force attempts.
- All todo queries are scoped to the authenticated user — no cross-user data leakage.
- **Production TODO:** use `httpOnly` cookies for refresh tokens, add HTTPS, migrate via Alembic, rotate the JWT secret periodically, and add request logging.

---

## Roadmap

- [ ] Alembic migrations
- [ ] Refresh-token revocation table (logout everywhere)
- [ ] Optimistic locking (`updated_at` version)
- [ ] Dockerfile + docker-compose
- [ ] GitHub Actions CI (lint + test)
- [ ] Due dates & reminders
- [ ] Drag-to-reorder todos

---

## License

MIT — see [LICENSE](LICENSE).

---

## Acknowledgements

Built as part of the [roadmap.sh Todo List API](https://roadmap.sh/projects/todo-list-api) project.