from app import create_app, db
from app.models.property import Property
import sqlite3
import os

# アプリケーションコンテキストを作成
app = create_app()
app_context = app.app_context()
app_context.push()

# データベースファイルのパス
db_path = os.path.join("instance", "aircon_report.db")

# データベースに接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル一覧を取得
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=== テーブル一覧 ===")
for table in tables:
    print(table[0])

# プロパティテーブルの構造を表示
print("\n=== propertiesテーブルの構造 ===")
cursor.execute("PRAGMA table_info(properties)")
columns = cursor.fetchall()
for i, col in enumerate(columns):
    print(f"{i}: {col[1]} ({col[2]})" + (" PRIMARY KEY" if col[5] == 1 else ""))

# プロパティテーブルのデータを表示
print("\n=== properties テーブルのデータ ===")
cursor.execute("SELECT id, name, address FROM properties")
properties = cursor.fetchall()
for prop in properties:
    print(f"ID: {prop[0]}, 名前: {prop[1]}, 住所: {prop[2]}")

# 写真テーブルのデータを表示
print("\n=== photos テーブルのデータ ===")
cursor.execute("SELECT id, report_id, photo_type, filename FROM photos")
photos = cursor.fetchall()
for photo in photos:
    print(
        f"ID: {photo[0]}, レポートID: {photo[1]}, タイプ: {photo[2]}, ファイル名: {photo[3]}"
    )

# 写真タイプごとの数を表示
print("\n=== 写真タイプごとの数 ===")
cursor.execute("SELECT photo_type, COUNT(*) FROM photos GROUP BY photo_type")
photo_counts = cursor.fetchall()
for count in photo_counts:
    print(f"タイプ: {count[0]}, 数: {count[1]}")

# データベース接続を閉じる
conn.close()
app_context.pop()
