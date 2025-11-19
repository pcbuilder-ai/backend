import os
import chromadb
import mysql.connector
import pandas as pd
from datetime import datetime
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Chroma 초기화 (Lazy Loading 적용 - 서버 재시작 없이 연결 갱신)
_chroma_client = None
_chroma_collection = None

def get_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        try:
            _chroma_client = chromadb.PersistentClient(path="/app/chroma")
            _chroma_collection = _chroma_client.get_or_create_collection(name="products")
        except Exception as e:
            print(f"❌ ChromaDB 연결 실패: {e}")
            return None
    return _chroma_collection

# ✅ 부품별 예산 비중 (GPU에 집중)
BUDGET_RATIOS = {
    "cpu": (0.15, 0.25),
    "gpu": (0.35, 0.55), 
    "mboard": (0.05, 0.12),
    "ram": (0.15, 0.25),  
    "ssd": (0.05, 0.10),
    "cooler": (0.02, 0.05),
    "power": (0.05, 0.10),
    "case": (0.03, 0.05),
}

# 🚨 [필수] 가짜 데이터 거르기 (이 단어 있으면 무조건 탈락)
NEGATIVE_KEYWORDS = {
    "gpu": ["FAN", "팬", "COOLER", "쿨러", "케이스", "CASE", "지지대", "CABLE"],
    "cpu": ["COOLER", "쿨러", "FAN", "팬"],
    "ssd": ["CASE", "케이스", "ENCLOSURE", "방열판"],
    "ram": ["방열판", "HEATSINK"],
}

def get_connection():
    return mysql.connector.connect(
        host="db", user="root", password="1234", database="project", charset="utf8mb4", collation="utf8mb4_unicode_ci"
    )

def get_openai_embedding(text: str):
    res = openai_client.embeddings.create(model="text-embedding-3-small", input=text)
    return res.data[0].embedding

# ✅ Chroma 검색
def get_chroma_products(query_text: str, category_filter: str = None, min_price: int = 0, max_price: int = 99999999, keyword_filter: str = None, n_results: int = 10):
    try:
        collection = get_collection()
        if collection is None: return []

        query_embedding = get_openai_embedding(query_text)
        
        where_clauses = []
        if category_filter: where_clauses.append({"category": {"$eq": category_filter}})
        where_clauses.append({"price": {"$gte": min_price}})
        where_clauses.append({"price": {"$lte": max_price}})
        final_where = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]

        # 넉넉하게 3배수 가져와서 필터링
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 3,
            include=["metadatas"],
            where=final_where
        )

        flattened = []
        for entry in results.get("metadatas", []):
            if isinstance(entry, list): flattened.extend(entry)
            elif isinstance(entry, dict): flattened.append(entry)

        filtered = []
        
        # 🕵️ 네거티브 & 포지티브 필터링 적용
        negatives = NEGATIVE_KEYWORDS.get(category_filter, [])
        target_kw = keyword_filter.upper() if keyword_filter else None

        for item in flattened:
            name_upper = item["name"].upper()
            
            # 1. 네거티브 체크 (가짜 부품 제거)
            if any(neg in name_upper for neg in negatives): continue

            # 2. 키워드 체크
            if category_filter == "mboard":
                if target_kw == "DDR5":
                    if "DDR4" in name_upper or " D4" in name_upper: continue
                    if "B660" in name_upper and "DDR5" not in name_upper: continue
                elif target_kw == "DDR4":
                    if "DDR4" not in name_upper and " D4" not in name_upper: continue
            
            elif category_filter == "ram" and target_kw and target_kw not in name_upper: continue
            
            # SSD NVMe 강제
            elif category_filter == "ssd" and target_kw == "NVME":
                if "NVME" not in name_upper: continue

            filtered.append(item)
        
        # 로그 출력
        log_msg = f"🧠 [Chroma] '{category_filter}' 검색: {len(filtered)}개 (가격: {min_price}~{max_price})"
        print(log_msg)
        
        return filtered[:n_results]

    except Exception as e:
        print(f"❌ [Chroma] 검색 실패: {e}")
        return []

# ✅ MySQL 백업 검색
def get_mysql_products(cat: str, limit: int = 10):
    conn = get_connection()
    df = pd.read_sql(f"SELECT name, category, price, link, spec FROM product WHERE category = '{cat}' AND price > 0 ORDER BY price ASC LIMIT {limit}", conn)
    conn.close()
    return df.to_dict(orient="records")


# ✅ 최종 함수 (개선된 배율 조절 방식)
def get_hint_products(budget=None, purpose=None):
    total_budget = budget if budget else 1500000
    
    target_memory_type = "DDR5" if total_budget >= 1300000 else "DDR4"
    ssd_type = "NVME" if total_budget >= 900000 else None

    print(f"🎯 [Strategy] 예산 {total_budget}원 -> {target_memory_type} / {ssd_type or 'SATA'}")

    categories = {
        "cpu": ["CPU"], "gpu": ["VGA"], "ram": ["RAM"], "ssd": ["SSD"],
        "mboard": ["MBoard_intel", "MBoard_amd"], "cooler": ["Cooler_Air", "Cooler_Liquid"],
        "power": ["Power"], "case": ["Case"],
    }

    result = {key: [] for key in categories.keys()}

    for key, cat_list in categories.items():
        items = []

        ratio_min, ratio_max = BUDGET_RATIOS.get(key, (0, 1.0))
        
        # 🚨 [수정 1] 배율 조정: 상한선을 타이트하게 (1.5배 -> 1.1배)
        # 이렇게 하면 아무리 비싼걸 골라도 예산 범위를 크게 벗어나지 않음
        if total_budget >= 1500000:
             min_p = int(total_budget * ratio_min)
             max_p = int(total_budget * ratio_max * 1.1) # 1.1배로 축소
        else:
             min_p = int(total_budget * ratio_min * 0.8)
             max_p = int(total_budget * ratio_max * 1.2)

        # 🚨 [핵심 수정] RAM/SSD 상한선 현실화
        if key == "ram":
            min_p = int(total_budget * 0.10)  # 최소 10% (20만원)
            max_p = int(total_budget * 0.30)  # 최대 30% (60만원)까지 허용
            # 이렇게 해야 40만원짜리 시금치 램이 검색 범위에 들어옴
        
        elif key == "ssd":
            min_p = int(total_budget * 0.02)
            max_p = int(total_budget * 0.15)

        if key == "gpu" and total_budget > 3500000:
            max_p = 10000000

        keyword_filter = None
        if key in ["ram", "mboard"]: keyword_filter = target_memory_type
        if key == "ssd": keyword_filter = ssd_type

        for cat in cat_list:
            query_text = f"{cat} {purpose or ''} 고성능".strip()
            
            chroma_items = get_chroma_products(query_text, cat, min_p, max_p, keyword_filter, 8)
            
            # 구명조끼 (결과 없으면 하한선 낮춤 - 상한선은 유지!)
            if not chroma_items and keyword_filter:
                print(f"⚠️ [Retry] {cat} 하한선 해제")
                chroma_items = get_chroma_products(query_text, cat, 0, max_p, keyword_filter, 5)
            
            items.extend(chroma_items)

            # MySQL 백업 (네거티브 필터 적용)
            if len(items) < 3:
                mysql_items = get_mysql_products(cat, limit=20)
                negatives = NEGATIVE_KEYWORDS.get(key, [])
                
                for m in mysql_items:
                    name_up = m["name"].upper()
                    if any(neg in name_up for neg in negatives): continue # 가짜 거르기
                    if keyword_filter and keyword_filter not in m.get("spec", ""): continue
                    
                    # 너무 싼 거 제외 (가짜 방지 2차)
                    if key == "gpu" and m["price"] < total_budget * 0.1: continue 

                    items.append(m)

        # 중복 제거
        seen = set()
        unique = []
        for p in items:
            key2 = (p.get("name"), p.get("category"))
            if key2 not in seen and p.get("price", 0) > 0:
                seen.add(key2)
                unique.append(p)

        # 🚨 [수정 3] 정렬 전략 차별화
        # - 성능 핵심(CPU/GPU) : 비싼 순 (그래야 좋은게 들어감)
        # - 나머지(RAM/SSD/Case) : 싼 순 (그래야 예산 세이브)
        if key in ["cpu", "gpu"]:
            unique.sort(key=lambda x: x["price"], reverse=True) # 내림차순
        else:
            unique.sort(key=lambda x: x["price"], reverse=False) # 오름차순 (가성비 우선)

        result[key] = unique[:8]

    print("📌 [DataService] 최종 hint_products 생성 완료")
    for k, v in result.items():
        print(f"   - {k}: {len(v)}개")

    return result