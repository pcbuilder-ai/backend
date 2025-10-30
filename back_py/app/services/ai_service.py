# app/services/ai_service.py
import os
import re
import json
from openai import OpenAI  
from dotenv import load_dotenv
from app.services.data_service import get_hint_products

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_query(query: str):
    """자연어에서 예산(만원 단위)과 용도 키워드 추출"""
    budget = None
    purpose = None

    # 예산 추출 (예: 100만원 이하, 150만원대)
    match = re.search(r"(\d+)\s*만원", query)
    if match:
        budget = int(match.group(1)) * 10000

    # 용도 키워드 탐색
    for keyword in ["사무", "게임", "롤", "영상", "편집", "디자인", "작업"]:
        if keyword in query:
            purpose = keyword
            break

    return budget, purpose

def prepare_gpt_prompt(query: str):
    budget, purpose = parse_query(query)
    hint_products = get_hint_products(budget, purpose)

    grouped = {}
    for item in hint_products:
        cat = item["category"].lower()
        grouped.setdefault(cat, []).append(item)

    grouped_json = json.dumps(grouped, ensure_ascii=False, indent=2)


    grouped_json = json.dumps(hint_products, ensure_ascii=False, indent=2)

    prompt = f"""
    사용자의 요청: "{query}"

    분석 결과:
    - 예산: {budget if budget else "명시 안됨"}
    - 용도: {purpose if purpose else "명시 안됨"}

    아래는 실제 DB에서 가져온 부품 목록입니다.
    ⚠️ 반드시 이 목록 안에 있는 제품만 사용해야 합니다.
    ⚠️ DB에 없는 제품은 절대 새로 만들어내지 마세요.
    ⚠️ name, price, link 값을 절대로 수정하거나 요약하지 마세요.
    ⚠️ 특히 link는 반드시 DB에 있는 값을 그대로 복사해서 사용해야 합니다.
    ⚠️ 'www.danawa.com', 'example.com' 등으로 바꾸지 마세요.
    ⚠️ DB JSON에 있는 link 값을 그대로 결과에 포함하세요.

    부품 목록(JSON):
    {grouped_json}

    위 목록 안의 제품들로, 다음 카테고리를 모두 포함한 PC 견적을 구성하세요.
    - CPU
    - VGA
    - RAM
    - SSD
    - Cooler
    - Power
    - Case

    출력 형식(반드시 JSON만):
    {{
      "cpu": {{ "name": "...", "price": ..., "link": "..." }},
      "gpu": {{ "name": "...", "price": ..., "link": "..." }},
      "ram": {{ "name": "...", "price": ..., "link": "..." }},
      "ssd": {{ "name": "...", "price": ..., "link": "..." }},
      "cooler": {{ "name": "...", "price": ..., "link": "..." }},
      "power": {{ "name": "...", "price": ..., "link": "..." }},
      "case": {{ "name": "...", "price": ..., "link": "..." }},
      "total_price": "..." 
    }}

    반드시 DB에서 제공된 부품 중 각 카테고리별 하나씩만 선택하고,
    가격의 총합(total_price)은 각 price의 합계로 계산하세요.
    """
    return prompt

def generate_estimate(query: str):
    prompt = prepare_gpt_prompt(query)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", 
             "content": "너는 반드시 DB에서 제공된 JSON 목록 안의 제품만 사용하는 견적 전문가야."
              "JSON 안에 제공된 link 값을 절대 수정하거나 요약하지 마. " 
              "링크는 반드시 그대로 복사해 사용해야 해."},
            {"role": "user", "content": prompt},
        ],
    )

    text = response.choices[0].message.content.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"raw": text}

    return {"raw": text}