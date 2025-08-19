FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=base /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=base /usr/local/bin /usr/local/bin
COPY . /app

# Ensure sqlite dir exists and set default DB URL
RUN mkdir -p /app/data
ENV HOST=0.0.0.0 PORT=8000 DATABASE_URL=sqlite+aiosqlite:////app/data/app.db

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD curl -fsS http://localhost:${PORT}/api/v1/public/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
