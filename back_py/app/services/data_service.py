import os
import pandas as pd
import mysql.connector
import hashlib
from datetime import datetime

def get_connection():
    return mysql.connector.connect(
        host="db",        
        user="root",
        password="1234",
        database="project"
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )

def get_latest_csv_path(data_dir="/app/data"):
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError("❌ CSV 파일이 없습니다.")
    latest = max(csv_files, key=lambda f: os.path.getctime(os.path.join(data_dir, f)))
    return os.path.join(data_dir, latest)

def csv_to_db():
    """가장 최신 CSV 파일을 DB로 적재"""
    csv_path = get_latest_csv_path()
    df = pd.read_csv(csv_path)

    # 컬럼 정리
    df.columns = [c.strip().lower() for c in df.columns]
    if "price" in df.columns:
        df["price"] = (
            df["price"].astype(str)
            .str.replace(",", "")
            .str.extract("(\d+)", expand=False)
            .fillna(0)
            .astype(int)
        )

    conn = get_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO product (name, category, spec, price, link, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                price=VALUES(price),
                updated_at=VALUES(updated_at)
            """,
            (
                row.get("name"),
                row.get("category"),
                row.get("spec"),
                int(row.get("price", 0)),
                row.get("link"),
                datetime.now(),
            ),
        )

    conn.commit()
    conn.close()
    print(f"✅ {len(df)}개 제품을 '{os.path.basename(csv_path)}'에서 불러와 DB에 저장했습니다.")

def get_hint_products(budget=None, purpose=None):
    conn = get_connection()
    df = pd.read_sql("SELECT name, category, price, link FROM product", conn)
    conn.close()

    # ✅ 포함할 모든 카테고리
    categories = ["CPU", "VGA", "RAM", "SSD", "Cooler", "Power", "Case"]
    df = df[df["category"].isin(categories)]

    # ✅ 예산 제한만 적용 (카테고리 필터링 X)
    if budget:
        df = df[df["price"].notna() & (df["price"] <= budget * 0.95)]

    # ✅ 카테고리별로 몇 개씩 샘플링
    samples = []
    for cat in categories:
        subset = df[df["category"] == cat].sort_values("price").head(5)
        if not subset.empty:
            samples.append(subset)

    if not samples:
        return []
    result = pd.concat(samples)
    return result.to_dict(orient="records")