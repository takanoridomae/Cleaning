#!/usr/bin/env python3
"""
全テーブルデータエクスポートスクリプト
データベースの全テーブルをJSONファイルとして一括エクスポート
"""

import sys
import os
import json
from datetime import datetime, date, time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
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


def serialize_datetime(obj):
    """日付・時刻オブジェクトを文字列に変換"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_table_data(model_class, table_name):
    """指定されたテーブルのデータをエクスポート"""
    try:
        print(f"📋 {table_name}テーブルをエクスポート中...")

        # 全データを取得
        records = model_class.query.all()
        data = []

        for record in records:
            # モデルインスタンスを辞書に変換
            record_dict = {}
            for column in record.__table__.columns:
                value = getattr(record, column.name)
                record_dict[column.name] = value
            data.append(record_dict)

        print(f"  ✅ {len(data)}件のデータを取得")
        return data

    except Exception as e:
        print(f"  ❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return []


def export_all_data():
    """全テーブルのデータをエクスポート"""
    app = create_app()

    with app.app_context():
        print("🚀 全テーブルデータエクスポート開始...")

        # エクスポート対象テーブル（依存関係順）
        export_config = [
            (User, "users"),
            (Customer, "customers"),
            (Property, "properties"),
            (Report, "reports"),
            (Photo, "photos"),
            (AirConditioner, "air_conditioners"),
            (WorkTime, "work_times"),
            (WorkDetail, "work_details"),
            (WorkItem, "work_items"),
            (Schedule, "schedules"),
        ]

        all_data = {}
        total_records = 0

        for model_class, table_name in export_config:
            table_data = export_table_data(model_class, table_name)
            all_data[table_name] = table_data
            total_records += len(table_data)

        # ファイル名生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_data_export_{timestamp}.json"

        # JSONファイルに保存
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(
                    all_data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=serialize_datetime,
                )

            # ファイルサイズ取得
            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)

            print(f"\n🎉 エクスポート完了!")
            print(f"📁 ファイル名: {filename}")
            print(f"📊 総レコード数: {total_records}件")
            print(f"💾 ファイルサイズ: {file_size_mb:.2f}MB")

            # テーブル別サマリー
            print(f"\n📋 テーブル別データ数:")
            for table_name, table_data in all_data.items():
                print(f"  • {table_name}: {len(table_data)}件")

            return filename

        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")
            import traceback

            traceback.print_exc()
            return None


if __name__ == "__main__":
    export_file = export_all_data()
    if export_file:
        print(f"\n✅ エクスポートファイル: {export_file}")
        print("📤 このファイルをデプロイ環境にアップロードしてください")
    else:
        print("\n❌ エクスポートに失敗しました")
        sys.exit(1)
