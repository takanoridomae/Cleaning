#!/usr/bin/env python3
"""
日付変換処理のテストスクリプト
"""

import json
from datetime import datetime


def test_date_conversion():
    """日付変換のテスト"""

    # サンプルデータ（エクスポートファイルと同じ形式）
    sample_data = [
        {
            "id": 1,
            "property_id": 1,
            "manufacturer": "ダイキン",
            "model_number": "AN22XRS-W",
            "created_at": "2025-05-15 11:17:20.850729",
            "updated_at": "2025-05-15 11:17:20.850729",
        }
    ]

    print("🔍 日付変換テスト開始...")

    for i, item in enumerate(sample_data):
        try:
            # IDを除いてデータを準備
            item_data = {k: v for k, v in item.items() if k != "id"}

            print(f"\n📝 アイテム {i}:")
            print(f"  変換前: {item_data}")

            # 日付フィールドの変換（デプロイ環境対応）
            for date_field in ["created_at", "updated_at"]:
                if date_field in item_data and item_data[date_field]:
                    original_value = item_data[date_field]
                    try:
                        if isinstance(item_data[date_field], str):
                            # 文字列から日付オブジェクトに変換
                            item_data[date_field] = datetime.fromisoformat(
                                item_data[date_field].replace("Z", "+00:00")
                            )
                            print(
                                f"  ✅ {date_field}: '{original_value}' → {item_data[date_field]} ({type(item_data[date_field])})"
                            )
                    except (ValueError, AttributeError) as e:
                        print(f"  ⚠️ 日付変換エラー {date_field}: {e}")
                        # 現在の日時を設定
                        item_data[date_field] = datetime.now()
                        print(
                            f"  🔄 {date_field}: '{original_value}' → {item_data[date_field]} (現在時刻で置換)"
                        )

            print(f"  変換後: {item_data}")

        except Exception as e:
            print(f"  ❌ 処理エラー: {e}")

    print("\n✅ 日付変換テスト完了")


if __name__ == "__main__":
    test_date_conversion()
