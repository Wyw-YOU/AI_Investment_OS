from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    return {"user_id": "default", "username": "admin"}


@router.post("/login")
async def login():
    return {"token": "placeholder", "token_type": "bearer"}
