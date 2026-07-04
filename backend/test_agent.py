# from app.agents.base import list_agents, get_agent

# agents = list_agents()
# print(f'已注册 Agent ({len(agents)}): {agents}')

# for name in agents:
#     agent = get_agent(name)
#     print(f'  {name}: {agent.__class__.__name__}')


# from app.agents.state import InvestmentState
# from app.agents.finance import FinanceAgent
# from app.agents.technical import TechnicalAgent
# from app.agents.risk import RiskAgent
# import random

# # ---------- Finance Agent ----------
# state = InvestmentState(
#     current_stock='600519',
#     financial_data={'pe_ratio': 35, 'roe': 0.32, 'debt_ratio': 0.45, 'pb_ratio': 8.5},
# )
# result = FinanceAgent().run(state)
# print(f'Finance: verdict={result["output"]["verdict"]}, confidence={result["confidence"]}')
# print(f'  evidence: {result["evidence"]}')

# # ---------- Technical Agent ----------
# state = InvestmentState(
#     current_stock='600519',
#     market_data={'closes': [100 + i * 0.5 for i in range(50)]},
# )
# result = TechnicalAgent().run(state)
# print(f'Technical: trend={result["output"]["trend"]}, verdict={result["output"]["verdict"]}')
# print(f'  confidence={result["confidence"]}')

# # ---------- Risk Agent ----------
# random.seed(42)
# state = InvestmentState(
#     current_stock='600519',
#     market_data={'closes': [100 + random.uniform(-2, 2) for _ in range(60)]},
# )
# result = RiskAgent().run(state)
# print(f'Risk: level={result["output"]["risk_level"]}, verdict={result["output"]["verdict"]}')
# print(f'  volatility={result["output"]["volatility_30d"]}')

from app.agents.state import InvestmentState
from app.agents.judge import JudgeAgent

state = InvestmentState(current_stock='600519')
state.set_agent_output('finance', {
    'output': {'verdict': 'undervalued'},
    'confidence': 0.8,
    'evidence': ['e'],
    'reasoning': 'r' * 20,
})
state.set_agent_output('technical', {
    'output': {'verdict': 'buy'},
    'confidence': 0.7,
    'evidence': ['e'],
    'reasoning': 'r' * 20,
})
state.set_agent_output('news', {
    'output': {'verdict': 'positive'},
    'confidence': 0.6,
    'evidence': ['e'],
    'reasoning': 'r' * 20,
})
state.set_agent_output('risk', {
    'output': {'risk_level': 'LOW'},
    'confidence': 0.7,
    'evidence': ['e'],
    'reasoning': 'r' * 20,
})

result = JudgeAgent().run(state)
out = result['output']
print(f'Score: {out["overall_score"]}/100')
print(f'Verdict: {out["verdict"]}')
print(f'Key points: {out["key_points"]}')
print(f'Warnings: {out["warnings"]}')