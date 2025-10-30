from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import generate_estimate

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
def ai_query(req: QueryRequest):
    try:
        result = generate_estimate(req.query)
        print("🔥 [ai_query RESULT]", result)
        return result
    except Exception as e:
        print("🔥 [ai_query ERROR]", e)
        return {"error": str(e)}