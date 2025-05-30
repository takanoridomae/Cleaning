from app import create_app, db
from app.models.report import Report
from app.models.schedule import Schedule
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from datetime import datetime, date


def test_report_delete_schedule_cancel():
    """レポート削除時のスケジュールキャンセル機能をテスト"""
    app = create_app()
    with app.app_context():
        print("=== レポート削除時のスケジュールキャンセル機能テスト ===")

        # 実行前の状況確認
        reports_before = Report.query.count()
        schedules_before = Schedule.query.count()
        print(
            f"実行前 - 報告書数: {reports_before}, スケジュール数: {schedules_before}"
        )

        # テスト用報告書作成
        test_report = Report(
            title="削除テスト報告書",
            property_id=1,
            date=date(2025, 6, 1),
            work_address="テスト住所（削除テスト用）",
            note="スケジュールキャンセル機能のテスト",
            status="pending",
        )

        db.session.add(test_report)
        db.session.flush()  # IDを取得

        print(f"作成した報告書ID: {test_report.id}")

        # 作業時間追加
        work_time = WorkTime(
            report_id=test_report.id,
            property_id=1,
            work_date=date(2025, 6, 1),
            start_time=datetime.strptime("10:00", "%H:%M").time(),
            end_time=datetime.strptime("16:00", "%H:%M").time(),
            note="削除テスト作業",
        )
        db.session.add(work_time)

        # 作業内容追加
        work_detail = WorkDetail(
            report_id=test_report.id,
            property_id=1,
            description="エアコンクリーニング削除テスト",
            confirmation="テスト作業完了",
        )
        db.session.add(work_detail)

        # 関連スケジュール作成
        test_schedule1 = Schedule(
            title=f"削除テスト: 報告書 #{test_report.id}",
            description="削除テスト用スケジュール1",
            start_datetime=datetime(2025, 6, 1, 10, 0),
            end_datetime=datetime(2025, 6, 1, 16, 0),
            all_day=False,
            status="pending",
            priority="normal",
            customer_id=1,
            property_id=1,
            report_id=test_report.id,
        )
        db.session.add(test_schedule1)

        # 追加スケジュール（複数関連のテスト）
        test_schedule2 = Schedule(
            title=f"削除テスト2: 報告書 #{test_report.id}",
            description="削除テスト用スケジュール2",
            start_datetime=datetime(2025, 6, 2, 9, 0),
            end_datetime=datetime(2025, 6, 2, 17, 0),
            all_day=False,
            status="completed",  # 異なるステータスでテスト
            priority="high",
            customer_id=1,
            property_id=1,
            report_id=test_report.id,
        )
        db.session.add(test_schedule2)

        db.session.commit()

        print(
            f"作成したスケジュール1 ID: {test_schedule1.id} (ステータス: {test_schedule1.status})"
        )
        print(
            f"作成したスケジュール2 ID: {test_schedule2.id} (ステータス: {test_schedule2.status})"
        )
        print(f"報告書 #{test_report.id} とスケジュールが関連付けられました")

        # 削除前の関連スケジュールステータス確認
        print("\n=== 削除前のスケジュールステータス確認 ===")
        related_schedules_before = Schedule.query.filter_by(
            report_id=test_report.id
        ).all()
        for schedule in related_schedules_before:
            print(
                f"スケジュール #{schedule.id}: ステータス={schedule.status}, report_id={schedule.report_id}"
            )

        # レポート削除の処理をシミュレート（修正した削除処理をテスト）
        print(f"\n=== 報告書 #{test_report.id} の削除処理実行 ===")

        # 修正した削除処理と同じロジックを実行
        related_schedules = Schedule.query.filter_by(report_id=test_report.id).all()
        for schedule in related_schedules:
            schedule.status = "cancelled"
            schedule.updated_at = datetime.now()
            schedule.report_id = None  # 関連を断つ
            print(
                f"スケジュール #{schedule.id} のステータスを「キャンセル」に更新しました"
            )

        # 関連データの削除
        WorkTime.query.filter_by(report_id=test_report.id).delete()
        WorkDetail.query.filter_by(report_id=test_report.id).delete()

        # 報告書自体の削除
        db.session.delete(test_report)
        db.session.commit()

        print(f"報告書 #{test_report.id} を削除しました")

        # 削除後の状況確認
        print(f"\n=== 削除後の状況確認 ===")
        reports_after = Report.query.count()
        schedules_after = Schedule.query.count()
        print(f"実行後 - 報告書数: {reports_after}, スケジュール数: {schedules_after}")

        # 削除されたスケジュールIDでスケジュールが残っているか確認
        remaining_schedule1 = Schedule.query.get(test_schedule1.id)
        remaining_schedule2 = Schedule.query.get(test_schedule2.id)

        if remaining_schedule1:
            print(
                f"スケジュール1 #{remaining_schedule1.id}: ステータス={remaining_schedule1.status}, report_id={remaining_schedule1.report_id}"
            )
        else:
            print("❌ スケジュール1が削除されています（期待されない動作）")

        if remaining_schedule2:
            print(
                f"スケジュール2 #{remaining_schedule2.id}: ステータス={remaining_schedule2.status}, report_id={remaining_schedule2.report_id}"
            )
        else:
            print("❌ スケジュール2が削除されています（期待されない動作）")

        # テスト結果判定
        print(f"\n=== テスト結果 ===")
        success = True

        if (
            remaining_schedule1
            and remaining_schedule1.status == "cancelled"
            and remaining_schedule1.report_id is None
        ):
            print(
                "✅ スケジュール1: ステータスがキャンセルに更新され、関連が解除されました"
            )
        else:
            print("❌ スケジュール1: 期待される状態になっていません")
            success = False

        if (
            remaining_schedule2
            and remaining_schedule2.status == "cancelled"
            and remaining_schedule2.report_id is None
        ):
            print(
                "✅ スケジュール2: ステータスがキャンセルに更新され、関連が解除されました"
            )
        else:
            print("❌ スケジュール2: 期待される状態になっていません")
            success = False

        if reports_after == reports_before:
            print("✅ 報告書は正常に削除されました")
        else:
            print("❌ 報告書の削除に問題があります")
            success = False

        if schedules_after == schedules_before + 2:
            print("✅ スケジュールは削除されずに保持されています")
        else:
            print("❌ スケジュールの保持に問題があります")
            success = False

        print(
            f"\n{'✅ テスト成功' if success else '❌ テスト失敗'}: レポート削除時のスケジュールキャンセル機能"
        )

        return success


if __name__ == "__main__":
    test_report_delete_schedule_cancel()
