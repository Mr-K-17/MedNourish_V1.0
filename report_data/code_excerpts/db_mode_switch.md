# Code Excerpt: `db_mode_switch`

- **Repository Path**: [`backend/app/db/session.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/db/session.py#L17-L46)
- **Lines**: 17–46 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Dynamically configures SQLAlchemy engine connections between SQLite (in-memory/file for rapid local testing) and MySQL (production localhost) based on environment configuration without code changes.

```python
# Database Engine and Session Factory
try:
    if settings.DB_MODE == "mysql":
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 3},
        )
    else:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning("Database engine initialization warning: %s", str(e))
    engine = None
    SessionLocal = None


def get_db():
    """Dependency that provides a database session."""
    if SessionLocal is None:
        raise RuntimeError("Database session factory is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
