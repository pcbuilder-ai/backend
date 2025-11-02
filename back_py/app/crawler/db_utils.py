import mysql.connector
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

def save_to_mysql(product):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO product (fingerprint, name, category, spec, price, capacity, link, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            price=VALUES(price),
            capacity=VALUES(capacity),
            spec=VALUES(spec),
            updated_at=VALUES(updated_at)
        """,
        (
            product["id"],               # ✅ stable_id_from_link(link) → fingerprint로 사용
            product["name"],
            product["category"],
            product["spec"],
            int(product.get("price") or 0),
            product.get("capacity"),
            product["link"],
            datetime.now()
        ),
    )

    conn.commit()
    conn.close()
