# FastAPI Skeleton: JWT Auth, SQLite, Rate Limiting

## Stack
- FastAPI + Uvicorn
- SQLite via SQLAlchemy async (aiosqlite)
- JWT (HS256)
- In-memory token-bucket rate limiting
- Pydantic Settings with `.env`

## Structure
```
app/
  api/
    routes/
      auth.py
      users.py
      public.py
    deps.py
    router.py
  core/
    config.py
    security.py
    rate_limit.py
  db/
    session.py
    models.py
    init_db.py
  schemas/
    auth.py
    user.py
  main.py
.env.example
requirements.txt
```

## Quickstart
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Auth Flow
- `POST /api/v1/auth/register` → create user
- `POST /api/v1/auth/login` → returns `access_token` (JWT) and `refresh_token`
- `GET /api/v1/users/me` → requires `Authorization: Bearer <access_token>`
- `POST /api/v1/auth/refresh` → exchange `refresh_token` for new access token
- `POST /api/v1/auth/logout` → revoke refresh token

### Example
```
curl -X POST http://127.0.0.1:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email":"a@a.com","full_name":"Alice","password":"pass"}'

curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"a@a.com","password":"pass"}'
# -> use access_token from response
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/v1/users/me
```

## Rate Limiting
- Default: all API routes use a global limiter (configurable in `.env`).
- Login route has a stricter limit.
- Keying: authenticated requests are keyed by user id; others by client IP.
- Algorithm: token bucket
  1. Each key has capacity `limit` and refill rate `limit/window` tokens per second.
  2. On request, refill by elapsed time × rate.
  3. If at least 1 token, consume and proceed; otherwise return 429.

For multi-instance deployments, use a shared store like Redis. Replace `InMemoryStore` with a Redis-backed store that manages per-key `tokens` and `last_refill` atomically.

## Auth vs Authorization
- Auth: password-based login issues JWT access and refresh tokens.
- Authorization: role-based (`user`, `admin`). Example: `GET /api/v1/admin/secret` requires role `admin`.

## Configuration Management
- Centralized in `app/core/config.py` using `pydantic-settings`.
- Load from env vars and `.env` with sane defaults.
- Typed settings for token expiry, algorithm, DB URL, limiter defaults, environment.

## Scaling Playbook
- Stateless app behind an ASGI server, horizontal scale with a shared DB and Redis.
- Use connection pooling and tune workers (`--workers`), ensure idempotent handlers.
- Externalize sessions, rate limiters, and caches to Redis.
- Add observability: request logs, metrics, tracing.
- Introduce task queue for long work.
- Prefer pagination, projection, and indexing in DB.
- For SQLite, keep single-node dev only; migrate to Postgres/MySQL for production.
- Use migrations (Alembic) when moving beyond the skeleton.

## Algorithms Summary
- Rate limiting: token bucket as above.
- Auth: verify password → issue JWT with `sub` and `role` → protect endpoints via dependency that validates signature, expiry, and loads user.
- Refresh: persistent `refresh_token` with `jti` stored; on logout mark revoked; on refresh check unrevoked + expiry then mint new access token.
- Config precedence: env vars > `.env` > defaults.
