FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=5

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt gunicorn==26.2.0

COPY . .

RUN mkdir -p /app/outputs /app/data
EXPOSE 8090
CMD ["gunicorn", "--bind=0.0.0.0:8090", "--workers=1", "--threads=16", "--worker-class=gthread", "api.main:app"]
