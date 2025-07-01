from app import db
from datetime import datetime, time
import pytz


class WorkTime(db.Model):
    """作業時間モデル"""

    __tablename__ = "work_times"

    id = db.Column(db.Integer, primary_key=True)
    work_date = db.Column(db.Date, nullable=False)  # 作業日
    start_time = db.Column(db.Time, nullable=False)  # 作業開始時間
    end_time = db.Column(db.Time, nullable=False)  # 作業終了時間
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
        onupdate=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
    )

    # 外部キー
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    # 備考
    note = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<WorkTime {self.work_date} {self.start_time}-{self.end_time}>"

    def to_dict(self):
        """作業時間情報を辞書形式で返す"""
        return {
            "id": self.id,
            "work_date": self.work_date.isoformat() if self.work_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "report_id": self.report_id,
            "property_id": self.property_id,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
