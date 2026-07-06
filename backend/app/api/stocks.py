from fastapi import APIRouter

from app.models.schemas import ApiResponse
from app.services.financial import financial_service
from app.services.market_data import market_data_service
from app.services.indicators import indicators_service
from app.services.news import news_service

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/stocks/hot")
async def hot_stocks():
    data = await market_data_service.get_hot_stocks()
    return ApiResponse(data=data)


@router.get("/stocks/{code}")
async def stock_detail(code: str):
    data = await market_data_service.get_stock_realtime(code)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/history")
async def stock_history(code: str, days: int = 120):
    data = await market_data_service.get_stock_history(code, days)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/indicators")
async def stock_indicators(code: str):
    history = await market_data_service.get_stock_history(code, 120)
    data = indicators_service.calculate_all(history)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/financials")
async def stock_financials(code: str):
    data = await financial_service.get_financial_data(code)
    return ApiResponse(data=data)


@router.get("/stocks/{code}/news")
async def stock_news(code: str):
    data = await news_service.fetch_stock_news(code)
    return ApiResponse(data=data)


@router.get("/market/overview")
async def market_overview():
    data = await market_data_service.get_market_overview()
    return ApiResponse(data=data)
