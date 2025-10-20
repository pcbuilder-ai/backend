# app/services/ai_service.py
import os
from openai import OpenAI  

client = OpenAI(api_key="OPENAI_KEY")

def generate_estimate(query: str):
    if not query:
        return {"error": "질의가 비어 있습니다."}

    prompt = f"""
    사용자의 요청: "{query}"
    아래는 맞춤형 PC 견적을 생성하는 규칙입니다.
    - 용도(사무용, 게이밍 등)에 맞게 CPU, GPU, RAM, SSD, 파워, 케이스 조합
    - 가격은 저가/중간/고가 수준으로 추정
    - 결과를 JSON 형식으로 출력

    예시:
    {{
        "cpu": "Intel i5-13400F",
        "gpu": "RTX 4060",
        "ram": "DDR5 16GB",
        "storage": "SSD 500GB",
        "power": "600W",
        "case": "미들타워",
        "total_price": "약 100만원"
    }}
    """

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 PC 견적 전문가야."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    except Exception as e:
        print("🔥 [OpenAI Error]", e)

        return {"error": str(e)}
