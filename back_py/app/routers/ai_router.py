from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict
from app.services.ai_service import generate_estimate
import traceback
import sys
import json

router = APIRouter()


# -------------------------------------
# 🧾 요청 모델 정의 (Spring → FastAPI)
# -------------------------------------
class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}, ...]


# -------------------------------------
# 🚀 견적 생성 엔드포인트
# -------------------------------------
@router.post("/query")
def ai_query(req: ChatRequest):
    try:
        # 💬 마지막 user 메시지 내용만 추출
        user_message = ""
        for msg in reversed(req.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return {"success": False, "message": "user 메시지가 비어 있습니다."}

        # 🧠 견적 생성 로직 실행
        result = generate_estimate(user_message)

        print("🔥 [ai_query INPUT]", user_message)
        print("🔥 [ai_query RESULT]", json.dumps(result, ensure_ascii=False, indent=2))
        sys.stdout.flush()

        return result

    except Exception as e:
        traceback.print_exc()
        sys.stdout.flush()
        print("🔥 [ai_query ERROR]", e)
        return {"success": False, "error": str(e)}
