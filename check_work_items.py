#!/usr/bin/env python3
from app import create_app, db


def check_work_items_table():
    app = create_app()
    with app.app_context():
        # work_itemsテーブルの構造を確認
        with db.engine.connect() as connection:
            result = connection.execute(db.text("PRAGMA table_info(work_items)"))
            print("work_itemsテーブル構造:")
            for row in result:
                print(f"{row[0]}: {row[1]} ({row[2]}) {row[3]} {row[4]}")

            # 既存データの確認
            result = connection.execute(db.text("SELECT * FROM work_items LIMIT 5"))
            print("\nwork_itemsテーブルの既存データ:")
            for row in result:
                print(row)


if __name__ == "__main__":
    check_work_items_table()
