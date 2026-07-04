"""Agent package — auto-registers all agents on import."""
from app.agents.planner import PlannerAgent      # noqa: F401
from app.agents.finance import FinanceAgent       # noqa: F401
from app.agents.technical import TechnicalAgent   # noqa: F401
from app.agents.news import NewsAgent             # noqa: F401
from app.agents.risk import RiskAgent             # noqa: F401
from app.agents.judge import JudgeAgent           # noqa: F401
from app.agents.portfolio_agent import PortfolioAgent  # noqa: F401
from app.agents.report import ReportAgent         # noqa: F401
