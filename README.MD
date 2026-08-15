# FastAPI Demo

A small, layered FastAPI application demonstrating a clean project structure:
routers (controllers), services (business logic), repositories (data access),
Pydantic schemas, and environment-based configuration.

The API ships with a versioned `users` CRUD resource backed by a local SQLite
database (via SQLAlchemy 2.0, seeded with sample data on first run), a
health-check endpoint, and cookie-based JWT authentication with role-based
access control and CSRF protection.

## Requirements

- Python 3.11+ (the local virtual environment uses 3.14)
- [`uv`](https://docs.astral.sh/uv/) or `pip` for dependency management

## Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install runtime dependencies
pip install fastapi uvicorn python-dotenv "sqlalchemy>=2.0"

# (Optional) install dev tools for the quality gates
pip install -e ".[dev]"
pre-commit install

# Copy the example environment file and adjust as needed
cp .env.example .env
```

## Running

```bash
.venv/bin/uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`. Opening the root URL redirects to
the interactive docs.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Configuration

Settings are read from environment variables, with a local `.env` file loaded
automatically at startup (see `app/core/config.py`). Real environment variables
take precedence over values in `.env`.

| Variable          | Default             | Description                                        |
| ----------------- | ------------------- | -------------------------------------------------- |
| `APP_NAME`        | `RAG API`           | Display name shown in the OpenAPI docs.            |
| `APP_VERSION`     | `0.1.0`             | Version shown in the OpenAPI docs.                 |
| `APP_DESCRIPTION` | `Local-first AI API.` | Short description shown in the OpenAPI docs.     |
| `API_V1_PREFIX`   | `/api/v1`           | Prefix all v1 routes are mounted under. Set empty to serve routes without a prefix (e.g. `/users`). |
| `DATABASE_URL`    | `sqlite:///./app.db` | SQLAlchemy connection string. Point at Postgres/MySQL by changing this value. |
| `SECRET_KEY`      | `dev-insecure-change-me` | Secret used to sign JWTs. **Must** be a strong random value in production. |
| `JWT_ALGORITHM`   | `HS256`             | JWT signing algorithm. |
| `ACCESS_TOKEN_TTL_MINUTES` | `15`       | Access-token lifetime (minutes). |
| `REFRESH_TOKEN_TTL_DAYS`   | `7`        | Refresh-token lifetime (days). |
| `COOKIE_SECURE`   | `false`             | Send cookies only over HTTPS. Set `true` in production. |
| `COOKIE_SAMESITE` | `lax`               | Cookie SameSite policy: `lax`, `strict`, or `none`. |
| `COOKIE_DOMAIN`   | _(unset)_           | Optional cookie domain. |

Settings are cached, so changes to `.env` require a server restart to take
effect. Generate a production secret with:
`python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## API endpoints

All routes are mounted under `API_V1_PREFIX` (default `/api/v1`).

| Method   | Path                       | Description              | Access |
| -------- | -------------------------- | ------------------------ | ------ |
| `GET`    | `/`                        | Redirects to `/docs`.    | public |
| `GET`    | `/api/v1/health`           | Health check.            | public |
| `POST`   | `/api/v1/auth/register`    | Register + start session.| public |
| `POST`   | `/api/v1/auth/login`       | Log in + start session.  | public |
| `POST`   | `/api/v1/auth/refresh`     | Rotate tokens.           | cookie + CSRF |
| `POST`   | `/api/v1/auth/logout`      | Revoke session.          | cookie + CSRF |
| `GET`    | `/api/v1/auth/me`          | Current user.            | authenticated |
| `GET`    | `/api/v1/users`            | List all users.          | admin |
| `GET`    | `/api/v1/users/{user_id}`  | Get a user by ID.        | admin or self |
| `POST`   | `/api/v1/users`            | Create a user.           | admin + CSRF |
| `PUT`    | `/api/v1/users/{user_id}`  | Replace a user.          | admin + CSRF |
| `PATCH`  | `/api/v1/users/{user_id}`  | Partially update a user. | admin + CSRF |
| `DELETE` | `/api/v1/users/{user_id}`  | Delete a user.           | admin + CSRF |

### Example: create a user

The `POST /api/v1/users` body requires `name`, `email`, and `age`
(`is_active` and `role` are optional).

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Ada", "email": "ada@example.com", "age": 30}'
```

## Response format

All user endpoints return a consistent, readable envelope.

Success (e.g. `POST /api/v1/users` → `201`):

```json
{
  "success": true,
  "message": "User 'Ada' created successfully",
  "data": { "id": 11, "name": "Ada", "email": "ada@example.com", "age": 30, "is_active": false, "role": "user" }
}
```

Delete returns a message-only envelope (`200`):

```json
{ "success": true, "message": "User 1 deleted successfully" }
```

Errors use a matching shape with an HTTP status and machine-readable `code`:

| Situation           | Status | `error.code`            |
| ------------------- | ------ | ----------------------- |
| Not authenticated   | `401`  | `authentication_failed` |
| Insufficient role   | `403`  | `permission_denied`     |
| CSRF check failed   | `403`  | `csrf_failed`           |
| User not found      | `404`  | `user_not_found`        |
| Duplicate email     | `409`  | `email_already_exists`  |
| Invalid request body| `422`  | `validation_error`      |
| Unexpected failure  | `500`  | `internal_server_error` |

```json
{
  "success": false,
  "message": "Request validation failed",
  "error": {
    "code": "validation_error",
    "details": [
      { "field": "age", "message": "Field required" }
    ]
  }
}
```

## Authentication & authorization

Auth is cookie-based with JWTs and a refresh-token rotation scheme.

- **register / login** issue two httpOnly cookies — a short-lived
  `access_token` and a longer-lived `refresh_token` (scoped to the `/auth`
  path) — plus a readable `csrf_token` cookie.
- **refresh** validates the refresh token, revokes it, and issues a fresh pair
  (rotation). Reusing a rotated refresh token is rejected.
- **logout** revokes the refresh token server-side and clears the cookies.
- **RBAC**: new registrations get the `user` role. Admin-only endpoints require
  `role == "admin"`; `GET /users/{id}` also allows a user to read their own
  record.

### CSRF (double-submit)

Because the JWT lives in an httpOnly cookie, state-changing requests that rely
on that ambient cookie (`refresh`, `logout`, and all admin user writes) require
the value of the readable `csrf_token` cookie to be echoed back in the
`X-CSRF-Token` header. `register` and `login` are exempt (no session exists
yet).

### Example flow

```bash
# 1) Log in (cookies are stored in cookies.txt). Seeded admin: Priya.
curl -c cookies.txt -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "priya.singh@example.com", "password": "password123"}'

# 2) Read the CSRF token from the cookie jar and call an admin write endpoint.
CSRF=$(awk '/csrf_token/ {print $7}' cookies.txt)
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" -H "X-CSRF-Token: $CSRF" \
  -d '{"name": "New User", "email": "new@example.com", "age": 22}'
```

> Seeded users all share the demo password `password123` (see
> `app/db/init_db.py`); Priya and Arjun have the `admin` role.

## Quality gates

The project uses the Python equivalents of ESLint/Prettier:

- **Ruff** — linter and formatter (config in `pyproject.toml`).
- **mypy** — strict static type checking.
- **pre-commit** — runs all gates automatically on `git commit`.

Run them manually:

```bash
ruff format app        # format (like Prettier)
ruff check app         # lint (like ESLint); add --fix to autofix
mypy                   # type-check the app package

pre-commit run --all-files   # run every gate across the repo
```

Once `pre-commit install` has been run, these gates run on every commit and
block the commit if anything fails.

## Project structure

```
app/
├── main.py                     # App factory, exception handlers, root redirect
├── api/
│   └── v1/
│       └── router.py           # Aggregates all v1 routers
├── core/
│   ├── config.py               # Settings (loads .env)
│   ├── cookies.py              # Auth cookie set/clear helpers
│   ├── exceptions.py           # Domain exceptions
│   └── security.py             # Password hashing, JWT, CSRF tokens
├── db/
│   ├── session.py              # Engine, session factory, Base, get_db dependency
│   └── init_db.py              # Table creation + seeding on startup
├── dependencies/
│   ├── auth.py                 # current-user, require_admin, csrf_protect
│   └── user.py                 # Depends() providers (session, repository, service)
├── routers/
│   ├── auth.py                 # register / login / refresh / logout / me
│   ├── health.py               # Health endpoint
│   └── users.py                # User endpoints (thin controllers)
├── services/
│   ├── auth_service.py         # Auth business logic (tokens, rotation)
│   └── user_service.py         # Business logic
├── repositories/
│   ├── refresh_token_repository.py  # Refresh-token persistence/revocation
│   └── user_repository.py      # SQLAlchemy data access (+ seed data)
├── models/
│   ├── refresh_token.py        # RefreshToken ORM model
│   └── user.py                 # SQLAlchemy ORM model
└── schemas/
    ├── auth.py                 # Register/login/token schemas
    ├── response.py             # Standard response envelopes
    └── user.py                 # Pydantic request/response schemas
```

## Database

- Data is stored in a local SQLite file (default `./app.db`), created
  automatically on first startup.
- Tables are created and seeded with sample users on startup only if the
  `users` table is empty, so data persists across restarts.
- To start fresh, stop the server and delete the database file:
  ```bash
  rm app.db
  ```
- The repository layer talks only to a SQLAlchemy `Session`, so switching to
  Postgres/MySQL is just a `DATABASE_URL` change (plus installing the driver).

## Notes

- Not-found errors raise a domain exception that a global handler translates
  into a `404` response.
- The SQLite file (`app.db`) is local state and generally should not be
  committed; add it to `.gitignore`.
