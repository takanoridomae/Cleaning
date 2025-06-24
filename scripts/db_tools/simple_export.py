#!/usr/bin/env python
"""
ローカルデータベースの主要データをJSONファイルにエクスポートする（簡易版）
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
from app.models.air_conditioner import AirConditioner


def simple_export():
    """主要データのみをエクスポート"""
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
                        "reception_type": getattr(prop, "reception_type", None),
                        "reception_detail": getattr(prop, "reception_detail", None),
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

            # エクスポートファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"simple_export_{timestamp}.json"

            # JSONファイルに保存
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"\n簡易データエクスポート完了: {export_file}")
            print(f"ファイルサイズ: {os.path.getsize(export_file)} bytes")

            # データ統計
            print(f"\n=== エクスポートデータ統計 ===")
            print(f"ユーザー: {len(export_data['users'])}件")
            print(f"顧客: {len(export_data['customers'])}件")
            print(f"物件: {len(export_data['properties'])}件")
            print(f"エアコン: {len(export_data['air_conditioners'])}件")

            return export_file

        except Exception as e:
            print(f"エクスポートエラー: {e}")
            return None


if __name__ == "__main__":
    simple_export()
