from app import create_app, db
import sqlite3
import os

app = create_app()


def add_work_time_note_field():
    print("作業時間テーブルに備考フィールドを追加します...")

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
        # work_timesテーブルの構造を確認
        cursor.execute("PRAGMA table_info(work_times)")
        columns = cursor.fetchall()
        print("現在のwork_timesテーブルの構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # note列が既に存在するかチェック
        note_exists = any(col[1] == "note" for col in columns)

        if note_exists:
            print("note列は既に存在しています。")
        else:
            # note列を追加
            cursor.execute("ALTER TABLE work_times ADD COLUMN note TEXT")
            print("note列を追加しました。")

        # 変更を保存
        conn.commit()
        print("データベースの更新が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    add_work_time_note_field()
