from app import create_app, db
import sqlite3

# アプリケーションコンテキストを作成
app = create_app()
app_context = app.app_context()
app_context.push()

print("物件テーブルに受付フィールドを追加します...")

# SQLiteデータベースに接続
db_path = "./instance/aircon_report.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # reception_typeカラムを追加
    print("reception_typeカラムを追加しています...")
    cursor.execute("ALTER TABLE properties ADD COLUMN reception_type TEXT;")
    print("reception_typeカラムを追加しました")

    # reception_detailカラムを追加
    print("reception_detailカラムを追加しています...")
    cursor.execute("ALTER TABLE properties ADD COLUMN reception_detail TEXT;")
    print("reception_detailカラムを追加しました")

    # 変更を確定
    conn.commit()
    print("マイグレーション成功: 受付フィールドが追加されました")

except Exception as e:
    conn.rollback()
    print(f"マイグレーションエラー: {e}")

# propertiesテーブルの構造を表示
print("\n=== propertiesテーブルの構造 ===")
cursor.execute("PRAGMA table_info(properties);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

conn.close()
app_context.pop()
