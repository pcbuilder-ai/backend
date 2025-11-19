from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.ai_service import process_chat_request
import traceback
import sys

router = APIRouter()

class ChatRequest(BaseModel):
    message: str


@router.post("/query")
async def ai_query(req: ChatRequest, request: Request):
    try:
        session_id = request.headers.get("session-id")
        if not session_id:
            return {"success": False, "message": "세션 ID가 누락되었습니다."}

        result = await process_chat_request(session_id, req.message)
        return result

    except Exception as e:
        traceback.print_exc()
        sys.stdout.flush()
        return {"success": False, "error": str(e)}
