import uvicorn
import sys
import io
import os
import asyncio
import httpx
from fastapi import FastAPI
from fastapi_app.routes.webhook import router
from fastapi_app.database.init_db import init_db

os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

APP_URL = os.getenv("APP_URL")  # مثال: https://your-app.onrender.com

app = FastAPI()


async def keep_alive():
    await asyncio.sleep(30)  # استنى شوية الأول عشان الـ server يقوم
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{APP_URL}/health", timeout=10)
            print("✅ Keep-alive ping sent")
        except Exception as e:
            print(f"⚠️ Keep-alive failed: {str(e)}")
        await asyncio.sleep(840)  # كل 14 دقيقة (Render بيوقف بعد 15)


@app.on_event("startup")
async def startup_event():
    init_db()
    if APP_URL:
        asyncio.create_task(keep_alive())
    else:
        print("⚠️ APP_URL not set — keep-alive disabled")


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
