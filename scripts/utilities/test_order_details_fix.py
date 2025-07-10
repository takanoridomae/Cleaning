#!/usr/bin/env python3
"""
受注明細の金額修正のテストスクリプト
修正前: 物件全体のエアコンの金額合計を表示
修正後: 報告書毎に作業したエアコンの金額のみを表示
"""

from app import create_app, db
from app.models.report import Report
from app.models.work_detail import WorkDetail
from app.models.air_conditioner import AirConditioner
from app.models.property import Property
from app.models.customer import Customer

app = create_app()


def test_order_details_calculation():
    """受注明細の金額計算をテストする"""
    with app.app_context():
        print("=== 受注明細金額計算テスト ===")

        # 全ての報告書を取得
        reports = Report.query.join(Property).join(Customer).all()

        print(f"総報告書数: {len(reports)}件")
        print()

        for report in reports:
            print(f"報告書ID: {report.id}")
            print(f"物件: {report.property.name} (ID: {report.property.id})")
            print(f"顧客: {report.property.customer.name}")

            # 修正前の計算（物件全体）
            old_total_amount = (
                db.session.query(db.func.sum(AirConditioner.total_amount))
                .filter(AirConditioner.property_id == report.property_id)
                .scalar()
                or 0
            )

            # 修正後の計算（報告書毎の作業エアコンのみ）
            new_total_amount = (
                db.session.query(db.func.sum(AirConditioner.total_amount))
                .join(WorkDetail, AirConditioner.id == WorkDetail.air_conditioner_id)
                .filter(WorkDetail.report_id == report.id)
                .scalar()
                or 0
            )

            # エアコン数も確認
            old_ac_count = AirConditioner.query.filter_by(
                property_id=report.property_id
            ).count()

            new_ac_count = (
                db.session.query(
                    db.func.count(db.func.distinct(WorkDetail.air_conditioner_id))
                )
                .filter(
                    WorkDetail.report_id == report.id,
                    WorkDetail.air_conditioner_id.isnot(None),
                )
                .scalar()
                or 0
            )

            # 作業内容の詳細を表示
            work_details = WorkDetail.query.filter_by(report_id=report.id).all()
            work_ac_ids = [
                wd.air_conditioner_id for wd in work_details if wd.air_conditioner_id
            ]

            print(f"  作業内容数: {len(work_details)}件")
            print(f"  作業エアコンID: {work_ac_ids}")
            print(
                f"  修正前 - エアコン数: {old_ac_count}台, 金額: ¥{old_total_amount:,}"
            )
            print(
                f"  修正後 - エアコン数: {new_ac_count}台, 金額: ¥{new_total_amount:,}"
            )

            if old_total_amount != new_total_amount:
                print(
                    f"  ★ 金額に差異あり: 差額 ¥{old_total_amount - new_total_amount:,}"
                )

            print()


if __name__ == "__main__":
    test_order_details_calculation()
