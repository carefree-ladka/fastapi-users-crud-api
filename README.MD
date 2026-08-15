# FastAPI Demo

A small, layered FastAPI application demonstrating a clean project structure:
routers (controllers), services (business logic), repositories (data access),
Pydantic schemas, and environment-based configuration.

The API ships with a versioned `users` CRUD resource backed by a local SQLite
database (via SQLAlchemy 2.0, seeded with sample data on first run) and a
health-check endpoint.

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

Settings are cached, so changes to `.env` require a server restart to take
effect.

## API endpoints

All routes are mounted under `API_V1_PREFIX` (default `/api/v1`).

| Method   | Path                      | Description              |
| -------- | ------------------------- | ------------------------ |
| `GET`    | `/`                       | Redirects to `/docs`.    |
| `GET`    | `/api/v1/health`          | Health check.            |
| `GET`    | `/api/v1/users`           | List all users.          |
| `GET`    | `/api/v1/users/{user_id}` | Get a user by ID.        |
| `POST`   | `/api/v1/users`           | Create a user.           |
| `PUT`    | `/api/v1/users/{user_id}` | Replace a user.          |
| `PATCH`  | `/api/v1/users/{user_id}` | Partially update a user. |
| `DELETE` | `/api/v1/users/{user_id}` | Delete a user.           |

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
│   └── exceptions.py           # Domain exceptions
├── db/
│   ├── session.py              # Engine, session factory, Base, get_db dependency
│   └── init_db.py              # Table creation + seeding on startup
├── dependencies/
│   └── user.py                 # Depends() providers (session, repository, service)
├── routers/
│   ├── health.py               # Health endpoint
│   └── users.py                # User endpoints (thin controllers)
├── services/
│   └── user_service.py         # Business logic
├── repositories/
│   └── user_repository.py      # SQLAlchemy data access (+ seed data)
├── models/
│   └── user.py                 # SQLAlchemy ORM model
└── schemas/
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
