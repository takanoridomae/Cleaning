from app import create_app, db
import sqlite3
import os
from datetime import datetime

app = create_app()


def fix_work_time_table():
    print("作業時間テーブルの構造を修正します...")

    # アプリケーション設定からデータベースパスを取得
    with app.app_context():
        db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_path.startswith("sqlite:///"):
            db_path = db_path[10:]  # sqlite:/// を削除
        else:
            db_path = "instance/aircon_report.db"  # デフォルトパス

    # 絶対パスに変換
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.root_path, "..", db_path)

    print(f"データベースパス: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return

    # SQLiteデータベースに直接接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 既存のデータをバックアップ
        cursor.execute("SELECT * FROM work_times")
        existing_data = cursor.fetchall()
        print(f"既存の作業時間データ {len(existing_data)}件をバックアップしました")

        # カラム情報を取得
        cursor.execute("PRAGMA table_info(work_times)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print("現在のwork_timesテーブル構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # property_idカラムの存在確認
        has_property_id = "property_id" in column_names
        # noteカラムの存在確認
        has_note = "note" in column_names

        if has_property_id and has_note:
            print("既に必要なカラムが全て存在しています。")
            return

        # テーブルの再作成
        print("作業時間テーブルを再作成します...")

        # 一時テーブルにデータを移動
        cursor.execute(
            """
            CREATE TABLE work_times_backup (
                id INTEGER PRIMARY KEY,
                work_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                report_id INTEGER NOT NULL
            )
        """
        )

        # 既存データを一時テーブルにコピー
        for row in existing_data:
            # 既存のカラム数に合わせてINSERT文を調整
            placeholders = ", ".join(["?" for _ in range(len(column_names))])
            insert_sql = f"INSERT INTO work_times_backup VALUES ({placeholders})"
            cursor.execute(insert_sql, row)

        # 元のテーブルを削除
        cursor.execute("DROP TABLE work_times")

        # 新しいテーブルを作成（全ての必要なカラムを含む）
        cursor.execute(
            """
            CREATE TABLE work_times (
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

        # データを新テーブルに移行
        for row in existing_data:
            # 元のデータを取得
            id_val = row[0]
            work_date = row[1]
            start_time = row[2]
            end_time = row[3]
            created_at = row[4]
            updated_at = row[5]
            report_id = row[6]

            # 新しいテーブルには追加のカラムがあるので、それらには空値を設定
            property_id = None
            note = None

            # レポートに紐づく物件IDを取得（可能な場合）
            cursor.execute("SELECT property_id FROM reports WHERE id = ?", (report_id,))
            report_result = cursor.fetchone()
            if report_result:
                property_id = report_result[0]

            # 新テーブルにデータを挿入
            cursor.execute(
                """
                INSERT INTO work_times 
                (id, work_date, start_time, end_time, created_at, updated_at, report_id, property_id, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    id_val,
                    work_date,
                    start_time,
                    end_time,
                    created_at,
                    updated_at,
                    report_id,
                    property_id,
                    note,
                ),
            )

        # 一時テーブルを削除
        cursor.execute("DROP TABLE work_times_backup")

        # 変更を確定
        conn.commit()

        # 更新後のテーブル構造を確認
        cursor.execute("PRAGMA table_info(work_times)")
        columns = cursor.fetchall()
        print("\n更新後のwork_timesテーブル構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        print("\nテーブル構造の更新が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    fix_work_time_table()
