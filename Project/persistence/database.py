"""Database configuration and session helpers."""
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_URL = "sqlite:///" + str(BASE_DIR / "database" / "breakcheck.db").replace("\\", "/")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()
Session = SessionLocal
# Public compatibility name used by the service and workflow tests.
session_factory = SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from . import models
    (BASE_DIR / "database").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
        if "password_salt" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_salt VARCHAR(100)"))
        for table, additions in {
            "assessments": [("executive_request","TEXT"),("decided_by","VARCHAR(120)"),
                            ("decided_by_role","VARCHAR(80)"),("decided_at","DATETIME")],
            "agent_runs": [("thread_id","VARCHAR(120)")],
            "llm_calls": [("latency_milliseconds","INTEGER")],
        }.items():
            existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))]
            for name, kind in additions:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {kind}"))

def reset_db():
    Base.metadata.drop_all(bind=engine)
    init_db()

create_tables = init_db
get_session = get_db