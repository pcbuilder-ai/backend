# app/routers/ai_router.py
from fastapi import APIRouter
from app.services.ai_service import generate_estimate

router = APIRouter()

@router.post("/query")
def ai_query(data: dict):
    text = data.get("query", "")
    result = generate_estimate(text)
    return {"result": result}
