# Job Application Tracker API

> A REST API for tracking job applications, contacts, statuses, and follow-up dates — built with Python, FastAPI, PostgreSQL, and Docker.

![Build Status](https://img.shields.io/github/actions/workflow/status/tristabug/job-tracker/ci.yml?branch=main)
![Coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen) <!-- TODO: make coverage dynamic -->
![License](https://img.shields.io/github/license/tristabug/job-tracker)

[Report a Bug](https://github.com/tristabug/job-tracker/issues) · [Request a Feature](https://github.com/tristabug/job-tracker/issues)


## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Related Projects](#related-projects)
- [Contributing](#contributing)
- [License](#license)


## Overview

Job Application Tracker is a production-quality REST API for managing a job search. It lets users log job applications, track status changes through the hiring pipeline, attach recruiter and hiring manager contacts to each application, and surface upcoming follow-up dates — all behind JWT authentication so each user sees only their own data.

**Live:** [API docs](https://jobtracker-api.saraeclark.com/docs) · [job-tracker-ui demo](https://jobtracker.saraeclark.com)

<!-- TODO: add screenshots -->


## Features

- **Full job application lifecycle tracking**: six status values (`applied`, `phone_screen`, `interview`, `offer`, `rejected`, `withdrawn`) with filtering and pagination on list endpoints
- **Upcoming follow-ups endpoint**: queries applications by follow-up date window so nothing falls through the cracks
- **Nested contact management**: attach multiple contacts (recruiters, hiring managers) to any application
- **JWT authentication**: all routes protected; user data is fully isolated at the service layer
- **Role-based access**: `demo`, `user`, and `admin` roles via `GET /auth/me`; the shared `demo` account is enforced as read-only (403 on any write) so portfolio visitors can explore safely
- **Cascading deletes**: deleting an application automatically removes all its contacts
- **Containerized with Docker**: multi-stage Dockerfile + Docker Compose spins up the full stack in one command with no local PostgreSQL required
- **90%+ test coverage**: enforced in CI via pytest-cov; PRs that drop below threshold fail the pipeline
<!-- TODO: add architecture diagram or high-level overview -->

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Python 3.12 + FastAPI |
| Database | PostgreSQL (production), SQLite (local test runs) |
| ORM | SQLAlchemy 2.x async |
| Migrations | Alembic |
| Auth | JWT via python-jose + bcrypt |
| Testing | pytest + httpx + pytest-cov |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |


## Prerequisites

- **Docker** ≥ 24.x and **Docker Compose** ≥ 2.x — the entire stack runs in containers; no local Python or PostgreSQL install required
- **A terminal**
- **Git** ≥ 2.x *(optional — for cloning the repository)*


## Installation

### 1. Get the repository

**Option A — clone with Git:**
```bash
git clone https://github.com/tristabug/job-tracker.git
cd job-tracker
```

**Option B — download as ZIP (no Git required):**
1. Go to `https://github.com/tristabug/job-tracker`
2. Click **Code → Download ZIP**
3. Unzip the file and open a terminal in the project folder

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your values. All required keys are listed below.

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string for the API | `postgresql+asyncpg://postgres:postgres@db/jobtracker_dev` |
| `SECRET_KEY` | Secret key used to sign JWT tokens — use a long random string in production | `change-me-to-a-long-random-string` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long access tokens stay valid (in minutes) | `30` |
| `DEMO_EMAIL` | Login email for the shared, read-only demo account (see [Demo Account](#demo-account)) | `demo@jobtracker.dev` |
| `DEMO_PASSWORD` | Login password for the shared, read-only demo account | `DemoPass123!` |

> **Never commit real secrets.** `.env` is gitignored and should never be pushed to the repository.

### 3. Start the stack

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. The postgres container starts first; the API waits for it to be healthy before accepting connections.

### 4. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Seed the demo account (optional)

```bash
docker compose exec api python -m scripts.seed_demo
```

Creates the shared, read-only `demo` account (see [Demo Account](#demo-account)) pre-populated with sample applications and contacts. Safe to re-run — it does nothing if the account is already seeded.

### Switching Environments

The stack uses whichever database is set in `DATABASE_URL`. To switch to staging:

```bash
# Create the staging database (first time only)
docker compose exec db createdb -U postgres jobtracker_staging

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/jobtracker_staging

# Apply migrations and restart
docker compose exec api alembic upgrade head
docker compose restart api
```

### Daily Commands

```bash
docker compose up                   # start the stack (hot reload on)
docker compose down                 # stop — volume and data preserved
docker compose down -v              # stop and wipe all database volumes
docker compose exec api bash        # shell inside the running api container
docker compose restart api          # reload after .env changes
```


## Usage

### API Endpoints

#### Auth

```
POST /auth/register     Register a new user
POST /auth/login        Login (OAuth2 form), returns JWT
GET  /auth/me           Get the current authenticated user (includes role)
```

#### Applications

```
POST   /applications              Create a new application
GET    /applications              List your applications (filter + paginate)
GET    /applications/upcoming     Applications with follow_up_date within N days
GET    /applications/{id}         Get a single application
PUT    /applications/{id}         Full update
PATCH  /applications/{id}         Partial update
DELETE /applications/{id}         Delete
```

Query params for `GET /applications`:
- `status` — filter by status value
- `skip` — pagination offset (default 0)
- `limit` — page size (default 20, max 100)

Query params for `GET /applications/upcoming`:
- `days` — look-ahead window (default 7, max 30)

#### Contacts (nested under applications)

```
POST   /applications/{app_id}/contacts           Add a contact
GET    /applications/{app_id}/contacts           List contacts
GET    /applications/{app_id}/contacts/{id}      Get a contact
PUT    /applications/{app_id}/contacts/{id}      Update a contact
DELETE /applications/{app_id}/contacts/{id}      Delete a contact
```

> **Note:** All `POST`/`PUT`/`PATCH`/`DELETE` routes above return `403 Forbidden` for users with the `demo` role. See [Demo Account](#demo-account).


### Using Swagger UI

Swagger UI is built into FastAPI and requires no additional setup. With the stack running, open `http://localhost:8000/docs` in your browser.

**Create an account:**
1. Click `POST /auth/register` → **Try it out**
2. Fill in your email, password, and name in the request body
3. Click **Execute**

**Log in and authorize:**
1. Click `POST /auth/login` → **Try it out**
2. Fill in your `username` (email) and `password`
3. Click **Execute**
4. Click the **Authorize** button at the top right of the page
5. Enter your username and password in the form and click **Authorize**

All subsequent requests in Swagger will automatically include your token. Authorization does not persist across page refreshes — you will need to log in and re-authorize if you reload the page.

**Create an application:**
1. Click `POST /applications` → **Try it out**
2. Fill in the request body — at minimum `company_name`, `job_title`, and `status`
3. Click **Execute**

**List your applications:**
1. Click `GET /applications` → **Try it out**
2. Optionally set `status`, `skip`, or `limit` query params to filter or paginate
3. Click **Execute**


### Using curl

**Register and log in:**

```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword", "full_name": "Your Name"}'

# Log in and get a token — copy the access_token value from the response
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=yourpassword"
```

**Create and list applications:**

```bash
# Create an application
curl -X POST http://localhost:8000/applications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "job_title": "Software Engineer",
    "status": "applied",
    "follow_up_date": "2026-04-18"
  }'

# List your applications
curl http://localhost:8000/applications \
  -H "Authorization: Bearer <token>"
```

Replace `<token>` with the `access_token` value returned from the login response.

**Tip — save your token to a variable** so you don't have to paste it into every request:

```bash
TOKEN="your-access-token-here"
```

Then reference it in any request:

```bash
curl http://localhost:8000/applications \
  -H "Authorization: Bearer $TOKEN"
```

The variable lasts for the duration of your terminal session. If you close the terminal or open a new one, you'll need to log in and set it again.


### Demo Account

A shared, read-only account is available for exploring the API without registering. Credentials come from the `DEMO_EMAIL` / `DEMO_PASSWORD` environment variables (defaults: `demo@jobtracker.dev` / `DemoPass123!`).

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@jobtracker.dev&password=DemoPass123!"
```

Log in with these credentials to browse a pre-populated set of applications and contacts. `GET /auth/me` returns `"role": "demo"` for this account, and any write request (`POST`/`PUT`/`PATCH`/`DELETE`) returns `403 Forbidden` — read-only access is enforced server-side via the `require_write_access` dependency, regardless of what a client UI allows.

To create or refresh the demo account's sample data:

```bash
docker compose exec api python -m scripts.seed_demo
```

The script is idempotent: it only seeds sample applications/contacts if the account doesn't already have any, and corrects the account's `role` to `demo` if it was registered as a normal user first.


### Accessing the Database in VS Code

Install the **SQLTools** and **SQLTools PostgreSQL/Cockroach Driver** extensions (both by Matheus Teixeira). Create a connection pointing to `localhost:5432`, database `jobtracker_dev`, username and password both `postgres`. The Docker stack must be running before connecting. To query staging, create a second connection pointing to `jobtracker_staging`.


## Running Tests

```bash
# With Docker — uses PostgreSQL, matches CI exactly
docker compose run --rm \
  -e TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db/test_jobtracker \
  api pytest --cov=app --cov-report=term-missing

# Without Docker — uses SQLite, no setup required
pytest --cov=app --cov-report=term-missing
```

Coverage threshold is enforced at **90%** in CI. PRs that drop below this will fail the pipeline.


## Deployment

The API is deployed at **https://jobtracker-api.saraeclark.com** (`/docs` for interactive API docs), running on `main`. [`job-tracker-ui`](https://github.com/tristabug/job-tracker-ui) is deployed alongside it at **https://jobtracker.saraeclark.com**.

### CI/CD Pipeline

The pipeline triggers on pushes and pull requests to all three protected branches.

```
dev push     → test
staging push → test
main push    → test → deploy-production
```

The `test` job runs pytest against a PostgreSQL service container and enforces the 90% coverage threshold. The `deploy-production` job runs on a self-hosted runner on sara-server: it pulls the latest `main` into `~/apps/job-tracker` and runs `docker compose -f docker-compose.yml up --build -d`, redeploying the API automatically.

> **Database migrations are not automated.** If a merged change includes a new Alembic migration, run `docker compose exec api alembic upgrade head` on sara-server by hand after the deploy completes.

[`job-tracker-ui`](https://github.com/tristabug/job-tracker-ui) follows the same `dev → staging → main` promotion flow and is deployed alongside this API on sara-server via the same pattern.

### Branch & Environment Strategy

| Environment | Branch | Database |
|---|---|---|
| Development | `dev` | `jobtracker_dev` |
| Staging | `staging` | `jobtracker_staging` |
| Production | `main` | `jobtracker` |
| Test | (any) | `jobtracker_test` — wiped after every run |

Promotion flow: `feature-branch → dev → staging → main`. No direct pushes to `main` or `staging` — all changes go through PRs with the `test` CI check required to pass.


## Related Projects

[`job-tracker-ui`](https://github.com/tristabug/job-tracker-ui) is a Flask front end that consumes this API. [`API_CONTRACT_CHECKLIST.md`](./API_CONTRACT_CHECKLIST.md) documents the parts of this API's contract (auth, roles, applications, contacts, error codes, demo account) that the UI depends on — update it alongside any breaking API change.


## Contributing

> **Note:** This repository is not currently open to public contributions. The standards below apply to those with write access to the repository.

### Branching & PR Process

1. Cut a branch from `dev`:
   ```bash
   git checkout dev && git pull origin dev
   git checkout -b feat/your-feature-name
   # also: fix/description, chore/description
   ```
2. Make your changes and ensure tests pass locally
3. Open a PR into `dev` — the `test` CI job must pass before merging
4. When `dev` is stable, PRs flow `dev → staging → main`

### Commit Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add resume upload endpoint
fix: correct token expiry calculation
chore: update dependencies
```


## License

Distributed under the **MIT License**. See [LICENSE](./LICENSE) for details.

*Built and maintained by [tristabug](https://github.com/tristabug)*
