FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY shared/python /shared
RUN pip install --no-cache-dir -e /shared
COPY services/scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/scheduler/app ./app
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
CMD ["celery", "-A", "app.celery_app", "beat", "--loglevel=info"]
