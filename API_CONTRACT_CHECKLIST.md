# API Contract Checklist

This file documents the parts of the `job-tracker` API contract that [`job-tracker-ui`](https://github.com/tristabug/job-tracker-ui) (a separate Flask front end) depends on.

**Process:** when a PR changes any endpoint, request/response field, status code, or role behavior listed below, update this file in the same PR and note in the PR description whether `job-tracker-ui` needs a corresponding change.


## Auth

| Method & Path | Auth | Request | Response |
|---|---|---|---|
| `POST /auth/register` | none | `{email, password, full_name?}` | `201 UserResponse` / `409` if email taken / `422` validation |
| `POST /auth/login` | none | OAuth2 form: `username` (email), `password` | `200 Token {access_token, token_type}` / `401` invalid credentials |
| `GET /auth/me` | Bearer | — | `200 UserResponse` / `401` |

### `UserResponse`

```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string | null",
  "role": "demo | user | admin",
  "created_at": "datetime"
}
```

`job-tracker-ui` uses `role` to:
- Show a "read-only demo" banner and hide/disable write controls when `role == "demo"` (the API enforces this server-side regardless — see [Demo Account](#demo-account))
- Gate any future admin-only UI on `role == "admin"`


## Applications

| Method & Path | Auth | Notes |
|---|---|---|
| `POST /applications` | Bearer, write access | Create |
| `GET /applications` | Bearer | List, paginated |
| `GET /applications/upcoming` | Bearer | Follow-ups within `days` |
| `GET /applications/{id}` | Bearer | Single application |
| `PUT /applications/{id}` | Bearer, write access | Full update |
| `PATCH /applications/{id}` | Bearer, write access | Partial update |
| `DELETE /applications/{id}` | Bearer, write access | Cascades to contacts |

Query params:
- `GET /applications`: `status` (filter), `skip` (default 0), `limit` (default 20, max 100)
- `GET /applications/upcoming`: `days` (default 7, max 30)

### `ApplicationCreate` / `ApplicationUpdate`

```json
{
  "company_name": "string",
  "job_title": "string",
  "job_url": "string | null",
  "status": "applied | phone_screen | interview | offer | rejected | withdrawn",
  "applied_date": "date",
  "follow_up_date": "date | null",
  "notes": "string | null"
}
```

`ApplicationCreate` defaults `status` to `applied` and `applied_date` to today. All fields on `ApplicationUpdate` are optional (partial update via `PATCH`, full replace via `PUT`).

### `ApplicationResponse`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "company_name": "string",
  "job_title": "string",
  "job_url": "string | null",
  "status": "applied | phone_screen | interview | offer | rejected | withdrawn",
  "applied_date": "date",
  "follow_up_date": "date | null",
  "notes": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `ApplicationList`

```json
{
  "items": ["ApplicationResponse"],
  "total": "int",
  "skip": "int",
  "limit": "int"
}
```


## Contacts (nested under applications)

| Method & Path | Auth | Notes |
|---|---|---|
| `POST /applications/{app_id}/contacts` | Bearer, write access | Create |
| `GET /applications/{app_id}/contacts` | Bearer | List |
| `GET /applications/{app_id}/contacts/{id}` | Bearer | Single contact |
| `PUT /applications/{app_id}/contacts/{id}` | Bearer, write access | Update |
| `DELETE /applications/{app_id}/contacts/{id}` | Bearer, write access | Delete |

### `ContactCreate` / `ContactUpdate`

```json
{
  "name": "string",
  "title": "string | null",
  "email": "string | null",
  "phone": "string | null",
  "linkedin_url": "string | null",
  "notes": "string | null"
}
```

### `ContactResponse`

```json
{
  "id": "uuid",
  "application_id": "uuid",
  "user_id": "uuid",
  "name": "string",
  "title": "string | null",
  "email": "string | null",
  "phone": "string | null",
  "linkedin_url": "string | null",
  "notes": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```


## Error Contract

| Status | Meaning |
|---|---|
| `401` | Missing, invalid, or expired token |
| `403` | `demo`-role user attempting a write (`require_write_access`) |
| `404` | Resource not found, or not owned by the current user |
| `409` | `POST /auth/register` with an email that's already registered |
| `422` | Request body/query validation error |


## Demo Account

- A shared account with `role == "demo"`, enforced as **read-only** server-side: any `POST`/`PUT`/`PATCH`/`DELETE` to `/applications` or nested `/contacts` returns `403`.
- Credentials come from `DEMO_EMAIL` / `DEMO_PASSWORD` env vars (defaults: `demo@jobtracker.dev` / `DemoPass123!`).
- Seeded via `python -m scripts.seed_demo` (idempotent) with 6 sample applications — one per `status` value — and a few sample contacts.
- `job-tracker-ui`'s `/demo` route logs in with these credentials directly so visitors can explore without registering.
