#!/usr/bin/env python3
"""
重複データ削除スクリプト
安全に重複レコードを削除し、データ整合性を保持します
"""

import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app import create_app, db
from app.models.customer import Customer
from app.models.property import Property
from app.models.air_conditioner import AirConditioner
from app.models.report import Report
from app.models.photo import Photo
from app.models.work_time import WorkTime
from sqlalchemy import func, and_
from datetime import datetime


def remove_duplicate_customers():
    """重複顧客の削除"""
    print("=== 顧客の重複削除開始 ===")

    # 名前とメールアドレスが同じ重複顧客を特定
    duplicates = (
        db.session.query(
            Customer.name, Customer.email, func.count(Customer.id).label("count")
        )
        .group_by(Customer.name, Customer.email)
        .having(func.count(Customer.id) > 1)
        .all()
    )

    removed_count = 0
    for duplicate in duplicates:
        print(
            f"重複顧客発見: {duplicate.name} ({duplicate.email}) - {duplicate.count}件"
        )

        # 同じ名前・メールアドレスの顧客を取得
        customers = (
            Customer.query.filter_by(name=duplicate.name, email=duplicate.email)
            .order_by(Customer.id)
            .all()
        )

        # 最初の1件を残して削除
        for customer in customers[1:]:
            print(f"  削除: ID {customer.id}")

            # 関連データの移行
            # 物件を最初の顧客に移行
            Property.query.filter_by(customer_id=customer.id).update(
                {"customer_id": customers[0].id}
            )

            # 顧客を削除
            db.session.delete(customer)
            removed_count += 1

    db.session.commit()
    print(f"重複顧客削除完了: {removed_count}件削除")
    return removed_count


def remove_duplicate_properties():
    """重複物件の削除"""
    print("\n=== 物件の重複削除開始 ===")

    # 住所が同じ重複物件を特定
    duplicates = (
        db.session.query(Property.address, func.count(Property.id).label("count"))
        .group_by(Property.address)
        .having(func.count(Property.id) > 1)
        .all()
    )

    removed_count = 0
    for duplicate in duplicates:
        print(f"重複物件発見: {duplicate.address} - {duplicate.count}件")

        # 同じ住所の物件を取得
        properties = (
            Property.query.filter_by(address=duplicate.address)
            .order_by(Property.id)
            .all()
        )

        # 最初の1件を残して削除
        for prop in properties[1:]:
            print(f"  削除: ID {prop.id} ({prop.address})")

            # 関連データの移行
            # エアコンを最初の物件に移行
            AirConditioner.query.filter_by(property_id=prop.id).update(
                {"property_id": properties[0].id}
            )

            # 物件を削除
            db.session.delete(prop)
            removed_count += 1

    db.session.commit()
    print(f"重複物件削除完了: {removed_count}件削除")
    return removed_count


def remove_duplicate_airconditioners():
    """重複エアコンの削除"""
    print("\n=== エアコンの重複削除開始 ===")

    # 物件ID、メーカー、機種が同じ重複エアコンを特定
    duplicates = (
        db.session.query(
            AirConditioner.property_id,
            AirConditioner.manufacturer,
            AirConditioner.model_number,
            func.count(AirConditioner.id).label("count"),
        )
        .group_by(
            AirConditioner.property_id,
            AirConditioner.manufacturer,
            AirConditioner.model_number,
        )
        .having(func.count(AirConditioner.id) > 1)
        .all()
    )

    removed_count = 0
    for duplicate in duplicates:
        print(
            f"重複エアコン発見: 物件{duplicate.property_id} {duplicate.manufacturer} {duplicate.model_number} - {duplicate.count}件"
        )

        # 同じ仕様のエアコンを取得
        airconditioners = (
            AirConditioner.query.filter_by(
                property_id=duplicate.property_id,
                manufacturer=duplicate.manufacturer,
                model_number=duplicate.model_number,
            )
            .order_by(AirConditioner.id)
            .all()
        )

        # 最初の1件を残して削除
        for ac in airconditioners[1:]:
            print(f"  削除: ID {ac.id}")

            # 関連データの移行
            # 報告書を最初のエアコンに移行
            Report.query.filter_by(air_conditioner_id=ac.id).update(
                {"air_conditioner_id": airconditioners[0].id}
            )

            # エアコンを削除
            db.session.delete(ac)
            removed_count += 1

    db.session.commit()
    print(f"重複エアコン削除完了: {removed_count}件削除")
    return removed_count


def remove_duplicate_reports():
    """重複報告書の削除"""
    print("\n=== 報告書の重複削除開始 ===")

    # エアコンID、作業日が同じ重複報告書を特定
    duplicates = (
        db.session.query(
            Report.air_conditioner_id,
            func.date(Report.work_date).label("work_date"),
            func.count(Report.id).label("count"),
        )
        .group_by(Report.air_conditioner_id, func.date(Report.work_date))
        .having(func.count(Report.id) > 1)
        .all()
    )

    removed_count = 0
    for duplicate in duplicates:
        print(
            f"重複報告書発見: エアコン{duplicate.air_conditioner_id} {duplicate.work_date} - {duplicate.count}件"
        )

        # 同じエアコン・日付の報告書を取得
        reports = (
            Report.query.filter(
                and_(
                    Report.air_conditioner_id == duplicate.air_conditioner_id,
                    func.date(Report.work_date) == duplicate.work_date,
                )
            )
            .order_by(Report.id)
            .all()
        )

        # 最初の1件を残して削除
        for report in reports[1:]:
            print(f"  削除: ID {report.id}")

            # 関連データの削除
            # 写真データの削除
            Photo.query.filter_by(report_id=report.id).delete()

            # 作業時間データの削除
            WorkTime.query.filter_by(report_id=report.id).delete()

            # 報告書を削除
            db.session.delete(report)
            removed_count += 1

    db.session.commit()
    print(f"重複報告書削除完了: {removed_count}件削除")
    return removed_count


def show_final_statistics():
    """最終統計の表示"""
    print("\n=== 重複削除後の最終統計 ===")
    customer_count = Customer.query.count()
    property_count = Property.query.count()
    ac_count = AirConditioner.query.count()
    report_count = Report.query.count()

    print(f"顧客数: {customer_count}")
    print(f"物件数: {property_count}")
    print(f"エアコン数: {ac_count}")
    print(f"報告書数: {report_count}")

    return customer_count, property_count, ac_count, report_count


def main():
    """メイン処理"""
    app = create_app()

    with app.app_context():
        print("重複データ削除処理を開始します...")
        print(f"開始時刻: {datetime.now()}")

        # 処理前の状態確認
        print("\n=== 処理前の状態 ===")
        initial_customers = Customer.query.count()
        initial_properties = Property.query.count()
        initial_acs = AirConditioner.query.count()
        initial_reports = Report.query.count()

        print(f"顧客数: {initial_customers}")
        print(f"物件数: {initial_properties}")
        print(f"エアコン数: {initial_acs}")
        print(f"報告書数: {initial_reports}")

        # 重複削除処理
        removed_customers = remove_duplicate_customers()
        removed_properties = remove_duplicate_properties()
        removed_acs = remove_duplicate_airconditioners()
        removed_reports = remove_duplicate_reports()

        # 最終結果
        final_customers, final_properties, final_acs, final_reports = (
            show_final_statistics()
        )

        print("\n=== 削除サマリー ===")
        print(f"削除された顧客: {removed_customers}件")
        print(f"削除された物件: {removed_properties}件")
        print(f"削除されたエアコン: {removed_acs}件")
        print(f"削除された報告書: {removed_reports}件")

        print(f"\n完了時刻: {datetime.now()}")
        print("重複データ削除処理が完了しました！")


if __name__ == "__main__":
    main()
