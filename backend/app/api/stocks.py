from fastapi import APIRouter

router = APIRouter()


@router.get("/hot")
async def get_hot_stocks():
    return {"stocks": []}


@router.post("/analyze")
async def analyze_stock(stock_code: str):
    return {"stock_code": stock_code, "status": "pending"}


@router.get("/{stock_code}")
async def get_stock(stock_code: str):
    return {"stock_code": stock_code, "status": "not_analyzed"}
