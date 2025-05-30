from app import create_app, db
from app.models.report import Report
from app.models.schedule import Schedule
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from datetime import datetime, date


def test_report_schedule_sync():
    """報告書とスケジュールのステータス同期をテスト"""
    app = create_app()
    with app.app_context():
        print("=== 報告書とスケジュールのステータス同期テスト ===")

        # 実行前の状況確認
        reports_before = Report.query.count()
        schedules_before = Schedule.query.count()
        print(
            f"実行前 - 報告書数: {reports_before}, スケジュール数: {schedules_before}"
        )

        # テスト用報告書作成（ステータス: pending）
        test_report = Report(
            title="ステータス同期テスト報告書",
            property_id=1,
            date=date(2025, 5, 30),
            work_address="テスト住所 同期確認",
            note="ステータス同期機能のテスト",
            status="pending",  # 初期ステータス
        )

        db.session.add(test_report)
        db.session.flush()

        print(f"作成した報告書ID: {test_report.id}, ステータス: {test_report.status}")

        # 作業時間追加
        work_time = WorkTime(
            report_id=test_report.id,
            property_id=1,
            work_date=date(2025, 5, 30),
            start_time=datetime.strptime("10:00", "%H:%M").time(),
            end_time=datetime.strptime("16:00", "%H:%M").time(),
            note="同期テスト作業",
        )
        db.session.add(work_time)

        # 作業内容追加
        work_detail = WorkDetail(
            report_id=test_report.id,
            property_id=1,
            description="エアコンクリーニング同期テスト",
            confirmation="テスト作業完了",
        )
        db.session.add(work_detail)

        # スケジュール手動作成（関連付けあり）
        test_schedule = Schedule(
            title=f"同期テスト: 報告書 #{test_report.id}",
            description="ステータス同期テスト用スケジュール",
            start_datetime=datetime(2025, 5, 30, 10, 0),
            end_datetime=datetime(2025, 5, 30, 16, 0),
            all_day=False,
            status="pending",  # 初期ステータス
            priority="normal",
            customer_id=1,
            property_id=1,
            report_id=test_report.id,  # 報告書との関連付け
        )
        db.session.add(test_schedule)
        db.session.commit()

        print(
            f"作成したスケジュールID: {test_schedule.id}, ステータス: {test_schedule.status}"
        )
        print(
            f"報告書 #{test_report.id} とスケジュール #{test_schedule.id} が関連付けられました"
        )

        # ステータス同期関数のテスト
        from app.routes.reports import sync_schedule_status_with_report

        print("\n=== ステータス変更テスト ===")

        # 1. 報告書を「完了」に変更
        print("1. 報告書ステータスを 'completed' に変更")
        test_report.status = "completed"
        sync_schedule_status_with_report(test_report)
        db.session.commit()

        # 結果確認
        updated_schedule = Schedule.query.get(test_schedule.id)
        print(f"   報告書ステータス: {test_report.status}")
        print(f"   スケジュールステータス: {updated_schedule.status}")
        print(
            f"   同期成功: {'✅' if updated_schedule.status == 'completed' else '❌'}"
        )

        # 2. 報告書を「キャンセル」に変更
        print("\n2. 報告書ステータスを 'cancelled' に変更")
        test_report.status = "cancelled"
        sync_schedule_status_with_report(test_report)
        db.session.commit()

        # 結果確認
        updated_schedule = Schedule.query.get(test_schedule.id)
        print(f"   報告書ステータス: {test_report.status}")
        print(f"   スケジュールステータス: {updated_schedule.status}")
        print(
            f"   同期成功: {'✅' if updated_schedule.status == 'cancelled' else '❌'}"
        )

        # 3. 報告書を「作業中」に戻す
        print("\n3. 報告書ステータスを 'pending' に変更")
        test_report.status = "pending"
        sync_schedule_status_with_report(test_report)
        db.session.commit()

        # 結果確認
        updated_schedule = Schedule.query.get(test_schedule.id)
        print(f"   報告書ステータス: {test_report.status}")
        print(f"   スケジュールステータス: {updated_schedule.status}")
        print(f"   同期成功: {'✅' if updated_schedule.status == 'pending' else '❌'}")

        # 最終状況確認
        print(f"\n=== 最終状況 ===")
        reports_after = Report.query.count()
        schedules_after = Schedule.query.count()
        print(f"実行後 - 報告書数: {reports_after}, スケジュール数: {schedules_after}")

        # 関連データ表示
        all_schedules = Schedule.query.filter_by(report_id=test_report.id).all()
        print(f"報告書 #{test_report.id} に関連するスケジュール:")
        for schedule in all_schedules:
            print(
                f"  - ID: {schedule.id}, タイトル: {schedule.title}, ステータス: {schedule.status}"
            )

        print("✅ ステータス同期機能のテストが完了しました")


if __name__ == "__main__":
    test_report_schedule_sync()
