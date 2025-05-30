from app import create_app, db
from app.models.schedule import Schedule
from app.models.customer import Customer
from app.models.property import Property
from datetime import datetime, date, timedelta

# アプリケーションコンテキストを作成
app = create_app()
app_context = app.app_context()
app_context.push()

print("テスト用スケジュールデータを作成します...")

try:
    # 既存の顧客・物件を取得
    customers = Customer.query.limit(3).all()
    properties = Property.query.limit(3).all()

    if not customers:
        print("顧客データが存在しません。先に顧客データを登録してください。")
        app_context.pop()
        exit()

    # 今月のスケジュールを作成
    today = date.today()

    test_schedules = [
        {
            "title": "エアコンクリーニング作業",
            "description": f"{customers[0].name}様宅のエアコンクリーニング予定",
            "start_datetime": datetime.combine(
                today + timedelta(days=2), datetime.min.time().replace(hour=9)
            ),
            "end_datetime": datetime.combine(
                today + timedelta(days=2), datetime.min.time().replace(hour=17)
            ),
            "customer_id": customers[0].id,
            "property_id": properties[0].id if properties else None,
            "priority": "normal",
            "status": "pending",
        },
        {
            "title": "定期メンテナンス",
            "description": f"{customers[1].name if len(customers) > 1 else customers[0].name}様宅の定期メンテナンス",
            "start_datetime": datetime.combine(
                today + timedelta(days=5), datetime.min.time().replace(hour=10)
            ),
            "end_datetime": datetime.combine(
                today + timedelta(days=5), datetime.min.time().replace(hour=16)
            ),
            "customer_id": customers[1].id if len(customers) > 1 else customers[0].id,
            "property_id": (
                properties[1].id
                if len(properties) > 1
                else (properties[0].id if properties else None)
            ),
            "priority": "high",
            "status": "pending",
        },
    ]

    created_count = 0
    for schedule_data in test_schedules:
        schedule = Schedule(**schedule_data)
        db.session.add(schedule)
        created_count += 1

    db.session.commit()
    print(f"{created_count}件のテストスケジュールを作成しました")

    # 作成されたスケジュールを確認
    print("\n=== 作成されたスケジュール ===")
    schedules = Schedule.query.order_by(Schedule.start_datetime).all()
    for schedule in schedules:
        print(f"ID: {schedule.id}")
        print(f"タイトル: {schedule.title}")
        print(f"開始日時: {schedule.start_datetime}")
        print(f"ステータス: {schedule.status_display}")
        print(f"顧客: {schedule.customer.name if schedule.customer else 'なし'}")
        print(
            f"物件: {schedule.schedule_property.name if schedule.schedule_property else 'なし'}"
        )
        print("---")

    print(f"\n総スケジュール数: {len(schedules)}件")

except Exception as e:
    print(f"エラー: {e}")
    import traceback

    traceback.print_exc()
    db.session.rollback()

app_context.pop()
