from app import create_app, db
from app.models.schedule import Schedule
from app.models.report import Report
import sqlite3

app = create_app()
with app.app_context():
    print("=== スケジュールデータベース確認 ===")

    # スケジュール総数
    total_schedules = Schedule.query.count()
    print(f"総スケジュール数: {total_schedules}")

    # ステータス別の集計
    pending_count = Schedule.query.filter_by(status="pending").count()
    completed_count = Schedule.query.filter_by(status="completed").count()
    cancelled_count = Schedule.query.filter_by(status="cancelled").count()

    print(f"  - pending: {pending_count}")
    print(f"  - completed: {completed_count}")
    print(f"  - cancelled: {cancelled_count}")

    # 直近のスケジュール（最大10件）
    print(f"\n=== 直近のスケジュール（最大10件） ===")
    recent_schedules = Schedule.query.order_by(Schedule.id.desc()).limit(10).all()

    for schedule in recent_schedules:
        print(f"ID: {schedule.id}")
        print(f"  タイトル: {schedule.title}")
        print(f"  ステータス: {schedule.status}")
        print(f"  開始日時: {schedule.start_datetime}")
        print(f"  関連報告書ID: {schedule.report_id}")
        print(f"  顧客ID: {schedule.customer_id}")
        print(f"  物件ID: {schedule.property_id}")
        print("  ---")

    # キャンセルされたスケジュール
    print(f"\n=== キャンセルされたスケジュール ===")
    cancelled_schedules = Schedule.query.filter_by(status="cancelled").all()

    if cancelled_schedules:
        for schedule in cancelled_schedules:
            print(f"ID: {schedule.id}")
            print(f"  タイトル: {schedule.title}")
            print(f"  説明: {schedule.description}")
            print(f"  開始日時: {schedule.start_datetime}")
            print(f"  関連報告書ID: {schedule.report_id}")
            print(f"  更新日時: {schedule.updated_at}")
            print("  ---")
    else:
        print("キャンセルされたスケジュールはありません")

    # 報告書との関連性確認
    print(f"\n=== 報告書との関連性確認 ===")
    schedules_with_report = Schedule.query.filter(
        Schedule.report_id.isnot(None)
    ).count()
    schedules_without_report = Schedule.query.filter(
        Schedule.report_id.is_(None)
    ).count()

    print(f"報告書と関連付けされているスケジュール: {schedules_with_report}")
    print(f"報告書と関連付けされていないスケジュール: {schedules_without_report}")

    # 報告書に関連するスケジュール詳細
    if schedules_with_report > 0:
        print(f"\n=== 報告書関連スケジュール詳細 ===")
        related_schedules = Schedule.query.filter(Schedule.report_id.isnot(None)).all()
        for schedule in related_schedules:
            # 関連報告書が存在するかチェック
            report = Report.query.get(schedule.report_id)
            report_status = report.status if report else "報告書が削除済み"

            print(f"スケジュールID: {schedule.id}, 報告書ID: {schedule.report_id}")
            print(f"  スケジュールステータス: {schedule.status}")
            print(f"  報告書ステータス: {report_status}")
            print(
                f"  同期状況: {'一致' if report and schedule.status == report.status else '不一致または報告書削除済み'}"
            )
            print("  ---")

    print(f"\n=== 確認完了 ===")
