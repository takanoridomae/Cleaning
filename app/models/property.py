from app import db
from datetime import datetime
import pytz


class Property(db.Model):
    """物件情報モデル"""

    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(8))  # 郵便番号（ハイフンあり8文字）
    address = db.Column(db.String(200))
    note = db.Column(db.Text)
    reception_type = db.Column(db.String(50))  # 受付種別
    reception_detail = db.Column(db.Text)  # 受付明細
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
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)

    # リレーションシップ
    reports = db.relationship(
        "Report", backref="property", lazy=True, cascade="all, delete-orphan"
    )
    air_conditioners = db.relationship(
        "AirConditioner", backref="property", lazy=True, cascade="all, delete-orphan"
    )
    work_times = db.relationship(
        "WorkTime", backref="property", lazy=True, cascade="all, delete-orphan"
    )
    work_details = db.relationship(
        "WorkDetail", backref="property", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Property {self.name}>"

    def to_dict(self):
        """物件情報を辞書形式で返す"""
        return {
            "id": self.id,
            "name": self.name,
            "postal_code": self.postal_code,
            "address": self.address,
            "note": self.note,
            "reception_type": self.reception_type,
            "reception_detail": self.reception_detail,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "report_count": len(self.reports) if self.reports else 0,
        }
