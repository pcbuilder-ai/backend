import time
import csv
import hashlib
import re
from datetime import datetime,timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------
# 설정
# -----------------------
CONFIG = {
    "CPU": ("https://prod.danawa.com/list/?cate=112747", 4),
    "RAM": ("https://prod.danawa.com/list/?cate=112752", 10),
    "VGA": ("https://prod.danawa.com/list/?cate=112753", 10),
    "MBoard_intel": ("https://prod.danawa.com/list/?cate=11345282", 10),
    "MBoard_amd": ("https://prod.danawa.com/list/?cate=1131249", 10),
    "SSD": ("https://prod.danawa.com/list/?cate=112760", 5),
    "HDD": ("https://prod.danawa.com/list/?cate=1131401", 2),
    "Power": ("https://prod.danawa.com/list/?cate=112777", 10),
    "Case": ("https://prod.danawa.com/list/?cate=112775", 10),
    "Cooler_Liquid": ("https://prod.danawa.com/list/?cate=11336856", 5),
    "Cooler_Air": ("https://prod.danawa.com/list/?cate=11336857", 5),
}

KST = datetime.now() + timedelta(hours=9)
OUTPUT_CSV = f"./data/danawa{KST.strftime('%Y%m%d_%H%M%S')}.csv"


# -----------------------
# 드라이버 초기화
# -----------------------
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(5)
    return driver


# -----------------------
# 유틸
# -----------------------
def stable_id_from_link(link: str) -> str:
    return hashlib.sha256(link.encode("utf-8-sig")).hexdigest()[:16]


def ensure_csv_header(path: str):
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ["id", "name", "price","capacity", "link", "category", "spec", "updated_at"]

    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)


def append_rows_to_csv(path: str, rows: list[dict]):
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(
                [r.get(k, "") for k in ["id", "name", "price", "capacity", "link", "category", "spec","updated_at"]]
            )

def clean_capacity(category: str, raw_text: str):
    """
    용량 문자열 정제:
    - HDD의 괄호 뒤 모델명 제거
    - RAM의 수량형, 벌크형, 세트형 항목 제거
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # HDD: 괄호 안의 모델명 제거 (예: 4TB (WD40EZAZ) → 4TB)
    text = re.sub(r"\s*\(.*?\)", "", text)

    # RAM: 수량별/세트/벌크 등 제외
    if category.upper().startswith("RAM"):
        # 제외할 단어 목록
        skip_words = ["수량", "벌크", "세트", "패키지"]
        if any(word in text for word in skip_words):
            return ""

    # 용량만 남기기 (예: 32GB, 1TB 등)
    match = re.search(r"(\d+(?:\.\d+)?\s?(?:GB|TB))", text, re.IGNORECASE)
    return match.group(1).upper().replace(" ", "") if match else ""

# -----------------------
# 크롤링 로직
# -----------------------
def parse_products(driver, category: str, url: str, max_pages: int):
    results = []

    for page in range(1, max_pages + 1):
        page_url = f"{url}&page={page}"
        driver.get(page_url)
        time.sleep(2)

        items = driver.find_elements(
            By.CSS_SELECTOR, "div.main_prodlist > ul.product_list > li.prod_item"
        )
        if not items:
            print(f"[{category}] page {page}: no items found")
            break

        for item in items:
            try:
                name_el = item.find_element(By.CSS_SELECTOR, "p.prod_name a")
                base_name = name_el.text.strip()

                # 스펙
                try:
                    spec_el = item.find_element(By.CLASS_NAME, "spec_list")
                    spec_text = spec_el.get_attribute("textContent").strip()
                except:
                    spec_text = ""

                # ✅ 용량별 변형 상품 추출 (RAM, SSD, HDD 등)
                variant_elems = item.find_elements(By.CSS_SELECTOR, "div.prod_pricelist ul li")

                if variant_elems:
                    for v in variant_elems:
                        try:
                            raw_capacity = v.find_element(By.CSS_SELECTOR, "p.memory_sect span.text").text.strip()
                        except:
                            raw_capacity = ""
                        capacity = clean_capacity(category, raw_capacity)
                        if not capacity:
                            continue

                        try:
                            price_text = v.find_element(By.CSS_SELECTOR, "p.price_sect strong").text.strip()
                            price = int(price_text.replace(",", "").replace("원", ""))
                        except:
                            price = None

                        try:
                            link = v.find_element(By.CSS_SELECTOR, "p.price_sect a").get_attribute("href")
                        except:
                            link = name_el.get_attribute("href")

                        results.append({
                            "id": stable_id_from_link(link),
                            "name": f"{base_name} ({capacity})" if capacity else base_name,
                            "price": price,
                            "capacity": capacity,
                            "link": link,
                            "category": category,
                            "spec": spec_text,
                            "updated_at": datetime.now().isoformat(),
                        })
                else:
                    # 일반 상품 (CPU 등)
                    try:
                        price_el = item.find_element(By.CSS_SELECTOR, "p.price_sect strong")
                        price_text = price_el.text.replace(",", "").replace("원", "").strip()
                        price = int(price_text) if price_text.isdigit() else None
                    except:
                        price = None

                    link = name_el.get_attribute("href")

                    results.append({
                        "id": stable_id_from_link(link),
                        "name": base_name,
                        "price": price,
                        "capacity": "",
                        "link": link,
                        "category": category,
                        "spec": spec_text,
                        "updated_at": datetime.now().isoformat(),
                    })

            except Exception:
                continue

    return results


# -----------------------
# 메인
# -----------------------
def main():
    driver = init_driver()
    ensure_csv_header(OUTPUT_CSV)

    total = 0
    for category, (url, max_pages) in CONFIG.items():
        print(f"▶ 카테고리: {category}")
        products = parse_products(driver, category, url, max_pages)
        append_rows_to_csv(OUTPUT_CSV, products)
        total += len(products)

    driver.quit()
    print(f"총 {total}개 상품 저장 완료 → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
