#!/usr/bin/env python
"""
報告書データをRender環境にインポートする
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.report import Report
from app.models.photo import Photo
from app.models.work_time import WorkTime
from app.models.property import Property


def import_reports_to_render(json_file):
    """報告書データをRender環境にインポート"""
    app = create_app()

    if not os.path.exists(json_file):
        print(f"ファイルが見つかりません: {json_file}")
        return False

    with app.app_context():
        try:
            # JSONファイルを読み込み
            with open(json_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            print(f"報告書データインポート開始: {json_file}")

            # 既存データを確認
            print("\n=== Render環境の既存報告書データ確認 ===")
            print(f"Reports: {Report.query.count()}件")
            print(f"Photos: {Photo.query.count()}件")
            print(f"Work Times: {WorkTime.query.count()}件")

            # 物件IDマッピング用辞書（既存物件から新しい物件IDを取得）
            property_mapping = {}
            if "reports" in import_data:
                # 既存の物件データから、元のIDと新しいIDのマッピングを作成
                existing_properties = Property.query.all()
                for prop in existing_properties:
                    # 名前と住所で物件を特定してマッピング
                    property_mapping[prop.id] = prop.id  # 一旦同じIDでマッピング

            # IDマッピング用辞書
            report_id_map = {}

            # Reportsインポート
            if "reports" in import_data:
                for report_data in import_data["reports"]:
                    old_id = report_data["id"]
                    property_id = report_data["property_id"]

                    # 物件IDが存在するかチェック
                    existing_property = Property.query.get(property_id)
                    if existing_property:
                        report = Report(
                            property_id=property_id,
                            title=report_data["title"],
                            date=(
                                datetime.fromisoformat(report_data["date"]).date()
                                if report_data["date"]
                                else None
                            ),
                            work_address=report_data["work_address"],
                            technician=report_data["technician"],
                            status=report_data["status"],
                            work_description=report_data["work_description"],
                            note=report_data["note"],
                            created_at=(
                                datetime.fromisoformat(report_data["created_at"])
                                if report_data["created_at"]
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(report_data["updated_at"])
                                if report_data["updated_at"]
                                else None
                            ),
                        )
                        db.session.add(report)
                        db.session.flush()  # IDを取得
                        report_id_map[old_id] = report.id
                    else:
                        print(
                            f"警告: 物件ID {property_id} が見つかりません。報告書ID {old_id} をスキップします。"
                        )

                print(f"Reports: {len(import_data['reports'])}件をインポート")

            # Work Timesインポート
            if "work_times" in import_data:
                for wt_data in import_data["work_times"]:
                    new_report_id = report_id_map.get(wt_data["report_id"])
                    property_id = wt_data["property_id"]

                    if new_report_id and Property.query.get(property_id):
                        work_time = WorkTime(
                            report_id=new_report_id,
                            property_id=property_id,
                            work_date=(
                                datetime.fromisoformat(wt_data["work_date"]).date()
                                if wt_data["work_date"]
                                else None
                            ),
                            start_time=(
                                datetime.fromisoformat(wt_data["start_time"]).time()
                                if wt_data["start_time"]
                                else None
                            ),
                            end_time=(
                                datetime.fromisoformat(wt_data["end_time"]).time()
                                if wt_data["end_time"]
                                else None
                            ),
                            note=wt_data["note"],
                            created_at=(
                                datetime.fromisoformat(wt_data["created_at"])
                                if wt_data["created_at"]
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(wt_data["updated_at"])
                                if wt_data["updated_at"]
                                else None
                            ),
                        )
                        db.session.add(work_time)

                print(f"Work Times: {len(import_data['work_times'])}件をインポート")

            # 写真情報（ファイルは移行されないため、情報のみ）
            if "photos" in import_data:
                for photo_data in import_data["photos"]:
                    new_report_id = report_id_map.get(photo_data["report_id"])

                    if new_report_id:
                        photo = Photo(
                            report_id=new_report_id,
                            air_conditioner_id=photo_data.get("air_conditioner_id"),
                            photo_type=photo_data["photo_type"],
                            filename=photo_data["filename"],
                            created_at=(
                                datetime.fromisoformat(photo_data["created_at"])
                                if photo_data["created_at"]
                                else None
                            ),
                        )
                        # filepathがある場合は設定
                        if "filepath" in photo_data and photo_data["filepath"]:
                            if hasattr(photo, "filepath"):
                                photo.filepath = photo_data["filepath"]

                        db.session.add(photo)

                print(
                    f"Photos: {len(import_data['photos'])}件の情報をインポート（ファイルは手動移行が必要）"
                )

            # コミット
            db.session.commit()

            print("\n=== 報告書インポート後データ確認 ===")
            print(f"Reports: {Report.query.count()}件")
            print(f"Photos: {Photo.query.count()}件")
            print(f"Work Times: {WorkTime.query.count()}件")

            print(f"\n報告書データインポート完了!")
            print("注意: 写真ファイルは別途手動でアップロードが必要です")
            return True

        except Exception as e:
            print(f"報告書インポートエラー: {e}")
            import traceback

            traceback.print_exc()
            db.session.rollback()
            return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python import_reports.py <json_file>")
        print("例: python import_reports.py reports_export_20250624_191211.json")
    else:
        import_reports_to_render(sys.argv[1])
