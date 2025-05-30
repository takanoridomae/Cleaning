from app import create_app, db
from app.models.schedule import Schedule
from datetime import datetime


def create_test_schedules():
    app = create_app()
    with app.app_context():
        # 既存のスケジュールを確認
        existing_schedules = Schedule.query.all()
        print(f"既存のスケジュール数: {len(existing_schedules)}")

        # テストスケジュール1: 完了ステータス（5月）
        schedule1 = Schedule(
            title="クリーニング完了案件",
            description="エアコンクリーニング作業完了",
            start_datetime=datetime(2025, 5, 15, 14, 0),
            end_datetime=datetime(2025, 5, 15, 16, 0),
            all_day=False,
            status="completed",
            priority="normal",
        )

        # テストスケジュール2: 未完了ステータス（6月）
        schedule2 = Schedule(
            title="新規クリーニング予定",
            description="来月のエアコンクリーニング予定",
            start_datetime=datetime(2025, 6, 10, 9, 0),
            end_datetime=datetime(2025, 6, 10, 12, 0),
            all_day=False,
            status="pending",
            priority="high",
        )

        # テストスケジュール3: 完了ステータス（6月）
        schedule3 = Schedule(
            title="メンテナンス完了",
            description="定期メンテナンス作業完了",
            start_datetime=datetime(2025, 6, 20, 13, 0),
            end_datetime=datetime(2025, 6, 20, 15, 0),
            all_day=False,
            status="completed",
            priority="normal",
        )

        # テストスケジュール4: キャンセルステータス（6月）
        schedule4 = Schedule(
            title="キャンセル案件",
            description="お客様都合によりキャンセル",
            start_datetime=datetime(2025, 6, 25, 10, 0),
            end_datetime=datetime(2025, 6, 25, 12, 0),
            all_day=False,
            status="cancelled",
            priority="low",
        )

        # データベースに追加
        schedules_to_add = [schedule1, schedule2, schedule3, schedule4]
        for schedule in schedules_to_add:
            db.session.add(schedule)

        try:
            db.session.commit()
            print(f"テストスケジュール{len(schedules_to_add)}件を追加しました")

            # 追加後の確認
            all_schedules = Schedule.query.all()
            print(f"総スケジュール数: {len(all_schedules)}")

            for schedule in all_schedules:
                print(
                    f"ID: {schedule.id}, タイトル: {schedule.title}, ステータス: {schedule.status}, 日時: {schedule.start_datetime}"
                )

        except Exception as e:
            db.session.rollback()
            print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    create_test_schedules()
