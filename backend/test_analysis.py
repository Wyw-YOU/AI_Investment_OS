from app.engine.graph import run_analysis

# 使用模拟数据，不调用真实 API
result = run_analysis(
    stock_code='600519',
    market_data={
        'closes': [100 + i * 0.3 for i in range(60)],
        'klines': [{'close': 100 + i * 0.3, 'high': 101 + i * 0.3,
                    'low': 99 + i * 0.3} for i in range(60)],
    },
    financial_data={
        'pe_ratio': 35,
        'roe': 0.32,
        'debt_ratio': 0.45,
        'pb_ratio': 8.5,
        'revenue_growth': 0.15,
    },
    news_data=[
        {'title': '茅台Q3业绩超预期', 'content': '净利润增长20%'},
        {'title': '白酒板块整体走强', 'content': '行业景气度持续'},
    ],
)

print(f'Status: {result["status"]}')
print(f'Stock: {result["stock"]}')
print(f'Decision: {result["decision"]}')
print(f'Score: {result["report"].get("overall_score", "N/A")}')
print(f'Verdict: {result["report"].get("verdict", "N/A")}')
print(f'Agents used: {list(result["agent_outputs"].keys())}')
print(f'Confidences: {result["agent_confidence"]}')