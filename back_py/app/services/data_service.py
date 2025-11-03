import os
import chromadb
import mysql.connector
import pandas as pd
from datetime import datetime
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Chroma 초기화
client = chromadb.PersistentClient(path="/app/chroma")
collection = client.get_or_create_collection(name="products")


# ✅ MySQL 연결
def get_connection():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="1234",
        database="project",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )

def get_openai_embedding(text: str):
    """OpenAI 임베딩 (저장 때와 동일한 모델 사용)"""
    res = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding

# ✅ Chroma에서 제품 검색
def get_chroma_products(query_text: str, n_results: int = 20):
    try:
        query_embedding = get_openai_embedding(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas"]
        )

        metadatas = results.get("metadatas", [])
        flattened = []
        for entry in metadatas:
            if isinstance(entry, list):
                flattened.extend(entry)
            elif isinstance(entry, dict):
                flattened.append(entry)

        print(f"🧠 [Chroma] 검색 성공: '{query_text}' → {len(flattened)}개")
        return flattened
    except Exception as e:
        print(f"❌ [Chroma] 검색 실패: {e}")
        return []

# ✅ MySQL 제품 샘플 (백업용)
def get_mysql_products(cat: str, limit: int = 10):
    conn = get_connection()
    df = pd.read_sql(
        f"""
        SELECT name, category, price, link
        FROM product
        WHERE category = '{cat}'
          AND price IS NOT NULL
          AND price > 0
        ORDER BY price ASC
        LIMIT {limit}
        """,
        conn
    )
    conn.close()
    return df.to_dict(orient="records")


# ✅ 예산/용도 기반 제품 추천
def get_hint_products(budget=None, purpose=None):
    categories = ["CPU", "VGA", "RAM", "SSD", "MBoard_intel","MBoard_amd", "Cooler_Liquid", "Cooler_Air", "Power", "Case"]
    all_items = []

    for cat in categories:
        items = []

        # 1️⃣ Chroma 우선 검색 (OpenAI 임베딩 사용)
        query_text = f"{cat} 관련 제품 {purpose or ''}".strip()
        chroma_items = get_chroma_products(query_text, n_results=10)
        items.extend(chroma_items)

        # 2️⃣ 백업: Chroma가 부족할 때 MySQL 보완
        if len(items) < 5:
            mysql_items = get_mysql_products(cat, limit=10)
            items.extend(mysql_items)
            print(f"⚠️ [Fallback] {cat} → MySQL {len(mysql_items)}개 사용")

        # 3️⃣ 예산 필터 (너무 강하지 않게)
        if budget:
            items = [p for p in items if p.get("price") and p["price"] <= budget * 0.95]

        # ✅ 중복 제거 + 상위 8개
        seen = set()
        unique = []
        for p in items:
            key = (p.get("name"), p.get("category"))
            if key not in seen:
                seen.add(key)
                unique.append(p)
        all_items.extend(unique[:8])

    print(f"💡 [DataService] 반환 제품 수: {len(all_items)}")
    print(f"🧩 [DataService] hint_products 카테고리 분포:",
          [p["category"] for p in all_items])
    for p in all_items:
        if p["category"] in ["Cooler_Liquid", "Cooler_Air"]:
            p["category"] = "Cooler"
        elif p["category"] in ["MBoard_intel", "MBoard_amd"]:
            p["category"] = "MBoard"

    return all_items