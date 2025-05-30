import os
import sqlite3
from datetime import datetime

# データベースファイルのパス
db_path = os.path.join("instance", "aircon_report.db")

# アップロードフォルダのパス
UPLOAD_FOLDER = "uploads"

# 現在の日時を取得（バックアップファイル名用）
now = datetime.now().strftime("%Y%m%d%H%M%S")

print(f"写真レコードクリーンアップを開始します ({now})")

# データベースに接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 写真レコードを取得
cursor.execute("SELECT id, photo_type, filename FROM photos")
photos = cursor.fetchall()

deleted_count = 0
for photo in photos:
    photo_id, photo_type, filename = photo

    # ファイルパスを構築
    file_path = os.path.join(UPLOAD_FOLDER, photo_type, filename)

    # ファイルが存在しない場合、レコードを削除
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path} (ID: {photo_id})")
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        deleted_count += 1

# 変更をコミット
conn.commit()

print(f"クリーンアップ完了: {deleted_count}件の孤立した写真レコードを削除しました")

# 写真の数を確認
cursor.execute("SELECT photo_type, COUNT(*) FROM photos GROUP BY photo_type")
photo_counts = cursor.fetchall()
print("\n現在の写真レコード数:")
for count in photo_counts:
    print(f"タイプ: {count[0]}, 数: {count[1]}")

# データベース接続を閉じる
conn.close()
