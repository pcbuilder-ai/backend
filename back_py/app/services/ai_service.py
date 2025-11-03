import os
import re
import json
import sys

from openai import OpenAI
from dotenv import load_dotenv
from app.services.data_service import get_hint_products, get_connection

# ----------------------------
# 🌍 환경 로드 + 클라이언트 설정
# ----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------
# 💰 예산 / 용도 파싱
# ----------------------------
def parse_query(query: str):
    """문장에서 예산(만원 단위), 용도, 쿨러 타입, 메인보드 구분 추출"""
    budget = None
    purpose = None
    cooler_type = None
    board_type = None

    # 💸 예산 추출
    match = re.search(r"(\d+)\s*만원", query)
    if match:
        budget = int(match.group(1)) * 10000

    # 🖥️ 용도 키워드 추출
    for keyword in ["사무", "게임", "롤", "영상", "편집", "디자인", "작업"]:
        if keyword in query:
            purpose = keyword
            break

    # ❄️ 쿨러 타입 추출
    if "수랭" in query:
        cooler_type = "Cooler_Liquid"
    elif "공랭" in query:
        cooler_type = "Cooler_Air"

    # 🧩 메인보드 타입 추출
    if "인텔" in query:
        board_type = "MBoard_intel"
    elif "amd" in query.lower():
        board_type = "MBoard_amd"

    return budget, purpose, cooler_type, board_type

# ----------------------------
# 🧠 GPT 프롬프트 구성
# ----------------------------
def prepare_gpt_prompt(query: str):
    budget, purpose, cooler_type, board_type = parse_query(query)
    hint_products = get_hint_products(budget, purpose)

    grouped_json = json.dumps(hint_products, ensure_ascii=False, indent=2)

    prompt = f"""
    너는 고성능 PC 견적을 짜는 전문가야.
    반드시 **아래 JSON 형식 그대로** 출력해야 해.
    ⚠️ JSON 외 텍스트, 설명, 마크다운, 주석은 절대 출력하지 마.
    ⚠️ 배열([]) 형태로 출력하지 마. 반드시 하나의 JSON 객체({{}})로만 출력해야 해.

    사용자의 요청: "{query}"

    분석 결과:
    - 예산: {budget if budget else "명시 안됨"}
    - 용도: {purpose if purpose else "명시 안됨"}
    - 쿨러 타입: {cooler_type or "자동 선택"}
    - 메인보드 타입: {board_type or "자동 선택"}

    아래는 실제 DB 및 벡터DB에서 가져온 제품 목록이야.
    ⚠️ 반드시 이 목록 안의 제품만 사용할 수 있어.
    ⚠️ DB에 없는 제품, 이름, 링크, 가격을 새로 만들면 안 돼.
    ⚠️ name, link, price는 그대로 복사해야 해.

    제품 목록(JSON):
    {grouped_json}

    견적 구성 규칙:
      ⚠️ CPU는 반드시 포함되어야 하며, 어떤 상황에서도 생략하면 안 됨.
    - CPU는 가장 먼저 선택해야 하며, GPU보다 우선순위가 높음.
    - CPU와 메인보드 호환 규칙:
      | CPU 브랜드 | 선택 가능한 메인보드 |
      |-------------|----------------------|
      | Intel       | MBoard_intel (B660, B760, Z690, Z790 등) |
      | AMD         | MBoard_amd (A520, B550, X570 등) |
      ⚠️ CPU와 메인보드는 반드시 동일한 브랜드(플랫폼)여야 함.
      ⚠️ 예: "인텔 CPU + AMD 보드" 또는 "AMD CPU + Intel 보드"는 절대 금지.
      ⚠️ 호환되지 않는 조합이 있으면 반드시 올바른 쌍으로 교체해야 함.
          - 인텔 CPU ↔ 메인보드 소켓 규칙:
      | CPU 세대 | 소켓 | 호환 메인보드 |
      |-----------|------|----------------|
      | 10세대, 11세대 | LGA1200 | B460, B560, H510, Z490, Z590 |
      | 12세대, 13세대, 14세대 | LGA1700 | B660, B760, Z690, Z790 |
      ⚠️ 세대가 다르거나 소켓이 다르면 절대 호환되지 않음.
      ⚠️ 예: i5-11400 (LGA1200)은 B760, Z690 등과 호환되지 않음.
      ⚠️ CPU와 보드는 반드시 동일 소켓 규격이어야 함.
          - AMD CPU ↔ 메인보드 소켓 규칙:
      | CPU 시리즈 | 소켓 | 호환 메인보드 |
      |-------------|------|----------------|
      | Ryzen 3~5세대 | AM4 | A520, B550, X570 |
      | Ryzen 7000 시리즈 | AM5 | B650, X670 |
      ⚠️ AM4 CPU는 AM5 보드와 절대 호환되지 않음.
    - 반드시 다음 항목을 모두 포함해야 함: CPU, VGA, MBoard, RAM, SSD, Cooler, Power, Case
    - 하나라도 누락되거나 빈 문자열("") 또는 price=0이면 "잘못된 견적"으로 판단됨
    - 누락 시 반드시 가장 적합한 제품으로 채워넣어야 함
    - JSON 필드는 절대 생략하지 마
    - RAM 구성 원칙:
      ① "16GB 모듈 2개" (총 32GB 듀얼채널)을 가장 우선적으로 선택해야 함.
      ② "32GB 단일 모듈"은 절대 선택하지 마.
      ③ "8GB x2"는 너무 적으므로 피할 것.
      ④ "32GB x2" 또는 "64GB" 등 과도한 용량은 예산 낭비이므로 절대 선택하지 마.
    - Cooler는 "{cooler_type or '공랭 또는 수랭 중 선택'}" 기준으로 선택
    - MBoard는 "{board_type or 'CPU와 호환되는 메인보드'}" 선택
    - total_price는 모든 price의 합으로 계산
    - price는 원 단위 숫자만 (쉼표·단위 제거)
    - 빈 문자열("") 또는 0 금액은 절대 사용하지 마
    - JSON 이외 텍스트 금지
    - 메인보드(MBoard)는 CPU와 소켓 규격이 반드시 호환되어야 함
    - 메모리(RAM)는 메인보드의 지원 규격(DDR4 / DDR5)과 반드시 일치해야 함
    - 예: B550, B660, Z690 등은 DDR4 전용 / Z790, B760 등은 DDR5 지원
    - 호환되지 않는 부품 조합은 절대 선택하지 마

    예산 분배 가이드:
    - CPU: 약 25~30%
    - GPU: 약 30~40%
    - MBoard: 약 10%
    - RAM: 약 10%
    - SSD: 약 5~10%
    - Cooler: 약 5%
    - Power + Case: 약 10%

    출력 형식(반드시 JSON 객체만):
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


# ----------------------------
# 🧩 DB에서 가격·링크 보정
# ----------------------------
def enrich_with_db_info(result_json):
    """GPT가 생성한 견적을 DB 정보로 보정"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    final_result = {}
    total_price = 0

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
            final_result[key] = item  # GPT 결과 그대로 유지

    final_result["total_price"] = total_price
    conn.close()
    return final_result

# ----------------------------
# 🚀 GPT 호출 및 견적 생성
# ----------------------------
def generate_estimate(query: str):
    """사용자 입력(query)에 따라 견적 생성"""
    prompt = prepare_gpt_prompt(query)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": (
                 "너는 반드시 주어진 JSON 데이터 안의 제품만 사용하는 PC 견적 전문가야. "
                 "링크와 가격은 수정하거나 요약하면 안 되며, "
                 "출력은 반드시 JSON만 해야 해."
             )},
            {"role": "user", "content": prompt},
        ],
    )

    text = response.choices[0].message.content.strip()
    print("🔍 GPT 전체 응답 ↓↓↓\n", text)
    sys.stdout.flush()

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {"raw": text}

    try:
        result_json = json.loads(match.group(0))

        # ✅ GPT가 리스트 반환 시 예외 처리
        if isinstance(result_json, list):
            print("⚠️ GPT가 리스트를 반환함 → dict 변환 시도 중...")
            converted = {}
            for item in result_json:
                cat = item.get("category", "").lower()
                if cat:
                    converted[cat] = {
                        "name": item.get("name"),
                        "price": item.get("price"),
                        "link": item.get("link")
                    }
            result_json = converted

        # ✅ DB 정보 기반 보정
        enriched = enrich_with_db_info(result_json)

        print("✅ 최종 견적 ↓↓↓")
        print(json.dumps(enriched, ensure_ascii=False, indent=2))
        sys.stdout.flush()

        return enriched

    except Exception as e:
        return {"error": str(e), "raw": text}
