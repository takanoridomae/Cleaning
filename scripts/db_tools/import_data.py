#!/usr/bin/env python
"""
JSONファイルからデータベースにデータをインポートする
"""
import sys
import os
import json
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


def import_data(json_file):
    """JSONファイルからデータをインポート"""
    app = create_app()

    if not os.path.exists(json_file):
        print(f"ファイルが見つかりません: {json_file}")
        return False

    with app.app_context():
        try:
            # JSONファイルを読み込み
            with open(json_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            print(f"データインポート開始: {json_file}")

            # 既存データを確認
            print("\n=== 既存データ確認 ===")
            print(f"Users: {User.query.count()}件")
            print(f"Customers: {Customer.query.count()}件")
            print(f"Properties: {Property.query.count()}件")
            print(f"Air Conditioners: {AirConditioner.query.count()}件")
            print(f"Reports: {Report.query.count()}件")
            print(f"Photos: {Photo.query.count()}件")
            print(f"Work Times: {WorkTime.query.count()}件")
            print(f"Schedules: {Schedule.query.count()}件")

            # IDマッピング用辞書
            customer_id_map = {}
            property_id_map = {}
            report_id_map = {}
            ac_id_map = {}

            # Usersインポート（adminは除外）
            if "users" in import_data:
                for user_data in import_data["users"]:
                    if user_data["username"] != "admin":  # admin以外のユーザーのみ
                        existing_user = User.query.filter_by(
                            username=user_data["username"]
                        ).first()
                        if not existing_user:
                            user = User(
                                username=user_data["username"],
                                email=user_data["email"],
                                name=user_data["name"],
                                role=user_data["role"],
                                active=user_data["active"],
                                password_hash=user_data["password_hash"],
                                created_at=(
                                    datetime.fromisoformat(user_data["created_at"])
                                    if user_data["created_at"]
                                    else None
                                ),
                                updated_at=(
                                    datetime.fromisoformat(user_data["updated_at"])
                                    if user_data["updated_at"]
                                    else None
                                ),
                            )
                            db.session.add(user)
                print(
                    f"Users: {len([u for u in import_data['users'] if u['username'] != 'admin'])}件をインポート"
                )

            # Customersインポート
            if "customers" in import_data:
                for customer_data in import_data["customers"]:
                    old_id = customer_data["id"]
                    customer = Customer(
                        name=customer_data["name"],
                        company_name=customer_data["company_name"],
                        email=customer_data["email"],
                        phone=customer_data["phone"],
                        postal_code=customer_data["postal_code"],
                        address=customer_data["address"],
                        note=customer_data["note"],
                        created_at=(
                            datetime.fromisoformat(customer_data["created_at"])
                            if customer_data["created_at"]
                            else None
                        ),
                        updated_at=(
                            datetime.fromisoformat(customer_data["updated_at"])
                            if customer_data["updated_at"]
                            else None
                        ),
                    )
                    db.session.add(customer)
                    db.session.flush()  # IDを取得
                    customer_id_map[old_id] = customer.id
                print(f"Customers: {len(import_data['customers'])}件をインポート")

            # Propertiesインポート
            if "properties" in import_data:
                for property_data in import_data["properties"]:
                    old_id = property_data["id"]
                    new_customer_id = customer_id_map.get(property_data["customer_id"])
                    if new_customer_id:
                        property_obj = Property(
                            name=property_data["name"],
                            address=property_data["address"],
                            postal_code=property_data["postal_code"],
                            note=property_data["note"],
                            customer_id=new_customer_id,
                            reception_type=property_data.get("reception_type"),
                            reception_detail=property_data.get("reception_detail"),
                            created_at=(
                                datetime.fromisoformat(property_data["created_at"])
                                if property_data["created_at"]
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(property_data["updated_at"])
                                if property_data["updated_at"]
                                else None
                            ),
                        )
                        db.session.add(property_obj)
                        db.session.flush()  # IDを取得
                        property_id_map[old_id] = property_obj.id
                print(f"Properties: {len(import_data['properties'])}件をインポート")

            # Air Conditionersインポート
            if "air_conditioners" in import_data:
                for ac_data in import_data["air_conditioners"]:
                    old_id = ac_data["id"]
                    new_property_id = property_id_map.get(ac_data["property_id"])
                    if new_property_id:
                        ac = AirConditioner(
                            property_id=new_property_id,
                            ac_type=ac_data["ac_type"],
                            manufacturer=ac_data["manufacturer"],
                            model_number=ac_data["model_number"],
                            location=ac_data["location"],
                            quantity=ac_data["quantity"],
                            unit_price=ac_data["unit_price"],
                            total_amount=ac_data["total_amount"],
                            cleaning_type=ac_data["cleaning_type"],
                            note=ac_data["note"],
                            created_at=(
                                datetime.fromisoformat(ac_data["created_at"])
                                if ac_data["created_at"]
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(ac_data["updated_at"])
                                if ac_data["updated_at"]
                                else None
                            ),
                        )
                        db.session.add(ac)
                        db.session.flush()  # IDを取得
                        ac_id_map[old_id] = ac.id
                print(
                    f"Air Conditioners: {len(import_data['air_conditioners'])}件をインポート"
                )

            # Reportsインポート
            if "reports" in import_data:
                for report_data in import_data["reports"]:
                    old_id = report_data["id"]
                    new_property_id = property_id_map.get(report_data["property_id"])
                    if new_property_id:
                        report = Report(
                            property_id=new_property_id,
                            work_date=(
                                datetime.fromisoformat(report_data["work_date"]).date()
                                if report_data["work_date"]
                                else None
                            ),
                            staff_name=report_data["staff_name"],
                            start_time=(
                                datetime.fromisoformat(report_data["start_time"])
                                if report_data["start_time"]
                                else None
                            ),
                            end_time=(
                                datetime.fromisoformat(report_data["end_time"])
                                if report_data["end_time"]
                                else None
                            ),
                            total_amount=report_data["total_amount"],
                            note=report_data["note"],
                            order_detail=report_data["order_detail"],
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
                print(f"Reports: {len(import_data['reports'])}件をインポート")

            # Work Timesインポート
            if "work_times" in import_data:
                for wt_data in import_data["work_times"]:
                    new_report_id = report_id_map.get(wt_data["report_id"])
                    if new_report_id:
                        work_time = WorkTime(
                            report_id=new_report_id,
                            start_time=(
                                datetime.fromisoformat(wt_data["start_time"])
                                if wt_data["start_time"]
                                else None
                            ),
                            end_time=(
                                datetime.fromisoformat(wt_data["end_time"])
                                if wt_data["end_time"]
                                else None
                            ),
                            break_time_minutes=wt_data["break_time_minutes"],
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

            # Schedulesインポート
            if "schedules" in import_data:
                for schedule_data in import_data["schedules"]:
                    new_property_id = property_id_map.get(schedule_data["property_id"])
                    new_report_id = (
                        report_id_map.get(schedule_data["report_id"])
                        if schedule_data["report_id"]
                        else None
                    )
                    if new_property_id:
                        schedule = Schedule(
                            property_id=new_property_id,
                            report_id=new_report_id,
                            scheduled_date=(
                                datetime.fromisoformat(
                                    schedule_data["scheduled_date"]
                                ).date()
                                if schedule_data["scheduled_date"]
                                else None
                            ),
                            scheduled_time=schedule_data["scheduled_time"],
                            status=schedule_data["status"],
                            staff_name=schedule_data["staff_name"],
                            note=schedule_data["note"],
                            created_at=(
                                datetime.fromisoformat(schedule_data["created_at"])
                                if schedule_data["created_at"]
                                else None
                            ),
                            updated_at=(
                                datetime.fromisoformat(schedule_data["updated_at"])
                                if schedule_data["updated_at"]
                                else None
                            ),
                        )
                        db.session.add(schedule)
                print(f"Schedules: {len(import_data['schedules'])}件をインポート")

            # 写真情報（ファイルは移行されないため、情報のみ）
            if "photos" in import_data:
                print(
                    f"Photos: {len(import_data['photos'])}件の情報がありますが、ファイルは手動で移行が必要です"
                )

            # コミット
            db.session.commit()

            print("\n=== インポート後データ確認 ===")
            print(f"Users: {User.query.count()}件")
            print(f"Customers: {Customer.query.count()}件")
            print(f"Properties: {Property.query.count()}件")
            print(f"Air Conditioners: {AirConditioner.query.count()}件")
            print(f"Reports: {Report.query.count()}件")
            print(f"Photos: {Photo.query.count()}件")
            print(f"Work Times: {WorkTime.query.count()}件")
            print(f"Schedules: {Schedule.query.count()}件")

            print(f"\nデータインポート完了!")
            return True

        except Exception as e:
            print(f"インポートエラー: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python import_data.py <json_file>")
    else:
        import_data(sys.argv[1])
