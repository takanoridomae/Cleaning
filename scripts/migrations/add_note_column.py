from app import create_app
import sqlite3
import os

app = create_app()


def add_note_column():
    print("作業時間テーブルにnoteカラムを追加します...")

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
        # カラム情報を取得
        cursor.execute("PRAGMA table_info(work_times)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print("現在のwork_timesテーブル構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # noteカラムの存在確認
        has_note = "note" in column_names

        if has_note:
            print("noteカラムは既に存在しています。")
            return

        # noteカラムを追加
        print("noteカラムを追加します...")
        cursor.execute("ALTER TABLE work_times ADD COLUMN note TEXT")

        # 変更を確定
        conn.commit()

        # 更新後のテーブル構造を確認
        cursor.execute("PRAGMA table_info(work_times)")
        columns = cursor.fetchall()
        print("\n更新後のwork_timesテーブル構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        print("\nnoteカラムの追加が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    add_note_column()
