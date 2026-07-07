"""
股票行情相关 API 路由。
所有接口均无需登录（无 get_current_user 依赖），公开访问。
数据来源：akshare（通过 market_data_service 等服务层调用）。
"""

from fastapi import APIRouter

from app.models.schemas import ApiResponse
from app.services.financial import financial_service
from app.services.market_data import market_data_service
from app.services.indicators import indicators_service
from app.services.news import news_service

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/stocks/hot")
async def hot_stocks():
    """获取成交额排名前 20 的热门股票列表。"""
    data = await market_data_service.get_hot_stocks()
    return ApiResponse(data=data)


@router.get("/stocks/{code}")
async def stock_detail(code: str):
    """获取单只股票的实时行情（价格、涨跌幅、成交量等）。"""
    data = await market_data_service.get_stock_realtime(code)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/history")
async def stock_history(code: str, days: int = 120):
    """获取单只股票最近 N 天的日 K 线数据（OHLCV）。"""
    data = await market_data_service.get_stock_history(code, days)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/indicators")
async def stock_indicators(code: str):
    """计算单只股票的技术指标（MA/RSI/MACD/BOLL/KDJ），基于最近 120 天数据。"""
    history = await market_data_service.get_stock_history(code, 120)
    data = indicators_service.calculate_all(history)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/financials")
async def stock_financials(code: str):
    """获取单只股票的财务摘要和估值数据（ROE/EPS/PE/PB 等）。"""
    data = await financial_service.get_financial_data(code)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/news")
async def stock_news(code: str):
    """获取单只股票的相关新闻（来源、标题、内容摘要）。"""
    data = await news_service.fetch_stock_news(code)
    return ApiResponse(data=data)


@router.get("/market/overview")
async def market_overview():
    """获取三大指数（上证/深证/创业板）的最新行情概览。"""
    data = await market_data_service.get_market_overview()
    return ApiResponse(data=data)
