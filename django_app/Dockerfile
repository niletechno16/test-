FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for pymssql
RUN apt-get update && apt-get install -y \
    freetds-dev \
    freetds-bin \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8080

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8080"]
