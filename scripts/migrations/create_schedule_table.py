from app import create_app, db
from app.models.schedule import Schedule
import sqlite3

# アプリケーションコンテキストを作成
app = create_app()
app_context = app.app_context()
app_context.push()

print("schedulesテーブルを作成します...")

try:
    # schedulesテーブルの作成
    db.metadata.create_all(bind=db.engine, tables=[Schedule.__table__])
    print("schedulesテーブルを作成しました")

    # テーブル構造の確認
    db_path = "./instance/aircon_report.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n=== schedulesテーブルの構造 ===")
    cursor.execute("PRAGMA table_info(schedules);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

    # 外部キー制約の確認
    print("\n=== schedulesテーブルの外部キー ===")
    cursor.execute("PRAGMA foreign_key_list(schedules);")
    foreign_keys = cursor.fetchall()
    for fk in foreign_keys:
        print(f"ID: {fk[0]}, From: {fk[3]}, To: {fk[2]}({fk[4]})")

    conn.close()
    print("\nschedulesテーブルの作成が完了しました")

except Exception as e:
    print(f"エラー: {e}")

app_context.pop()
