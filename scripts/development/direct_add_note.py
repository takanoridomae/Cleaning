import sqlite3
import os

# データベースパスを指定
db_path = os.path.join(os.getcwd(), "instance", "aircon_report.db")
print(f"データベースパス: {db_path}")

if not os.path.exists(db_path):
    print(f"エラー: データベースファイルが見つかりません: {db_path}")
    exit(1)

try:
    # SQLiteデータベースに直接接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル構造を表示
    cursor.execute("PRAGMA table_info(work_times)")
    columns = cursor.fetchall()
    print("現在のwork_timesテーブル構造:")
    column_names = []
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
        column_names.append(col[1])

    print(f"検出された列名: {column_names}")

    # noteカラムの存在を確認
    if "note" in column_names:
        print("noteカラムは既に存在しています。")
    else:
        print("noteカラムが存在しません。テーブルを再作成します。")

        # データのバックアップを取得
        cursor.execute("SELECT * FROM work_times")
        existing_data = cursor.fetchall()
        print(f"{len(existing_data)}件のデータをバックアップしました。")

        # 一時テーブルを作成
        cursor.execute(
            """
        CREATE TABLE work_times_temp (
            id INTEGER PRIMARY KEY,
            work_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            report_id INTEGER NOT NULL,
            property_id INTEGER,
            note TEXT
        )
        """
        )

        # データを一時テーブルに移行
        for row in existing_data:
            # データ長を確認して不足があれば埋める
            data = list(row)
            while len(data) < 8:  # property_idまで
                data.append(None)
            # noteカラム用にNoneを追加
            data.append(None)

            # データを挿入
            cursor.execute(
                """
            INSERT INTO work_times_temp (id, work_date, start_time, end_time, created_at, updated_at, report_id, property_id, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

        # 元のテーブルを削除して一時テーブルをリネーム
        cursor.execute("DROP TABLE work_times")
        cursor.execute("ALTER TABLE work_times_temp RENAME TO work_times")

        # 変更を確定
        conn.commit()

        # 更新後の構造を確認
        cursor.execute("PRAGMA table_info(work_times)")
        new_columns = cursor.fetchall()
        print("\n更新後のテーブル構造:")
        for col in new_columns:
            print(f"  {col[1]} ({col[2]})")

        print("テーブル構造の更新が完了しました。")

except Exception as e:
    print(f"エラーが発生しました: {e}")
    if "conn" in locals():
        conn.rollback()

finally:
    if "conn" in locals():
        conn.close()
    print("処理を完了しました。")
