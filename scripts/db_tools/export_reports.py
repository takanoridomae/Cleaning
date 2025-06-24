#!/usr/bin/env python
"""
報告書データをJSONファイルにエクスポートする
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app import create_app, db
from app.models.report import Report
from app.models.photo import Photo
from app.models.work_time import WorkTime


def export_reports():
    """報告書データをエクスポート"""
    app = create_app()

    with app.app_context():
        export_data = {}

        try:
            # Reports
            reports = Report.query.all()
            export_data["reports"] = []
            for report in reports:
                export_data["reports"].append(
                    {
                        "id": report.id,
                        "property_id": report.property_id,
                        "title": report.title,
                        "date": report.date.isoformat() if report.date else None,
                        "work_address": report.work_address,
                        "technician": report.technician,
                        "status": report.status,
                        "work_description": report.work_description,
                        "note": report.note,
                        "created_at": (
                            report.created_at.isoformat() if report.created_at else None
                        ),
                        "updated_at": (
                            report.updated_at.isoformat() if report.updated_at else None
                        ),
                    }
                )
            print(f"Reports: {len(export_data['reports'])}件")

            # Photos
            photos = Photo.query.all()
            export_data["photos"] = []
            for photo in photos:
                export_data["photos"].append(
                    {
                        "id": photo.id,
                        "report_id": photo.report_id,
                        "air_conditioner_id": getattr(
                            photo, "air_conditioner_id", None
                        ),
                        "photo_type": photo.photo_type,
                        "filename": photo.filename,
                        "filepath": getattr(photo, "filepath", None),
                        "created_at": (
                            photo.created_at.isoformat() if photo.created_at else None
                        ),
                    }
                )
            print(f"Photos: {len(export_data['photos'])}件")

            # Work Times
            work_times = WorkTime.query.all()
            export_data["work_times"] = []
            for wt in work_times:
                export_data["work_times"].append(
                    {
                        "id": wt.id,
                        "report_id": wt.report_id,
                        "property_id": wt.property_id,
                        "work_date": wt.work_date.isoformat() if wt.work_date else None,
                        "start_time": (
                            wt.start_time.isoformat() if wt.start_time else None
                        ),
                        "end_time": wt.end_time.isoformat() if wt.end_time else None,
                        "note": wt.note,
                        "created_at": (
                            wt.created_at.isoformat() if wt.created_at else None
                        ),
                        "updated_at": (
                            wt.updated_at.isoformat() if wt.updated_at else None
                        ),
                    }
                )
            print(f"Work Times: {len(export_data['work_times'])}件")

            # エクスポートファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"reports_export_{timestamp}.json"

            # JSONファイルに保存
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"\n報告書データエクスポート完了: {export_file}")
            print(f"ファイルサイズ: {os.path.getsize(export_file)} bytes")

            # データ統計
            print(f"\n=== エクスポートデータ統計 ===")
            print(f"報告書: {len(export_data['reports'])}件")
            print(f"写真: {len(export_data['photos'])}件")
            print(f"作業時間: {len(export_data['work_times'])}件")

            return export_file

        except Exception as e:
            print(f"エクスポートエラー: {e}")
            import traceback

            traceback.print_exc()
            return None


if __name__ == "__main__":
    export_reports()
