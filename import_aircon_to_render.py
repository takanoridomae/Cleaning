#!/usr/bin/env python3
"""
Renderサーバー上でair_conditionersデータをインポートするスクリプト
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app import create_app, db
from app.models.air_conditioner import AirConditioner


def import_aircon_data():
    app = create_app()

    # JSONデータを読み込み
    with open("aircon_export_20250628_210003.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        try:
            # 既存データの確認
            existing_count = AirConditioner.query.count()
            print(f"既存のair_conditionersレコード数: {existing_count}")

            imported_count = 0
            updated_count = 0

            for item in data:
                # IDを除いてデータを準備
                item_data = {k: v for k, v in item.items() if k != "id"}

                # 既存レコードを確認（property_id, manufacturer, model_numberで判定）
                existing = AirConditioner.query.filter_by(
                    property_id=item_data.get("property_id"),
                    manufacturer=item_data.get("manufacturer"),
                    model_number=item_data.get("model_number"),
                ).first()

                if existing:
                    # 既存レコードを更新
                    for key, value in item_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_count += 1
                    print(
                        f"更新: ID {existing.id} - {existing.manufacturer} {existing.model_number}"
                    )
                else:
                    # 新規レコードを作成
                    new_aircon = AirConditioner(**item_data)
                    db.session.add(new_aircon)
                    imported_count += 1
                    print(f"追加: {new_aircon.manufacturer} {new_aircon.model_number}")

            # データベースに保存
            db.session.commit()

            print(f"\nインポート完了:")
            print(f"  新規追加: {imported_count}件")
            print(f"  更新: {updated_count}件")
            print(f"  総処理件数: {len(data)}件")

            # 最終的なレコード数を確認
            final_count = AirConditioner.query.count()
            print(f"\n最終的なair_conditionersレコード数: {final_count}")

        except Exception as e:
            db.session.rollback()
            print(f"インポートエラー: {e}")
            raise


if __name__ == "__main__":
    import_aircon_data()
