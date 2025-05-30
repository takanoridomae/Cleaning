from app import db
from datetime import datetime


class Schedule(db.Model):
    """スケジュール管理モデル"""

    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # スケジュールタイトル
    description = db.Column(db.Text)  # 説明
    start_datetime = db.Column(db.DateTime, nullable=False)  # 開始日時
    end_datetime = db.Column(db.DateTime, nullable=False)  # 終了日時
    all_day = db.Column(db.Boolean, default=False)  # 終日フラグ
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, completed, cancelled
    priority = db.Column(db.String(10), default="normal")  # low, normal, high, urgent

    # 既存データとの関連
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=True)

    # Googleカレンダー連携（後のフェーズで使用）
    google_calendar_id = db.Column(db.String(500))  # GoogleカレンダーのイベントID
    google_calendar_sync = db.Column(db.Boolean, default=False)  # 同期フラグ

    # 繰り返し設定（後のフェーズで使用）
    recurrence_type = db.Column(db.String(20))  # none, daily, weekly, monthly
    recurrence_end = db.Column(db.Date)  # 繰り返し終了日

    # 通知設定
    notification_enabled = db.Column(db.Boolean, default=True)
    notification_minutes = db.Column(db.Integer, default=30)  # 何分前に通知

    # システム項目
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーションシップ
    customer = db.relationship("Customer", backref="schedules", lazy=True)
    schedule_property = db.relationship("Property", backref="schedules", lazy=True)
    report = db.relationship("Report", backref="schedules", lazy=True)
    creator = db.relationship("User", backref="schedules", lazy=True)

    def __repr__(self):
        return f"<Schedule {self.title} - {self.start_datetime}>"

    def to_dict(self):
        """スケジュール情報を辞書形式で返す"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_datetime": (
                self.start_datetime.isoformat() if self.start_datetime else None
            ),
            "end_datetime": (
                self.end_datetime.isoformat() if self.end_datetime else None
            ),
            "all_day": self.all_day,
            "status": self.status,
            "priority": self.priority,
            "customer_id": self.customer_id,
            "property_id": self.property_id,
            "report_id": self.report_id,
            "customer_name": self.customer.name if self.customer else None,
            "property_name": (
                self.schedule_property.name if self.schedule_property else None
            ),
            "notification_enabled": self.notification_enabled,
            "notification_minutes": self.notification_minutes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def status_display(self):
        """ステータスの日本語表示"""
        status_map = {
            "pending": "未完了",
            "completed": "完了",
            "cancelled": "キャンセル",
        }
        return status_map.get(self.status, self.status)

    @property
    def priority_display(self):
        """優先度の日本語表示"""
        priority_map = {"low": "低", "normal": "標準", "high": "高", "urgent": "緊急"}
        return priority_map.get(self.priority, self.priority)
