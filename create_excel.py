import pandas as pd

# 테이블 구조 데이터
table_structure = {
    'Field': ['id', 'username', 'password', 'role'],
    'Type': ['bigint', 'varchar(255)', 'varchar(255)', 'varchar(255)'],
    'Null': ['NO', 'NO', 'NO', 'YES'],
    'Key': ['PRI', 'UNI', '', ''],
    'Default': ['NULL', 'NULL', 'NULL', 'ROLE_USER'],
    'Extra': ['auto_increment', '', '', '']
}

# 사용자 데이터
user_data = {
    'id': [1],
    'username': ['testuser'],
    'password': ['$2a$10$jxQ9r4BDx722tnaeO2.bp.iyIHywpqFgvyPCd2NWP.8j7Y7lnBaEi'],
    'role': ['ROLE_USER']
}

# DataFrame 생성
df_structure = pd.DataFrame(table_structure)
df_users = pd.DataFrame(user_data)

# 엑셀 파일로 저장
with pd.ExcelWriter('user_table_info.xlsx', engine='openpyxl') as writer:
    df_structure.to_excel(writer, sheet_name='테이블구조', index=False)
    df_users.to_excel(writer, sheet_name='사용자데이터', index=False)

print("엑셀 파일이 생성되었습니다: user_table_info.xlsx")
print("\n=== 테이블 구조 ===")
print(df_structure)
print("\n=== 사용자 데이터 ===")
print(df_users)
