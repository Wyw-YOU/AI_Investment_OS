import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db

# Import all agent modules to ensure they register in AGENT_REGISTRY
import app.agents.planner       # noqa: F401
import app.agents.finance       # noqa: F401
import app.agents.technical     # noqa: F401
import app.agents.news          # noqa: F401
import app.agents.risk          # noqa: F401
import app.agents.judge         # noqa: F401
import app.agents.portfolio_agent  # noqa: F401
import app.agents.report        # noqa: F401

from app.main import app as fastapi_app

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def db_session():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()
