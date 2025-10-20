from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 import
from app.routers import ai_router, data_router

# -----------------------------------------------------
# FastAPI 앱 생성
# -----------------------------------------------------
app = FastAPI(
    title="AI 견적 백엔드",
    description="GPT와 크롤링 데이터를 활용한 맞춤형 PC 견적 API",
    version="1.0.0"
)

# -----------------------------------------------------
# CORS 설정 (React, Spring 등 외부 접근 허용)
# -----------------------------------------------------
origins = [
    "http://localhost:3000",  # React 프론트엔드
    "http://localhost:8080",  # Spring 백엔드
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 허용할 Origin
    allow_credentials=True,
    allow_methods=["*"],        # 모든 HTTP 메서드 허용
    allow_headers=["*"],        # 모든 헤더 허용
)

# -----------------------------------------------------
# 라우터 등록
# -----------------------------------------------------
app.include_router(ai_router.router, prefix="/ai", tags=["AI 견적"])
app.include_router(data_router.router, prefix="/data", tags=["데이터 관리"])

# -----------------------------------------------------
# 루트 경로
# -----------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI 견적 백엔드 서버 정상 작동 중 🚀"}


# -----------------------------------------------------
# 개발용 실행 명령어 (도커 외 단독 실행 시)
# -----------------------------------------------------
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
