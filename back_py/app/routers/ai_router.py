from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import generate_estimate
import sys
import traceback
import json

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
def ai_query(req: QueryRequest):
    try:
        result = generate_estimate(req.query)
        print("🔥 [ai_query RESULT]", json.dumps(result, ensure_ascii=False, indent=2))
        sys.stdout.flush()
        print("🔥 [ai_query RESULT]", result)
        return result
    except Exception as e:
        traceback.print_exc()
        sys.stdout.flush()
        print("🔥 [ai_query ERROR]", e)
        return {"error": str(e)}