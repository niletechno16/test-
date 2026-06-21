FROM python:3.12-slim

WORKDIR /app

# pymssql لازم freetds
RUN apt-get update && apt-get install -y \
    freetds-dev \
    freetds-bin \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./fastapi_app/requirements.txt
RUN pip install --no-cache-dir -r fastapi_app/requirements.txt

COPY . ./fastapi_app/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "fastapi_app.Main:app", "--host", "0.0.0.0", "--port", "8000"]
