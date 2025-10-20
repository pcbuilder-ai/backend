from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def data_test():
    return {"message": "Data router 정상 작동"}
