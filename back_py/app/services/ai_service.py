import os
import json
import re
import sys
from openai import OpenAI
from app.services.session_service import get_messages, append_message
from app.services.data_service import get_hint_products, get_connection

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------
# 🔍 예산 / 용도 파싱 (기존 그대로 사용)
# -------------------------------------
def parse_query(query: str):
    import re
    budget, purpose, cooler_type, board_type = None, None, None, None

    match = re.search(r"(\d+)\s*만원", query)
    if match:
        budget = int(match.group(1)) * 10000

    for keyword in ["사무", "게임", "롤", "영상", "편집", "디자인", "작업"]:
        if keyword in query:
            purpose = keyword
            break

    if "수랭" in query:
        cooler_type = "Cooler_Liquid"
    elif "공랭" in query:
        cooler_type = "Cooler_Air"

    if "인텔" in query:
        board_type = "MBoard_intel"
    elif "amd" in query.lower():
        board_type = "MBoard_amd"

    return budget, purpose, cooler_type, board_type


# -------------------------------------
# 🧠 Chroma 기반 제품 목록 생성
# -------------------------------------
def build_prompt(query: str):
    budget, purpose, cooler_type, board_type = parse_query(query)
    hint_products = get_hint_products(budget, purpose)
    grouped_json = json.dumps(hint_products, ensure_ascii=False, indent=2)

    prompt = f"""
    사용자의 요청: "{query}"
    분석 결과:
    - 예산: {budget if budget else "명시 안됨"}
    - 용도: {purpose if purpose else "명시 안됨"}
    - 쿨러 타입: {cooler_type or "자동 선택"}
    - 메인보드 타입: {board_type or "자동 선택"}

    아래는 사용할 수 있는 제품 목록이다.
    반드시 아래 JSON 목록 안에 존재하는 name, price, link만 사용해야 한다.

    제품 목록(JSON):
    {grouped_json}

    견적 구성 규칙 (호환성 필수 준수):
    1. [중요] CPU와 메인보드는 동일 브랜드여야 함 (인텔-인텔, AMD-AMD).
    2. [중요] 소켓 규격이 일치해야 함 (LGA1700 ↔ B660/B760/Z790 등).
    3. [중요] 램은 메인보드가 지원하는 규격(DDR4/DDR5)과 일치해야 함.
    4. 예산 분배: GPU에 가장 많은 투자를 하고, 나머지는 밸런스를 맞춰라.
    5. 이전 견적(JSON)이 제공된다면, 그것을 기반으로 수정하라.
    -cpu는 hint_products["cpu"]에서만 선택하라  
    -gpu는 hint_products["gpu"]에서만 선택하라  
    -mboard는 hint_products["mboard"]에서만 선택하라  
    -ram는 hint_products["ram"]에서만 선택하라  
    -ssd는 hint_products["ssd"]에서만 선택하라  
    -cooler는 hint_products["cooler"]에서만 선택하라  
    -power는 hint_products["power"]에서만 선택하라  
    -case는 hint_products["case"]에서만 선택하라


    출력 형식(JSON):
    {{
      "cpu": {{ "name": "", "price": 0, "link": "" }},
      "gpu": {{ "name": "", "price": 0, "link": "" }},
      "mboard": {{ "name": "", "price": 0, "link": "" }},
      "ram": {{ "name": "", "price": 0, "link": "" }},
      "ssd": {{ "name": "", "price": 0, "link": "" }},
      "cooler": {{ "name": "", "price": 0, "link": "" }},
      "power": {{ "name": "", "price": 0, "link": "" }},
      "case": {{ "name": "", "price": 0, "link": "" }},
      "total_price": 0
    }}
    """
    return prompt


# -------------------------------------
# 🧩 DB 가격/링크 보정
# -------------------------------------
def enrich_with_db_info(result_json):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    final_result, total_price = {}, 0

    for key, item in result_json.items():
        if key == "total_price":
            continue

        name = item.get("name")
        if not name:
            continue

        cursor.execute(
            "SELECT name, price, link FROM product WHERE name = %s LIMIT 1",
            (name,)
        )
        db_item = cursor.fetchone()

        if db_item:
            final_result[key] = db_item
            total_price += db_item["price"] or 0
        else:
            final_result[key] = item

    final_result["total_price"] = total_price
    conn.close()
    return final_result


# -------------------------------------
# 🚀 핵심: reply 제거 + JSON 견적만 반환
# -------------------------------------
async def process_chat_request(session_id: str, user_message: str):
    # 1️⃣ 이전 대화 문맥 불러오기
    messages = get_messages(session_id)

    # 2️⃣ 이전 JSON 견적 찾기
    previous_estimate = None
    for msg in reversed(messages):
        if msg["role"] == "assistant":
            try:
                js = json.loads(msg["content"])
                if "cpu" in js and "gpu" in js:
                    previous_estimate = js
                    break
            except:
                pass

    # 3️⃣ 기본 프롬프트 생성
    prompt = build_prompt(user_message)

    # 4️⃣ 시스템 프롬프트 (설명 제거)
    system_prompt = {
        "role": "system",
        "content": (
            "너는 PC 견적 전문가이다. "
            "항상 JSON만 출력해야 하며, 자연어는 절대 출력하지 않는다. "
            "이전 견적(JSON)이 있으면 반드시 그 견적을 기반으로 수정해야 한다. "
            "new JSON만 출력하고 설명 금지."
        ),
    }

    # 5️⃣ 전체 메시지 구성
    chat_messages = [system_prompt]

    # 이전 견적 있으면 문맥으로 제공
    if previous_estimate:
        chat_messages.append({
            "role": "assistant",
            "content": json.dumps(previous_estimate, ensure_ascii=False)
        })

    # 유저 요청 + Chroma 제품 목록 포함 프롬프트
    chat_messages.append({"role": "user", "content": prompt})

    # 6️⃣ GPT 호출
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_messages
    )
    raw_text = completion.choices[0].message.content.strip()

    print("🔥 GPT RAW:", raw_text)
    sys.stdout.flush()

    # 6️⃣ JSON 파싱 및 복구 (Code B의 리스트 변환 로직 추가)
    parsed = {}
    try:
        match = re.search(r"\{[\s\S]*\}", raw_text)
        if match:
            parsed = json.loads(match.group(0))
        else:
            # 혹시 JSON이 전체가 리스트로 감싸져 있을 경우 대비
            match_list = re.search(r"\[[\s\S]*\]", raw_text)
            if match_list:
                temp_list = json.loads(match_list.group(0))
                # 리스트를 딕셔너리로 변환
                if isinstance(temp_list, list):
                    print("⚠️ GPT가 리스트를 반환함 -> 변환 시도")
                    for item in temp_list:
                        cat = item.get("category", "").lower() or "unknown"
                        # 카테고리 매핑 (필요시 확장)
                        if "cpu" in cat: parsed["cpu"] = item
                        elif "vga" in cat or "gpu" in cat: parsed["gpu"] = item
                        elif "board" in cat: parsed["mboard"] = item
                        elif "ram" in cat: parsed["ram"] = item
                        elif "ssd" in cat: parsed["ssd"] = item
                        elif "cooler" in cat: parsed["cooler"] = item
                        elif "power" in cat: parsed["power"] = item
                        elif "case" in cat: parsed["case"] = item
    except Exception as e:
        print(f"❌ JSON 파싱 에러: {e}")
        parsed = {}
    
    # 8️⃣ DB 가격/링크 보정
    enriched = enrich_with_db_info(parsed)

    # 9️⃣ Redis 문맥 저장 (오직 JSON만 저장)
    append_message(session_id, "user", user_message)
    append_message(session_id, "assistant", json.dumps(enriched, ensure_ascii=False))

    # 10️⃣ "reply" 제거하고 JSON만 반환
    return {
        "success": True,
        "estimate": enriched
    }
