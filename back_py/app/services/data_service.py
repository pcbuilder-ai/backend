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
        database="project",
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci"
    )

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