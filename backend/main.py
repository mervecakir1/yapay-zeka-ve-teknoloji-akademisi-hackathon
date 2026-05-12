import os
from pathlib import Path
from dotenv import load_dotenv

# .env'i app modüllerinden önce yükle — explicit path (cwd ne olursa olsun çalışsın)
# backend/main.py'dan iki seviye yukarı = proje kök → .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models import Base
from .database import engine
from .routers.auth import router as auth_router
from .routers.products import router as products_router
from .routers.orders import router as orders_router
from .routers.inventory import router as inventory_router
from .routers.chat import router as chat_router
from .routers.dashboard import router as dashboard_router
from .routers.suppliers import router as suppliers_router

app = FastAPI(title="SMB E-Commerce AI Assistant - Backend API")

# CORS — gerekirse (tek port kullanırsak teknik olarak gereksiz, ama bırakıyoruz)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy"}


# JSON API router'ları — bunlar mount'tan ÖNCE register oluyor, öncelikleri yüksek
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(suppliers_router)

# Frontend static mount — en sona koyuyoruz ki API route'ları öncelikli olsun.
# html=True → "/" istendiğinde otomatik index.html serve eder.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

Base.metadata.create_all(bind=engine)
