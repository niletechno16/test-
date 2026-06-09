import uvicorn
import sys
import io
import os
from fastapi import FastAPI
from fastapi_app.routes.webhook import router
from fastapi_app.database.init_db import init_db

os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)