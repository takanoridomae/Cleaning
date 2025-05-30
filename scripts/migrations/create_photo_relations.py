from app import create_app, db
import sqlite3
import os

app = create_app()


def add_columns_to_photos():
    """photosテーブルにair_conditioner_idとwork_item_idカラムを追加"""
    with app.app_context():
        conn = sqlite3.connect("instance/aircon_report.db")
        cursor = conn.cursor()

        # カラムが存在するか確認
        columns = cursor.execute("PRAGMA table_info(photos)").fetchall()
        column_names = [col[1] for col in columns]

        print(f"現在のphotosテーブルのカラム: {column_names}")

        # work_item_idカラムがなければ追加
        if "work_item_id" not in column_names:
            try:
                # SQLite3のALTER TABLEでFOREIGN KEYを指定することはできないのでただの INTEGER に
                cursor.execute("ALTER TABLE photos ADD COLUMN work_item_id INTEGER")
                print("work_item_idカラムを追加しました")
            except sqlite3.OperationalError as e:
                print(f"work_item_idカラム追加エラー: {e}")
        else:
            print("work_item_idカラムは既に存在します")

        conn.commit()
        conn.close()

        print("photosテーブルの更新が完了しました")


if __name__ == "__main__":
    add_columns_to_photos()
