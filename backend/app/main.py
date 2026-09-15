from fastapi import FastAPI
from app.api.routes import health

app = FastAPI(title="AURA Backend", version="1.0.0")

app.include_router(health.router, prefix="/api")

from app.api.routes import auth
app.include_router(auth.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AURA Backend is running"}
