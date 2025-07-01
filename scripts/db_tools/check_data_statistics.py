#!/usr/bin/env python3
"""
データベースエクスポート画面のデータ統計取得機能の動作確認スクリプト
"""

import sys
import os

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app import create_app


def test_data_statistics():
    """データ統計取得機能のテスト"""
    app = create_app()

    with app.app_context():
        print("🔍 データ統計取得テスト開始...")

        try:
            # モデルのインポート
            from app.models.user import User
            from app.models.customer import Customer
            from app.models.property import Property
            from app.models.report import Report
            from app.models.photo import Photo
            from app.models.air_conditioner import AirConditioner
            from app.models.work_time import WorkTime
            from app.models.work_detail import WorkDetail
            from app.models.work_item import WorkItem
            from app.models.schedule import Schedule

            print("✅ モデルインポート完了")

            # 各テーブルのカウントを個別に取得
            table_counts = {}

            tables_to_test = [
                ("users", User),
                ("customers", Customer),
                ("properties", Property),
                ("reports", Report),
                ("photos", Photo),
                ("air_conditioners", AirConditioner),
                ("work_times", WorkTime),
                ("work_details", WorkDetail),
                ("work_items", WorkItem),
                ("schedules", Schedule),
            ]

            for table_name, model_class in tables_to_test:
                try:
                    count = model_class.query.count()
                    table_counts[table_name] = count
                    print(f"  ✅ {table_name}: {count}件")
                except Exception as e:
                    print(f"  ❌ {table_name}取得エラー: {e}")
                    table_counts[table_name] = "エラー"

            total_records = sum(
                count for count in table_counts.values() if isinstance(count, int)
            )
            print(f"\n🎉 データ統計取得完了: 総計{total_records}件")

            # 結果の詳細表示
            print("\n📊 詳細結果:")
            for table_name, count in table_counts.items():
                status = "✅" if isinstance(count, int) else "❌"
                print(f"  {status} {table_name}: {count}")

            return table_counts

        except Exception as e:
            print(f"⚠️ 全体エラー: {e}")
            import traceback

            traceback.print_exc()
            return {}


if __name__ == "__main__":
    test_data_statistics()
