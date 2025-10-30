from fastapi import APIRouter
from app.services.data_service import get_connection

router = APIRouter()

@router.get("/list")
def list_data(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM product LIMIT %s", (limit,))
    result = cursor.fetchall()
    conn.close()
    return result
