from app.services.market_data import MarketDataService

svc = MarketDataService()

# 测试实时行情
print('=== 实时行情测试 ===')
quote = svc.get_realtime_quote('600519')
if quote:
    print(f'股票: {quote.get("name")}')
    print(f'最新价: {quote.get("latest_price")}')
    print(f'涨跌幅: {quote.get("change_pct")}%')
    print('实时行情 OK!')
else:
    print('实时行情返回空（非交易时间或网络问题）')

# 测试 K 线数据
print()
print('=== K线数据测试 ===')
kline = svc.get_kline('600519', days=30)
if kline:
    print(f'获取到 {len(kline)} 条 K 线数据')
    print(f'最新一条: {kline[-1]}')
    print('K线数据 OK!')
else:
    print('K线数据返回空')

# 测试热门股票
print()
print('=== 热门股票测试 ===')
hot = svc.get_hot_stocks(5)
if hot:
    print(f'获取到 {len(hot)} 只热门股票')
    for s in hot[:3]:
        print(f'  {s["name"]} ({s["stock_code"]}) 涨跌幅: {s["change_pct"]}%')
    print('热门股票 OK!')
else:
    print('热门股票返回空')