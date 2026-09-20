from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health

app = FastAPI(title="AURA Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")

from app.api.routes import auth
app.include_router(auth.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AURA Backend is running"}
