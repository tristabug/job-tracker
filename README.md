# Job Application Tracker API

A production-quality REST API for tracking job applications, contacts, statuses, and follow-up dates.

![Coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen)
![CI](https://github.com/YOUR_USERNAME/job-tracker/actions/workflows/ci.yml/badge.svg)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Python 3.11 + FastAPI |
| Database | PostgreSQL (production), SQLite (local test runs) |
| ORM | SQLAlchemy 2.x async |
| Auth | JWT via python-jose + bcrypt |
| Testing | pytest + httpx + pytest-cov |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Project Structure

```
job-tracker/
├── app/
│   ├── config.py            # Pydantic settings (env var loading)
│   ├── database.py          # Async SQLAlchemy engine + session factory
│   ├── dependencies.py      # FastAPI deps: get_db, get_current_user
│   ├── main.py              # App factory, router registration
│   ├── models/
│   │   ├── user.py          # User ORM model
│   │   ├── application.py   # Application ORM model + status enum
│   │   └── contact.py       # Contact ORM model
│   ├── schemas/
│   │   ├── user.py          # User Pydantic request/response schemas
│   │   ├── application.py   # Application schemas + pagination response
│   │   ├── contact.py       # Contact schemas
│   │   └── token.py         # JWT token schema
│   ├── services/
│   │   ├── auth.py          # Password hashing, JWT creation, user CRUD
│   │   ├── applications.py  # Application CRUD + filtering
│   │   └── contacts.py      # Contact CRUD
│   └── routers/
│       ├── auth.py          # POST /auth/register, POST /auth/login
│       ├── applications.py  # Full CRUD + /upcoming endpoint
│       └── contacts.py      # Nested CRUD under /applications/{id}/contacts
├── tests/
│   ├── conftest.py          # Engine, session, client, auth fixtures
│   ├── test_auth.py         # Register, login, token validation tests
│   ├── test_applications.py # Application CRUD + edge case tests
│   └── test_contacts.py     # Contact CRUD + ownership tests
├── .github/
│   └── workflows/
│       └── ci.yml           # Run tests + enforce 90% coverage on every push
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── pyproject.toml
├── Dockerfile               # Multi-stage build: deps → slim runtime image
└── docker-compose.yml       # Local dev stack: api + postgres
```

---

## Getting Started (Do This First)

Set up GitHub and Docker before writing any application code. This gives you version history from commit one and a consistent environment to build and test in from day one.

### 1 — GitHub Repository Setup

```bash
# Rename the default branch to main (GitHub's expected default)
git branch -m master main

# On GitHub: create a new empty repo named "job-tracker" (no README, no .gitignore)
# Then link it and push:
git remote add origin https://github.com/YOUR_USERNAME/job-tracker.git
git add README.md
git commit -m "chore: initial commit with project plan"
git push -u origin main

# Create the staging and dev branches from main
git checkout -b staging && git push -u origin staging
git checkout -b dev && git push -u origin dev
git checkout main
```

Replace `YOUR_USERNAME` in the README badges (lines 6–7) and the clone URLs with your actual GitHub username before pushing.

After pushing all three branches, configure branch protection rules on GitHub — see the [Branch & Environment Strategy](#branch--environment-strategy) section below.

### 2 — Add .gitignore

Create `.gitignore` in the project root before adding any more files:

```
__pycache__/
*.pyc
*.pyo
.env
*.db
.venv/
.coverage
coverage.xml
htmlcov/
.pytest_cache/
```

This ensures `.env` (secrets), SQLite test databases, and cache files are never committed.

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
git push
```

### 3 — Get Docker Running First

Create `Dockerfile` and `docker-compose.yml` (full content in the [Docker Setup](#docker-setup) section below) before writing any app code. Then verify the stack starts cleanly:

```bash
# Create a minimal placeholder so the api container has something to import
mkdir -p app && touch app/__init__.py app/main.py

# Start the stack — postgres should come up healthy, api will fail gracefully
docker compose up --build
```

Once `app/main.py` has a real FastAPI app, the api container will serve requests at `http://localhost:8000`. From this point forward, develop inside Docker:

```bash
docker compose up            # start the stack (hot reload is on)
docker compose exec api bash # open a shell inside the running container
docker compose run --rm api pytest  # run tests
```

Commit the Docker files right away:

```bash
git add Dockerfile docker-compose.yml
git commit -m "chore: add Dockerfile and docker-compose for local dev"
git push
```

---

## Branch & Environment Strategy

### Environments and Databases

| Environment | Branch | Database | Where it runs |
|---|---|---|---|
| Development | `dev` | `jobtracker_dev` | Local Docker |
| Staging | `staging` | `jobtracker_staging` | Local Docker |
| Production | `main` | `jobtracker` | Local Docker for now — deployed server when hosting is added |
| Test | (any) | `jobtracker_test` | Local Docker / CI — wiped after every test run, never shared |

All three environments run locally in Docker for now. Dev and staging are separate databases inside the same postgres container, switched via the `DATABASE_URL` in your `.env` file. A deployed staging server can be added later without changing the branching strategy.

The test database is separate from all three environments. Staging is for manual QA verification; it cannot be the pytest database because tests destroy all data between runs.

### Promotion Flow

```
feature-branch → dev → staging → main
```

- All work starts on a short-lived feature branch cut from `dev`
- Merge feature branches into `dev` via PR
- When `dev` is stable, open a PR from `dev` → `staging` for QA
- After staging sign-off, open a PR from `staging` → `main` for production release
- **Never** merge directly to `main` or `staging` — always go through the chain

### Branch Protection Rules

Configure these in **GitHub → Settings → Branches → Add branch ruleset** for each of `main`, `staging`, and `dev`:

| Rule | `main` | `staging` | `dev` |
|---|---|---|---|
| Require PR before merging (no direct push) | ✅ | ✅ | ✅ |
| Require the `test` CI job to pass | ✅ | ✅ | ✅ |
| Require branch to be up to date before merge | ✅ | ✅ | ✅ |
| Block force pushes | ✅ | ✅ | ✅ |

To set this up:
1. Go to `https://github.com/YOUR_USERNAME/job-tracker/settings/rules`
2. Click **New ruleset**
3. Set **Enforcement status** to **Active**
4. Under **Target branches**, add each branch by name
5. Enable the rules from the table above — for **status checks**, add the `test` job name after your first CI run creates it

---

## Data Models

### User
| Field | Type | Notes |
|---|---|---|
| id | UUID (str) | Primary key |
| email | str | Unique |
| hashed_password | str | bcrypt |
| full_name | str | Optional |
| created_at | datetime | Auto |

### Application
| Field | Type | Notes |
|---|---|---|
| id | UUID (str) | Primary key |
| user_id | UUID (str) | FK → users |
| company_name | str | Required |
| job_title | str | Required |
| job_url | str | Optional |
| status | enum | applied / phone_screen / interview / offer / rejected / withdrawn |
| applied_date | date | Defaults to today |
| follow_up_date | date | Optional, drives /upcoming endpoint |
| notes | text | Optional |
| created_at / updated_at | datetime | Auto |

### Contact
| Field | Type | Notes |
|---|---|---|
| id | UUID (str) | Primary key |
| application_id | UUID (str) | FK → applications |
| user_id | UUID (str) | FK → users (for ownership checks) |
| name | str | Required |
| title | str | Optional |
| email | str | Optional |
| phone | str | Optional |
| linkedin_url | str | Optional |
| notes | text | Optional |
| created_at / updated_at | datetime | Auto |

---

## API Endpoints

### Auth
```
POST /auth/register        Register a new user
POST /auth/login           Login (OAuth2 form), returns JWT
```

### Applications
```
POST   /applications                  Create a new application
GET    /applications                  List your applications (filter + paginate)
GET    /applications/upcoming         Applications with follow_up_date within N days
GET    /applications/{id}             Get a single application
PUT    /applications/{id}             Full update
PATCH  /applications/{id}             Partial update
DELETE /applications/{id}             Delete
```

**Query params for GET /applications:**
- `status` — filter by status enum value
- `skip` — pagination offset (default 0)
- `limit` — page size (default 20, max 100)

**Query params for GET /applications/upcoming:**
- `days` — look-ahead window (default 7, max 30)

### Contacts (nested under applications)
```
POST   /applications/{app_id}/contacts              Add a contact
GET    /applications/{app_id}/contacts              List contacts for an application
GET    /applications/{app_id}/contacts/{id}         Get a contact
PUT    /applications/{app_id}/contacts/{id}         Update a contact
DELETE /applications/{app_id}/contacts/{id}         Delete a contact
```

---

## Build Steps

### Step 1 — Dependencies
**`requirements.txt`**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
aiosqlite>=0.20.0
alembic>=1.13.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
```

**`requirements-dev.txt`**
```
pytest>=8.0.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
httpx>=0.27.0
```

### Step 2 — Environment Config (`app/config.py`)
Use `pydantic-settings` to load from `.env`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost/jobtracker"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

Copy `.env.example` → `.env` and fill in values.

### Step 3 — Database Layer (`app/database.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Step 4 — ORM Models (`app/models/`)
Use SQLAlchemy 2.x `Mapped` + `mapped_column` style. Define `ApplicationStatus` as a `str` enum so it serializes cleanly in both Pydantic and SQLAlchemy:

```python
class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
```

Store UUIDs as `String(36)` with `default=lambda: str(uuid.uuid4())` for SQLite/PostgreSQL compatibility.

Use `DateTime` for timestamps, set via Python `default` (not server-side) so SQLite works in tests.

### Step 5 — Pydantic Schemas (`app/schemas/`)
Three schema types per resource:
- `*Create` — required fields for POST body
- `*Update` — all fields optional for PATCH
- `*Response` — outbound shape with `model_config = ConfigDict(from_attributes=True)`

Pagination wrapper for list endpoints:
```python
class ApplicationList(BaseModel):
    items: list[ApplicationResponse]
    total: int
    skip: int
    limit: int
```

### Step 6 — Services Layer (`app/services/`)
Each service is a module of plain `async def` functions that take `db: AsyncSession` as their first argument. This separation makes unit testing independent of the HTTP layer.

Key auth functions:
- `get_password_hash(password)` / `verify_password(plain, hashed)`
- `create_access_token(data, expires_delta)`
- `authenticate_user(db, email, password)` — returns `User | None`

Key application functions:
- `get_applications(db, user_id, status, skip, limit)` → `(list[Application], int)`
- `get_upcoming_followups(db, user_id, days)` — filters `follow_up_date` between today and today+days

### Step 7 — Routers (`app/routers/`)
- Declare a `router = APIRouter(prefix="...", tags=[...])` per file
- All protected routes use `current_user = Depends(get_current_user)`
- **Route ordering matters:** define `/upcoming` before `/{id}` so FastAPI doesn't interpret "upcoming" as an ID

### Step 8 — Auth Dependency (`app/dependencies.py`)
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)):
    # Decode JWT → extract user_id → load from DB
    # Raise HTTP 401 on any failure
```

### Step 9 — App Factory (`app/main.py`)
```python
app = FastAPI(title="Job Tracker API", version="0.1.0")
app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(contacts_router)
```

Add a `GET /health` route that returns `{"status": "ok"}` — useful for CI smoke tests.

---

## Test Architecture

### conftest.py — Key Fixtures
| Fixture | Scope | Purpose |
|---|---|---|
| `setup_tables` | session | `create_all` once, `drop_all` after all tests |
| `clear_tables` | function, autouse | DELETE all rows between tests for isolation |
| `db` | function | Fresh `AsyncSession` bound to test engine |
| `client` | function | `httpx.AsyncClient` with `get_db` overridden |
| `auth_headers` | function | Registers + logs in a user, returns Bearer header dict |
| `second_user_headers` | function | Second user for ownership isolation tests |

**Key pattern — override the DB dependency:**
```python
async def override_get_db():
    yield db_session

app.dependency_overrides[get_db] = override_get_db
```

**Key pattern — test database URL:**
```python
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_jobtracker.db"  # default: no setup needed
)
```

In CI, set `TEST_DATABASE_URL` to the PostgreSQL service container URL.

### Test Coverage Targets
**`test_auth.py`** (register + login flows)
- [ ] Register success
- [ ] Register with duplicate email → 409
- [ ] Register with invalid email format → 422
- [ ] Login success → returns access token
- [ ] Login with wrong password → 401
- [ ] Login with unknown email → 401
- [ ] Access protected route without token → 401
- [ ] Access protected route with malformed token → 401

**`test_applications.py`** (full CRUD + edge cases)
- [ ] Create application — all fields
- [ ] Create application — required fields only
- [ ] Create application — missing required field → 422
- [ ] Create application — invalid status enum → 422
- [ ] Create unauthenticated → 401
- [ ] List applications — empty state
- [ ] List applications — returns own applications only
- [ ] List applications — filter by status
- [ ] List applications — pagination (skip/limit)
- [ ] Get application by ID — success
- [ ] Get application — not found → 404
- [ ] Get application — belongs to other user → 404
- [ ] Update application — full update
- [ ] Patch application — partial update (only status)
- [ ] Update application — not found → 404
- [ ] Delete application — success
- [ ] Delete application — not found → 404
- [ ] Delete application — owned by another user → 404
- [ ] Get upcoming followups — returns correct window
- [ ] Get upcoming followups — excludes past dates

**`test_contacts.py`** (nested resource + ownership)
- [ ] Create contact on own application — success
- [ ] Create contact on nonexistent application → 404
- [ ] Create contact on another user's application → 404
- [ ] List contacts — returns contacts for that application only
- [ ] Get contact by ID — success
- [ ] Get contact — not found → 404
- [ ] Update contact — success
- [ ] Delete contact — success
- [ ] Deleting parent application cascades to contacts

---

## Docker Setup

> Referenced in step 3 of [Getting Started](#getting-started-do-this-first). Create these two files before writing any app code.

### Files to Create
**`Dockerfile`** — multi-stage build to keep the final image small:
```dockerfile
# ---- build stage ----
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`** — spins up the API and a PostgreSQL database together:
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: jobtracker_dev   # creates this database on first volume init
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@db/jobtracker_dev}
      SECRET_KEY: ${SECRET_KEY:-change-me-in-development}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app          # mount source for hot reload during development
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

> **Key choices:**
> - `postgres:16-alpine` keeps the DB image under 100 MB
> - `healthcheck` + `condition: service_healthy` ensures the API only starts after Postgres is accepting connections (avoids "connection refused" race conditions)
> - The source volume mount + `--reload` flag gives you live code reloading during development without rebuilding the image on every change
> - `${DATABASE_URL:-...}` reads from your `.env` file if set, otherwise falls back to `jobtracker_dev` — this is how you switch between environments without editing `docker-compose.yml`

### Build Step — Docker (`app/main.py` startup event)
Add a lifespan handler to run migrations or verify the DB connection on startup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup — good place to verify DB connection
    yield
    # Runs on shutdown

app = FastAPI(title="Job Tracker API", version="0.1.0", lifespan=lifespan)
```

For production, call `alembic upgrade head` in a separate container command (or an `init` entrypoint script) rather than inside `lifespan`, to keep the concerns separated.

---

## Running Locally

Everything runs in Docker. All three environments share the same postgres container but use separate databases.

### First-Time Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/job-tracker.git
cd job-tracker

# 2. Create your .env file (gitignored — never committed)
cp .env.example .env
# Edit .env and set a real SECRET_KEY value

# 3. Start the stack — postgres_data volume is created on first run
docker compose up --build

# 4. In a separate terminal, run migrations against the dev database
docker compose exec api alembic upgrade head

# API docs: http://localhost:8000/docs
# PostgreSQL: localhost:5432
```

### Switching Environments

Docker Compose reads your `.env` file automatically. To switch which database the API connects to, update `DATABASE_URL` in `.env` and restart:

**Working on `dev` branch (default):**
```bash
# .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/jobtracker_dev
```

**Switching to `staging` branch:**
```bash
# 1. Create the staging database if it doesn't exist yet
docker compose exec db createdb -U postgres jobtracker_staging

# 2. Update .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/jobtracker_staging

# 3. Apply migrations to the staging database
docker compose exec api alembic upgrade head

# 4. Restart the api container to pick up the new DATABASE_URL
docker compose restart api
```

The `postgres_data` volume holds all databases. Switching `DATABASE_URL` does not affect the other databases — `jobtracker_dev` and `jobtracker_staging` coexist on the same volume.

### Daily Commands

```bash
docker compose up                      # start the stack (hot reload on)
docker compose down                    # stop — data is safe, volume kept
docker compose down -v                 # stop + delete volume (wipes all databases)
docker compose exec api bash           # shell inside the running api container
docker compose restart api             # pick up .env changes without full rebuild
```

## Running Tests

### With Docker (uses PostgreSQL, matches CI exactly)
```bash
docker compose run --rm \
  -e TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/test_jobtracker \
  api pytest --cov=app --cov-report=term-missing
```

### Without Docker (uses SQLite — no setup required)
```bash
# Install dev dependencies if you haven't already
pip install -r requirements-dev.txt

pytest --cov=app --cov-report=term-missing
```

To run against a local PostgreSQL database:

```bash
TEST_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/test_jobtracker" \
  pytest --cov=app --cov-report=term-missing
```

---

## Accessing the Database in VS Code

Two extensions are needed:
- **SQLTools** — the query interface
- **SQLTools PostgreSQL/Cockroach Driver** — the database driver SQLTools uses to connect

Install both from the Extensions panel (`Cmd+Shift+X`) by searching for each name.
- both extensions are authored by Matheus Teixeira (publisher ID mtxr on the VS Code Marketplace)

### Create a Connection

1. Click the **SQLTools** icon in the Activity Bar (cylinder/database icon on the left sidebar)
2. Click **Add New Connection**
3. Select **PostgreSQL**
4. Fill in the connection details:

| Field | Value |
|---|---|
| Connection name | `job-tracker-dev` (or any label you want) |
| Host | `localhost` |
| Port | `5432` |
| Database | `jobtracker_dev` |
| Username | `postgres` |
| Password | `postgres` |

5. Click **Test Connection** — it should show a success message (the Docker stack must be running)
6. Click **Save Connection**

> The stack must be running (`docker compose up`) before you can connect. SQLTools connects to the port mapped to your host machine (5432), not inside the container.

### Running Queries

1. Click your saved connection in the SQLTools sidebar to open it
2. Click the **New SQL File** icon (or right-click the connection → **New SQL File**) — this creates a `*.session.sql` scratch file
3. Type a query and press `Cmd+Enter` (or click **Run**) to execute it:

```sql
-- See all tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- See all users
SELECT id, email, full_name, created_at FROM users;

-- See all applications for a specific user
SELECT id, company_name, job_title, status, applied_date
FROM applications
WHERE user_id = '<paste-user-id-here>'
ORDER BY created_at DESC;

-- See all applications with their contacts
SELECT a.company_name, a.job_title, c.name AS contact_name, c.email
FROM applications a
LEFT JOIN contacts c ON c.application_id = a.id
WHERE a.user_id = '<paste-user-id-here>';
```

### Notes

- The `*.session.sql` files SQLTools creates are gitignored — they're local scratch files and won't be committed
- To switch to the staging database, create a second connection pointing to `jobtracker_staging` (same host/port/credentials, different database name)
- If you get a "connection refused" error, make sure `docker compose up` is running

---

## CI/CD Pipeline (`.github/workflows/ci.yml`)

The pipeline triggers on all three protected branches. Staging is local, so CI only has one deployment job — production — which is a placeholder until a hosting platform is chosen.

```
dev push     → test
staging push → test
main push    → test → build image (deploy placeholder)
```

```yaml
name: CI

on:
  push:
    branches: [dev, staging, main]
  pull_request:
    branches: [dev, staging, main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_jobtracker
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests with coverage
        run: pytest --cov=app --cov-report=xml --cov-fail-under=90
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/jobtracker
          TEST_DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/test_jobtracker
          SECRET_KEY: ci-secret-key
      - uses: codecov/codecov-action@v4
        with: { file: ./coverage.xml }

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - uses: actions/checkout@v4
      - name: Build and tag Docker image
        run: |
          docker build \
            -t job-tracker-api:${{ github.sha }} \
            -t job-tracker-api:latest .
      # Add your hosting platform's deploy step here when ready.
      # Optional: push to GitHub Container Registry (GHCR)
      # - uses: docker/login-action@v3
      #   with:
      #     registry: ghcr.io
      #     username: ${{ github.actor }}
      #     password: ${{ secrets.GITHUB_TOKEN }}
      # - run: |
      #     docker tag job-tracker-api:${{ github.sha }} ghcr.io/${{ github.repository }}:${{ github.sha }}
      #     docker tag job-tracker-api:latest ghcr.io/${{ github.repository }}:latest
      #     docker push ghcr.io/${{ github.repository }} --all-tags
```

**Key points:**
- `test` runs on all three branches and every PR — it's the required status check for branch protection
- No `deploy-staging` job — staging runs locally in Docker, so there's nothing for CI to deploy
- `deploy-production` only runs on merges to `main`, and only after `test` passes
- The deploy steps are placeholders — add them when a hosting platform is chosen
- When a deployed staging environment is added later, a `deploy-staging` job can be inserted without changing anything else

---

## Database Migrations (Alembic)

```bash
# Initialize (first time only)
alembic init alembic

# Generate a migration after changing models
alembic revision --autogenerate -m "describe the change"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

Configure `alembic/env.py` to use your async engine and import `Base.metadata` from `app.database`.

---

## Portfolio Highlights

- **Containerized with Docker** — multi-stage Dockerfile keeps the production image small; `docker-compose.yml` spins up the full dev stack in one command with no local PostgreSQL required
- **User data isolation** enforced at the service layer — every query filters by `user_id`, so users can never read or modify each other's data
- **Cascading deletes** — deleting an application automatically deletes all its contacts (SQLAlchemy `cascade="all, delete-orphan"`)
- **Pagination + filtering** on list endpoints with a total count in the response
- **Upcoming follow-ups endpoint** — practical feature that queries by date range
- **Dependency injection** for the database session, making the test override pattern clean and explicit
- **90%+ coverage gate** enforced in CI — shows the coverage can't silently regress
- **Three-environment strategy** — `dev` → `staging` → `main` promotion flow with branch protection rules enforcing the chain; staging used for manual QA, test database kept separate and ephemeral
- **Environment-gated CI pipeline** — tests run on every branch; staging and production deploys only trigger on their respective branches using GitHub Environments for per-environment secrets
