from app import create_app, db
from app.models.report import Report
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from app.models.schedule import Schedule
from datetime import datetime, date


def test_report_schedule_integration():
    """報告書作成時の自動スケジュール登録をテスト"""
    app = create_app()
    with app.app_context():
        print("=== 報告書作成時のスケジュール自動登録テスト ===")

        # 実行前の状況確認
        report_count_before = Report.query.count()
        schedule_count_before = Schedule.query.count()
        print(
            f"実行前 - 報告書数: {report_count_before}, スケジュール数: {schedule_count_before}"
        )

        # テスト用報告書作成
        test_report = Report(
            title="テスト報告書",
            property_id=1,  # 東田クリニック
            date=date(2025, 5, 28),
            work_address="テスト住所",
            note="スケジュール自動登録テスト",
            status="pending",
        )

        db.session.add(test_report)
        db.session.flush()  # IDを取得

        print(f"作成した報告書ID: {test_report.id}")

        # 作業時間を追加
        work_time = WorkTime(
            report_id=test_report.id,
            property_id=1,
            work_date=date(2025, 5, 28),
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("15:00", "%H:%M").time(),
            note="テスト作業",
        )

        db.session.add(work_time)

        # 作業内容を追加
        work_detail = WorkDetail(
            report_id=test_report.id,
            property_id=1,
            description="エアコンクリーニング作業",
            confirmation="作業完了",
        )

        db.session.add(work_detail)

        # 手動でスケジュール作成関数を呼び出し
        from app.routes.reports import create_schedule_from_work_times

        work_dates = ["2025-05-28"]
        start_times = ["09:00"]
        end_times = ["15:00"]

        create_schedule_from_work_times(
            test_report, work_dates, start_times, end_times, 1
        )

        # コミット
        db.session.commit()

        # 結果確認
        report_count_after = Report.query.count()
        schedule_count_after = Schedule.query.count()

        print(
            f"実行後 - 報告書数: {report_count_after}, スケジュール数: {schedule_count_after}"
        )

        # 作成されたスケジュールを確認
        created_schedules = Schedule.query.filter_by(report_id=test_report.id).all()
        print(f"作成されたスケジュール数: {len(created_schedules)}")

        for schedule in created_schedules:
            print(f"  - ID: {schedule.id}")
            print(f"    タイトル: {schedule.title}")
            print(f"    開始日時: {schedule.start_datetime}")
            print(f"    終了日時: {schedule.end_datetime}")
            print(f"    ステータス: {schedule.status}")
            print(f"    報告書ID: {schedule.report_id}")
            print(f"    顧客ID: {schedule.customer_id}")
            print(f"    物件ID: {schedule.property_id}")
            print()

        # 確認完了
        if len(created_schedules) > 0:
            print("✅ スケジュール自動登録機能が正常に動作しています")
        else:
            print("❌ スケジュール自動登録機能に問題があります")


if __name__ == "__main__":
    test_report_schedule_integration()
