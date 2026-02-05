import os

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure required settings exist before importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-must-be-at-least-32-chars-long")
os.environ.setdefault("UPLOAD_DIR", "uploads")
os.environ.setdefault("ADMIN_TOKEN", "test-token")
os.environ.setdefault("ADMIN_USERNAME", "admin")

# Ensure auth/login is deterministic in tests (override .env if present)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
os.environ.setdefault("ADMIN_PASSWORD_HASH", pwd_context.hash("admin123456"))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.floor import Floor  # noqa: F401,E402
from app.models.waypoint import Waypoint  # noqa: F401,E402
from app.models.connection import Connection  # noqa: F401,E402
from app.models.room import Room  # noqa: F401,E402
from app.models.kiosk import Kiosk  # noqa: F401,E402
from app.core.login_security import login_security  # noqa: E402


TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    # Reset in-memory security state between tests
    login_security.reset()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    login_security.reset()


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {os.environ['ADMIN_TOKEN']}"}
