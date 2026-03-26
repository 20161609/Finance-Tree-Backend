# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.init import database, engine, Base
from app.route import auth, db
from app.db import model
from app.route import test
from app.firebase.init import initialize_firebase
import os
from dotenv import load_dotenv
from app.lib.ai_receipt import _get_ocr_engine

# Load environment variables
load_dotenv()

FRONT_URL = os.getenv("FRONT_URL")
BACK_URL = os.getenv("BACK_URL")
VERSION = os.getenv("VERSION")
ENV = os.getenv("ENV", "dev")  # dev / prod

# Create FastAPI instance
app = FastAPI()

# CORS configuration
ALLOWED_ORIGINS = [FRONT_URL if FRONT_URL else "https://finance-tree.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # No cookie-based auth
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Initialize Firebase
initialize_firebase()

# Connect to the database on startup
@app.on_event("startup")
async def startup():
    print("Connecting to the database")
    Base.metadata.create_all(bind=engine)
    await database.connect()
    _get_ocr_engine()

# Disconnect from the database on shutdown
@app.on_event("shutdown")
async def shutdown():
    print("Disconnecting from the database")
    await database.disconnect()

# Register routes
app.include_router(db.router, prefix="/db")
app.include_router(auth.router, prefix="/auth")
app.include_router(test.router, prefix="/test")

@app.get("/")
async def root():
    return {
        "message": "Finance Tree API is running",
        "version": VERSION
    }