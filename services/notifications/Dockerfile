FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM base AS builder
COPY shared/python /shared
RUN pip install --no-cache-dir -e /shared
COPY services/notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY shared/python /shared
RUN pip install --no-cache-dir -e /shared
COPY services/notifications/app ./app
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
EXPOSE 8007
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
