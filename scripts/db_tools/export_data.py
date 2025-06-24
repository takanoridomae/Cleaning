#!/usr/bin/env python
"""
ローカルデータベースのデータをJSONファイルにエクスポートする
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

# プロジェクトルートを追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app import create_app, db
from app.models.user import User
from app.models.customer import Customer
from app.models.property import Property
from app.models.report import Report
from app.models.photo import Photo
from app.models.air_conditioner import AirConditioner
from app.models.schedule import Schedule
from app.models.work_time import WorkTime
from app.models.work_item import WorkItem
from app.models.work_detail import WorkDetail


def export_data():
    """データベースの全データをJSONにエクスポート"""
    app = create_app()

    with app.app_context():
        export_data = {}

        try:
            # Users
            users = User.query.all()
            export_data["users"] = []
            for user in users:
                export_data["users"].append(
                    {
                        "username": user.username,
                        "email": user.email,
                        "name": user.name,
                        "role": user.role,
                        "active": user.active,
                        "password_hash": user.password_hash,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "updated_at": (
                            user.updated_at.isoformat() if user.updated_at else None
                        ),
                    }
                )
            print(f"Users: {len(export_data['users'])}件")

            # Customers
            customers = Customer.query.all()
            export_data["customers"] = []
            for customer in customers:
                export_data["customers"].append(
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "company_name": customer.company_name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "postal_code": customer.postal_code,
                        "address": customer.address,
                        "note": customer.note,
                        "created_at": (
                            customer.created_at.isoformat()
                            if customer.created_at
                            else None
                        ),
                        "updated_at": (
                            customer.updated_at.isoformat()
                            if customer.updated_at
                            else None
                        ),
                    }
                )
            print(f"Customers: {len(export_data['customers'])}件")

            # Properties
            properties = Property.query.all()
            export_data["properties"] = []
            for prop in properties:
                export_data["properties"].append(
                    {
                        "id": prop.id,
                        "name": prop.name,
                        "address": prop.address,
                        "postal_code": prop.postal_code,
                        "note": prop.note,
                        "customer_id": prop.customer_id,
                        "reception_type": prop.reception_type,
                        "reception_detail": prop.reception_detail,
                        "created_at": (
                            prop.created_at.isoformat() if prop.created_at else None
                        ),
                        "updated_at": (
                            prop.updated_at.isoformat() if prop.updated_at else None
                        ),
                    }
                )
            print(f"Properties: {len(export_data['properties'])}件")

            # Air Conditioners
            air_conditioners = AirConditioner.query.all()
            export_data["air_conditioners"] = []
            for ac in air_conditioners:
                export_data["air_conditioners"].append(
                    {
                        "id": ac.id,
                        "property_id": ac.property_id,
                        "ac_type": ac.ac_type,
                        "manufacturer": ac.manufacturer,
                        "model_number": ac.model_number,
                        "location": ac.location,
                        "quantity": ac.quantity,
                        "unit_price": ac.unit_price,
                        "total_amount": ac.total_amount,
                        "cleaning_type": ac.cleaning_type,
                        "note": ac.note,
                        "created_at": (
                            ac.created_at.isoformat() if ac.created_at else None
                        ),
                        "updated_at": (
                            ac.updated_at.isoformat() if ac.updated_at else None
                        ),
                    }
                )
            print(f"Air Conditioners: {len(export_data['air_conditioners'])}件")

            # Reports
            reports = Report.query.all()
            export_data["reports"] = []
            for report in reports:
                export_data["reports"].append(
                    {
                        "id": report.id,
                        "property_id": report.property_id,
                        "title": report.title,
                        "date": (report.date.isoformat() if report.date else None),
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
                        "air_conditioner_id": photo.air_conditioner_id,
                        "photo_type": photo.photo_type,
                        "filename": photo.filename,
                        "filepath": photo.filepath,
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
                        "work_date": (
                            wt.work_date.isoformat() if wt.work_date else None
                        ),
                        "start_time": (
                            wt.start_time.isoformat() if wt.start_time else None
                        ),
                        "end_time": wt.end_time.isoformat() if wt.end_time else None,
                        "property_id": wt.property_id,
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

            # Schedules
            schedules = Schedule.query.all()
            export_data["schedules"] = []
            for schedule in schedules:
                export_data["schedules"].append(
                    {
                        "id": schedule.id,
                        "property_id": schedule.property_id,
                        "report_id": schedule.report_id,
                        "scheduled_date": (
                            schedule.scheduled_date.isoformat()
                            if schedule.scheduled_date
                            else None
                        ),
                        "scheduled_time": schedule.scheduled_time,
                        "status": schedule.status,
                        "staff_name": schedule.staff_name,
                        "note": schedule.note,
                        "created_at": (
                            schedule.created_at.isoformat()
                            if schedule.created_at
                            else None
                        ),
                        "updated_at": (
                            schedule.updated_at.isoformat()
                            if schedule.updated_at
                            else None
                        ),
                    }
                )
            print(f"Schedules: {len(export_data['schedules'])}件")

            # エクスポートファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"db_export_{timestamp}.json"

            # JSONファイルに保存
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"\nデータエクスポート完了: {export_file}")
            print(f"ファイルサイズ: {os.path.getsize(export_file)} bytes")

            return export_file

        except Exception as e:
            print(f"エクスポートエラー: {e}")
            return None


if __name__ == "__main__":
    export_data()
