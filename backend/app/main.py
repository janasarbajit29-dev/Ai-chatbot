from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health

app = FastAPI(title="AURA Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")

from app.api.routes import auth, conversations, messages, chat, files
app.include_router(auth.router, prefix="/api")
app.include_router(conversations.router, prefix="/api/conversations")
app.include_router(messages.router, prefix="/api/conversations/{conversation_id}/messages")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(files.router, prefix="/api/files")
@app.get("/")
async def root():
    return {"message": "AURA Backend is running"}
