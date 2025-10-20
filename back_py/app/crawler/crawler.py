import time
import csv
import hashlib
from datetime import datetime
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

OUTPUT_CSV = f"./data/danawa{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


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
    header = ["id", "name", "price", "link", "category", "spec", "updated_at"]

    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)


def append_rows_to_csv(path: str, rows: list[dict]):
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(
                [r.get(k, "") for k in ["id", "name", "price", "link", "category", "spec","updated_at"]]
            )


# -----------------------
# 크롤링 로직
# -----------------------
def parse_products(driver, category: str, url: str, max_pages: int):
    results = []

    for page in range(1, max_pages + 1):
        page_url = f"{url}&page={page}"
        driver.get(page_url)
        time.sleep(2)  # 페이지 로딩 대기

        items = driver.find_elements(
            By.CSS_SELECTOR, "div.main_prodlist > ul.product_list > li.prod_item"
        )
        if not items:
            print(f"[{category}] page {page}: no items found")
            break

        for item in items:
            try:
                name_el = item.find_element(By.CSS_SELECTOR, "p.prod_name a")
                name = name_el.text.strip()
                link = name_el.get_attribute("href")

                try:
                    price_el = item.find_element(By.CSS_SELECTOR, "p.price_sect strong")
                    price_text = price_el.text.replace(",", "").replace("원", "").strip()
                    price = int(price_text) if price_text.isdigit() else None
                except:
                    price = None

                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "spec_list"))
                    )
                    spec_element = item.find_element(By.CLASS_NAME, "spec_list")

                    raw_spec = spec_element.get_attribute("textContent").strip()
                    parts = [p.strip() for p in raw_spec.replace("\n", " | ").split("|") if p.strip()]
                    unique_parts = list(dict.fromkeys(parts))  # 순서 유지 중복 제거

                    spec_final = " | ".join(unique_parts)
                except Exception:
                    spec_final = ""


                results.append(
                    {
                        "id": stable_id_from_link(link),
                        "name": name,
                        "price": price,
                        "link": link,
                        "category": category,
                        "spec": spec_final,
                        "updated_at": datetime.now().isoformat(),
                    }
                )
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
