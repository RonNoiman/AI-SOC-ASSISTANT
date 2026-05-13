from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from auth.router import router as auth_router
from api.chat import router as chat_router
from api.conversations import router as conversations_router
from api.admin import router as admin_router
from database.connection import engine, ensure_runtime_schema
from database.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    yield

app = FastAPI(
    title="AI SOC Assistant",
    description="AI-powered Security Operations Center Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-soc-assistant"}
