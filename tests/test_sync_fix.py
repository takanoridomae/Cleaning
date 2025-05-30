from app import create_app, db
from app.models.report import Report
from app.models.schedule import Schedule
from datetime import datetime


def test_sync_fix():
    """修正したステータス同期機能をテスト"""
    app = create_app()
    with app.app_context():
        print("=== 修正後のステータス同期テスト ===")

        # 現在の報告書9とスケジュール4の状況確認
        report9 = Report.query.get(9)
        schedule4 = Schedule.query.get(4)

        print(f"修正前状況:")
        print(f"  報告書9 ステータス: {report9.status}")
        print(f"  スケジュール4 ステータス: {schedule4.status}")
        print(
            f"  同期状況: {'✅ 一致' if report9.status == schedule4.status else '❌ 不一致'}"
        )

        # 手動でステータス同期を実行してテスト
        from app.routes.reports import sync_schedule_status_with_report

        print(f"\n=== 手動同期実行 ===")
        print(f"報告書9のステータス '{report9.status}' に合わせてスケジュールを同期...")

        sync_schedule_status_with_report(report9)
        db.session.commit()

        # 結果確認
        schedule4_updated = Schedule.query.get(4)
        print(f"同期実行後:")
        print(f"  報告書9 ステータス: {report9.status}")
        print(f"  スケジュール4 ステータス: {schedule4_updated.status}")
        print(
            f"  同期状況: {'✅ 一致' if report9.status == schedule4_updated.status else '❌ 不一致'}"
        )
        print(f"  更新日時: {schedule4_updated.updated_at}")

        # 別のステータスでテスト
        print(f"\n=== 異なるステータスでのテスト ===")

        # 報告書を completed に変更
        report9.status = "completed"
        sync_schedule_status_with_report(report9)
        db.session.commit()

        schedule4_completed = Schedule.query.get(4)
        print(f"報告書を completed に変更後:")
        print(f"  報告書9 ステータス: {report9.status}")
        print(f"  スケジュール4 ステータス: {schedule4_completed.status}")
        print(
            f"  同期状況: {'✅ 一致' if report9.status == schedule4_completed.status else '❌ 不一致'}"
        )

        # 報告書を pending に戻す
        report9.status = "pending"
        sync_schedule_status_with_report(report9)
        db.session.commit()

        schedule4_pending = Schedule.query.get(4)
        print(f"報告書を pending に戻した後:")
        print(f"  報告書9 ステータス: {report9.status}")
        print(f"  スケジュール4 ステータス: {schedule4_pending.status}")
        print(
            f"  同期状況: {'✅ 一致' if report9.status == schedule4_pending.status else '❌ 不一致'}"
        )

        print(f"\n✅ ステータス同期修正テスト完了")


if __name__ == "__main__":
    test_sync_fix()
