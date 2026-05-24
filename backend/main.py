import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from auth.router import router as auth_router
from api.chat import router as chat_router
from api.conversations import router as conversations_router
from api.admin import router as admin_router
from api.reference import router as reference_router
from database.connection import engine, SessionLocal, ensure_runtime_schema
from database.models import Base, User
from auth.service import AuthService

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("soc")


def _seed_demo_users() -> None:
    if os.getenv("SEED_DEMO_USERS", "true").lower() not in {"1", "true", "yes"}:
        return

    demo_users = [
        ("analyst@socdemo.com", "Analyst123!", "Demo Analyst", "analyst"),
        ("admin@socdemo.com", "Admin123!", "Demo Admin", "admin"),
    ]
    db = SessionLocal()
    try:
        for email, password, name, role in demo_users:
            if AuthService.get_user_by_email(db, email):
                continue
            user = User(
                email=email,
                hashed_password=AuthService.hash_password(password),
                full_name=name,
                role=role,
            )
            db.add(user)
            logger.info("Seeded demo user: %s (%s)", email, role)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    _seed_demo_users()
    yield


app = FastAPI(
    title="AI SOC Assistant",
    description="AI-powered Security Operations Center Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

_origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(reference_router, prefix="/api/reference", tags=["Reference"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-soc-assistant",
        "llm_configured": bool(os.getenv("GROQ_API_KEY")),
    }
