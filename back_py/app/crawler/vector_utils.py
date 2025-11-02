import os
import chromadb
from openai import OpenAI

# ✅ Chroma 초기화 (로컬 폴더에 저장됨)
client = chromadb.PersistentClient(path="/app/chroma")  # 경로는 자유롭게 변경 가능
collection = client.get_or_create_collection(name="products")

# ✅ OpenAI 클라이언트 (환경변수 OPENAI_API_KEY 사용)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_embeddings(texts: list[str]):
    """여러 문장을 한 번에 임베딩"""
    response = openai_client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    return [item.embedding for item in response.data]

def save_to_vector_db(products):
    """여러 제품을 한 번에 임베딩 + 저장"""
    if not products:
        return
    print(f"💡 입력 제품 수: {len(products)}")
    unique = {p["id"]: p for p in products}
    print(f"💡 중복 제거 후 남은 수: {len(unique)}")
    products = list(unique.values())

    texts = [f"{p['category']} 제품 {p['name']}의 주요 스펙은 {p['spec']}입니다." for p in products]
    ids = [p["id"] for p in products]
    metadatas = [
        {
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "link": p["link"],
        }
        for p in products
    ]

    try:
        # ✅ 1회 요청으로 모든 텍스트 임베딩 생성
        embeddings = get_openai_embeddings(texts)

        # ✅ 한 번에 Chroma에 추가
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
        print(f"🧠 [Chroma] {len(products)}개 제품 일괄 임베딩 완료")
    except Exception as e:
        print(f"❌ [Chroma] 일괄 임베딩 실패: {e}")
