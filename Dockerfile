FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/mediafiles /app/static \
    && chown -R 1000:1000 /app

COPY . .
RUN chown -R 1000:1000 /app

USER 1000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
