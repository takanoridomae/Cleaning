import sqlite3
import sys

# SQLiteデータベースに接続
db_path = "./instance/aircon_report.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# コマンドライン引数でテーブル名が指定されている場合
target_table = sys.argv[1] if len(sys.argv) > 1 else None

# テーブル一覧
print("=== テーブル一覧 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

# propertiesテーブルの構造
print("\n=== propertiesテーブル構造 ===")
cursor.execute("PRAGMA table_info(properties);")
columns = cursor.fetchall()
for col in columns:
    print(
        f"{col[0]}: {col[1]} ({col[2]}) {col[3]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
    )

# 指定されたテーブルがreportsの場合、reportsテーブルの構造を表示
if target_table == "reports":
    print("\n=== reportsテーブル構造 ===")
    cursor.execute("PRAGMA table_info(reports);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {col[3]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # foreign keyの確認
    print("\n=== reportsテーブルの外部キー ===")
    cursor.execute("PRAGMA foreign_key_list(reports);")
    foreign_keys = cursor.fetchall()
    for fk in foreign_keys:
        print(f"ID: {fk[0]}, From: {fk[3]}, To: {fk[2]}({fk[4]})")

    # reportsのデータがあるか確認
    print("\n=== reportsテーブルのデータ ===")
    cursor.execute("SELECT * FROM reports LIMIT 5;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("データがありません")
elif target_table == "work_times":
    print("\n=== work_timesテーブル構造 ===")
    cursor.execute("PRAGMA table_info(work_times);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {col[3]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # foreign keyの確認
    print("\n=== work_timesテーブルの外部キー ===")
    cursor.execute("PRAGMA foreign_key_list(work_times);")
    foreign_keys = cursor.fetchall()
    for fk in foreign_keys:
        print(f"ID: {fk[0]}, From: {fk[3]}, To: {fk[2]}({fk[4]})")

    # work_timesのデータがあるか確認
    print("\n=== work_timesテーブルのデータ ===")
    cursor.execute("SELECT * FROM work_times LIMIT 5;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("データがありません")
elif target_table == "work_details":
    print("\n=== work_detailsテーブル構造 ===")
    cursor.execute("PRAGMA table_info(work_details);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {col[3]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # foreign keyの確認
    print("\n=== work_detailsテーブルの外部キー ===")
    cursor.execute("PRAGMA foreign_key_list(work_details);")
    foreign_keys = cursor.fetchall()
    for fk in foreign_keys:
        print(f"ID: {fk[0]}, From: {fk[3]}, To: {fk[2]}({fk[4]})")

    # work_detailsのデータがあるか確認
    print("\n=== work_detailsテーブルのデータ ===")
    cursor.execute("SELECT * FROM work_details LIMIT 5;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("データがありません")
else:
    # air_conditionersテーブルの構造
    print("\n=== air_conditionersテーブル構造 ===")
    cursor.execute("PRAGMA table_info(air_conditioners);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {col[3]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # foreign keyの確認
    print("\n=== air_conditionersテーブルの外部キー ===")
    cursor.execute("PRAGMA foreign_key_list(air_conditioners);")
    foreign_keys = cursor.fetchall()
    for fk in foreign_keys:
        print(f"ID: {fk[0]}, From: {fk[3]}, To: {fk[2]}({fk[4]})")

    # air_conditionersのデータがあるか確認
    print("\n=== air_conditionersテーブルのデータ ===")
    cursor.execute("SELECT * FROM air_conditioners LIMIT 5;")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(row)
    else:
        print("データがありません")

conn.close()
