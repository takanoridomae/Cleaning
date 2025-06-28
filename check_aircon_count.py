#!/usr/bin/env python3
"""
現在のエアコン登録数を確認するスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.air_conditioner import AirConditioner
from sqlalchemy import func


def check_aircon_data():
    """エアコンデータの現在の状況を確認"""
    app = create_app()

    with app.app_context():
        try:
            # 総数を取得
            total_count = AirConditioner.query.count()
            print(f"🔢 現在のエアコン登録数: {total_count}件")

            if total_count > 0:
                # メーカー別内訳
                print("\n📊 メーカー別内訳:")
                manufacturer_stats = (
                    db.session.query(
                        AirConditioner.manufacturer, func.count(AirConditioner.id)
                    )
                    .group_by(AirConditioner.manufacturer)
                    .all()
                )

                for manufacturer, count in manufacturer_stats:
                    print(f"  • {manufacturer}: {count}件")

                # 最新の5件を表示
                print("\n📋 最新登録の5件:")
                recent_aircons = (
                    AirConditioner.query.order_by(AirConditioner.id.desc())
                    .limit(5)
                    .all()
                )

                for aircon in recent_aircons:
                    print(
                        f"  • ID:{aircon.id} - {aircon.manufacturer} {aircon.model_number} (物件ID:{aircon.property_id})"
                    )

            else:
                print("⚠️ エアコンデータが登録されていません")

        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            return False

    return True


if __name__ == "__main__":
    print("🔍 エアコンデータ確認を開始...")
    success = check_aircon_data()

    if success:
        print("\n✅ 確認完了")
    else:
        print("\n❌ 確認に失敗しました")
        sys.exit(1)
