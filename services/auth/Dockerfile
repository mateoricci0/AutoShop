FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# ── builder: install all dependencies ────────────────────────────────────────
FROM base AS builder

# Install shared package first (editable install resolves imports at container
# build time; a second install in the runtime stage keeps the image consistent)
COPY shared/python /shared
RUN pip install --no-cache-dir -e /shared

COPY services/auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── runtime: lean production image ───────────────────────────────────────────
FROM base AS runtime
WORKDIR /app

# Copy installed packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Re-install shared package so the editable link (.pth file) is present
COPY shared/python /shared
RUN pip install --no-cache-dir -e /shared

# Copy application source
COPY services/auth/app ./app

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
