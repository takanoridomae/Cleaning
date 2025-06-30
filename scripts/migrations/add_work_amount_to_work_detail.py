#!/usr/bin/env python3
"""
作業詳細 (work_details) テーブルに作業金額フィールドを追加するマイグレーション
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db


def add_work_amount_column():
    """work_detailsテーブルに作業金額フィールドを追加"""

    app = create_app()
    with app.app_context():
        try:
            print("=== work_detailsテーブルに作業金額フィールドを追加 ===")

            # 現在のテーブル構造を表示
            with db.engine.connect() as connection:
                result = connection.execute(db.text("PRAGMA table_info(work_details)"))
                print("現在のwork_detailsテーブル構造:")
                columns = []
                for row in result:
                    columns.append(row[1])
                    print(f"  {row[0]}: {row[1]} ({row[2]})")

                # work_amountカラムが既に存在するかチェック
                if "work_amount" in columns:
                    print("work_amountカラムは既に存在します")
                    return False

                print("\nwork_amountカラムを追加中...")

                # work_amountカラムを追加（デフォルト値0）
                connection.execute(
                    db.text(
                        "ALTER TABLE work_details ADD COLUMN work_amount INTEGER DEFAULT 0"
                    )
                )

                # 変更をコミット
                connection.commit()

                print("work_amountカラムの追加が完了しました")

                # 追加後のテーブル構造を確認
                result = connection.execute(db.text("PRAGMA table_info(work_details)"))
                print("\n追加後のwork_detailsテーブル構造:")
                for row in result:
                    print(f"  {row[0]}: {row[1]} ({row[2]})")

                return True

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return False


def main():
    """メイン実行関数"""
    success = add_work_amount_column()
    if success:
        print("\n✅ マイグレーションが正常に完了しました")
    else:
        print("\n❌ マイグレーションが失敗しました")


if __name__ == "__main__":
    main()
