from app import db
from datetime import datetime


class Report(db.Model):
    """報告書モデル"""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(
        db.String(100), nullable=False, default="作業完了書"
    )  # タイトル（デフォルト：作業完了書）
    date = db.Column(db.Date, nullable=False)  # 作業日
    work_address = db.Column(db.String(200))  # 作業住所
    technician = db.Column(db.String(100))  # 作業者名
    status = db.Column(db.String(20), default="pending")  # pending, completed
    work_description = db.Column(db.Text)  # 作業内容（古いフィールド）
    note = db.Column(db.Text)  # 備考
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 外部キー
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    # リレーションシップ
    photos = db.relationship(
        "Photo", backref="report", lazy=True, cascade="all, delete-orphan"
    )
    work_times = db.relationship(
        "WorkTime", backref="report", lazy=True, cascade="all, delete-orphan"
    )
    work_details = db.relationship(
        "WorkDetail", backref="report", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Report {self.title} - {self.id}>"

    def to_dict(self):
        """報告書情報を辞書形式で返す"""
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "work_address": self.work_address,
            "technician": self.technician,
            "status": self.status,
            "work_description": self.work_description,
            "note": self.note,
            "property_id": self.property_id,
            "property_name": self.property.name if self.property else None,
            "customer_name": (
                self.property.customer.name
                if self.property and self.property.customer
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "photo_count": len(self.photos) if self.photos else 0,
            "work_times_count": len(self.work_times) if self.work_times else 0,
            "work_details_count": len(self.work_details) if self.work_details else 0,
        }
