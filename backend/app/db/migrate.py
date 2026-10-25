import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine
from app.db.session import Base

logger = logging.getLogger("bayora.migrate")

def run_db_migrations(engine: Engine):
    """
    Safely applies schema migrations for SQLite / PostgreSQL:
    1. Creates all tables defined in Base.metadata (users, tenants, tenant_memberships, etc.)
    2. Adds any missing columns to existing tables (backward compatibility for existing databases).
    """
    # Create any missing tables first
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Check SQLite or PostgreSQL dialect
        is_sqlite = "sqlite" in engine.url.drivername

        if is_sqlite:
            # 1. Check columns in experiments
            exp_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(experiments)")).fetchall()]
            if "tenant_id" not in exp_cols:
                logger.info("Migrating experiments: adding tenant_id")
                conn.execute(text("ALTER TABLE experiments ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'tenant-alpha'"))
            if "user_id" not in exp_cols:
                logger.info("Migrating experiments: adding user_id")
                conn.execute(text("ALTER TABLE experiments ADD COLUMN user_id VARCHAR(36)"))
            if "parent_experiment_id" not in exp_cols:
                logger.info("Migrating experiments: adding parent_experiment_id")
                conn.execute(text("ALTER TABLE experiments ADD COLUMN parent_experiment_id VARCHAR(36)"))

            # 2. Check columns in audit_events
            audit_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(audit_events)")).fetchall()]
            if "sequence_number" not in audit_cols:
                logger.info("Migrating audit_events: adding sequence_number")
                conn.execute(text("ALTER TABLE audit_events ADD COLUMN sequence_number INTEGER NOT NULL DEFAULT 1"))
            if "tenant_id" not in audit_cols:
                logger.info("Migrating audit_events: adding tenant_id")
                conn.execute(text("ALTER TABLE audit_events ADD COLUMN tenant_id VARCHAR(36) DEFAULT 'tenant-alpha'"))
            if "user_id" not in audit_cols:
                logger.info("Migrating audit_events: adding user_id")
                conn.execute(text("ALTER TABLE audit_events ADD COLUMN user_id VARCHAR(36)"))

            conn.commit()
