import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./soc_assistant.db")

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_schema():
    """Apply lightweight additive migrations for SQLite demo databases.

    New nullable columns are added in place so an existing soc_assistant.db
    keeps working without a manual drop. Each entry is (table, column, DDL).
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    migrations = [
        ("users", "failed_login_attempts",
         "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"),
        ("users", "locked_until",
         "ALTER TABLE users ADD COLUMN locked_until DATETIME"),
        ("messages", "severity",
         "ALTER TABLE messages ADD COLUMN severity VARCHAR(20)"),
    ]

    statements: list[str] = []
    for table, column, ddl in migrations:
        if table not in tables:
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table)}
        if column not in existing_columns:
            statements.append(ddl)

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
