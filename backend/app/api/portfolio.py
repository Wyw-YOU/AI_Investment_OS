from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_portfolios():
    return {"portfolios": []}


@router.post("/")
async def create_portfolio():
    return {"id": "new", "status": "created"}


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    return {"id": portfolio_id, "holdings": {}, "candidate_pool": []}
