from fastapi import APIRouter, BackgroundTasks

router = APIRouter()


@router.get("/hot")
async def get_hot_stocks():
    return {"stocks": []}


@router.post("/analyze")
async def analyze_stock(stock_code: str, background_tasks: BackgroundTasks):
    from app.engine.graph import run_analysis
    background_tasks.add_task(run_analysis, stock_code)
    return {"stock_code": stock_code, "status": "submitted"}


@router.get("/analyze/sync/{stock_code}")
async def analyze_stock_sync(stock_code: str):
    from app.engine.graph import run_analysis
    result = run_analysis(stock_code)
    return result


@router.get("/{stock_code}")
async def get_stock(stock_code: str):
    return {"stock_code": stock_code, "status": "not_analyzed"}
