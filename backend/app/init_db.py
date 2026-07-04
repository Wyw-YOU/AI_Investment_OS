"""Initialize database tables."""
from app.database import engine, Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.stock import StockState
from app.models.event import MarketEvent, Alert
from app.models.agent_log import AgentLog


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()
