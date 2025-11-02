import time
import csv
import os
import re
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ DB & Vector utils
from db_utils import save_to_mysql
from vector_utils import save_to_vector_db


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

OUTPUT_CSV = f"./data/danawa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


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

def stable_id_from_link(link: str, category: str = "", capacity: str = "", name: str ="") -> str:
    """링크 + 카테고리 + 용량을 조합해서 고유 ID 생성"""
    if not capacity:
        capacity = "N/A"
    match = re.search(r"pcode=(\d+)",link)
    pcode = match.group(1) if match else link
    unique_key = f"{category}_{capacity}_{pcode}_{name}"
    return hashlib.sha256(unique_key.encode("utf-8-sig")).hexdigest()[:16]



def ensure_csv_header(path: str):
    """CSV 파일 생성 및 헤더 보장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ["id", "name", "price", "capacity", "link", "category", "spec", "updated_at"]
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(header)


def append_to_csv(product: dict):
    """한 줄씩 CSV 저장"""
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            product.get("id"),
            product.get("name"),
            product.get("price"),
            product.get("capacity"),
            product.get("link"),
            product.get("category"),
            product.get("spec"),
            product.get("updated_at")
        ])


def clean_capacity(category: str, raw_text: str):
    """RAM/HDD 용량 정제"""
    if not raw_text:
        return ""

    text = raw_text.strip()

    # RAM: 수량형, 벌크 등 제외
    if category.upper().startswith("RAM"):
        skip_words = ["수량", "벌크", "세트", "패키지"]
        if any(word in text for word in skip_words):
            return ""

    # HDD: 쉼표 뒤 모델명 제거
    if category.upper().startswith("HDD"):
        text = text.split(",")[0].strip()

    return text

# -----------------------
# 크롤링 로직
# -----------------------
def parse_products(driver, category: str, url: str, max_pages: int):
    results = []

    for page in range(1, max_pages + 1):
        print(f"  🔹 {category} {page}페이지 크롤링 중...")
        driver.get(url)
        time.sleep(2)

        if page > 1:
            try:
                js_code = f"movePage({page});"
                driver.execute_script(js_code)
                time.sleep(2.5)  # 페이지 로딩 대기
            except Exception as e:
                print(f"⚠️ 페이지 이동 실패 (page={page}): {e}")
                continue

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

                is_memeory_category = category.upper() in ["RAM", "SSD", "HDD"]
                # ✅ 용량별 변형 상품 추출 (RAM, SSD, HDD 등)
                if is_memeory_category:
                    variant_elems = item.find_elements(By.CSS_SELECTOR, "div.prod_pricelist ul li")
                    for v in variant_elems:
                        try:
                            raw_capacity = v.find_element(By.CSS_SELECTOR, "p.memory_sect span.text").text.strip()
                        except:
                            raw_capacity = ""
                        capacity = clean_capacity(category, raw_capacity)
                        if not capacity:
                            capacity="N/A"
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
                            "id": stable_id_from_link(link,category,capacity,f"{base_name} ({capacity})" if capacity else base_name),
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
                        "id": stable_id_from_link(link,category,"N/A",base_name),
                        "name": base_name,
                        "price": price,
                        "capacity": "N/A",
                        "link": link,
                        "category": category,
                        "spec": spec_text,
                        "updated_at": datetime.now().isoformat(),
                    })

            except Exception:
                continue

    return results


# -----------------------
# 메인 실행
# -----------------------
def main():
    driver = init_driver()
    ensure_csv_header(OUTPUT_CSV)

    for category, (url, max_pages) in CONFIG.items():
        print(f"\n▶ 카테고리: {category}")
        products = parse_products(driver, category, url, max_pages)

        for p in products:
            append_to_csv(p)
            save_to_mysql(p)
        save_to_vector_db(products)

    driver.quit()
    print(f"\n✅ 모든 크롤링 및 저장 완료 → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
