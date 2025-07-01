from app import db
from datetime import datetime
import pytz


class WorkDetail(db.Model):
    """作業内容モデル"""

    __tablename__ = "work_details"

    id = db.Column(db.Integer, primary_key=True)
    work_item_id = db.Column(
        db.Integer, db.ForeignKey("work_items.id")
    )  # 作業項目ID (マスターテーブル参照)
    work_item_text = db.Column(db.String(100))  # 作業項目テキスト (手動入力用)
    description = db.Column(db.Text, nullable=False)  # 作業内容
    confirmation = db.Column(db.String(100))  # 作業確認
    work_amount = db.Column(db.Integer, default=0)  # 作業金額
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
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=True)
    air_conditioner_id = db.Column(
        db.Integer, db.ForeignKey("air_conditioners.id"), nullable=True
    )

    # リレーションシップ
    work_item = db.relationship("WorkItem", backref="work_details", lazy=True)
    air_conditioner = db.relationship(
        "AirConditioner", backref="work_details", lazy=True
    )

    def __repr__(self):
        item_name = self.work_item.name if self.work_item else self.work_item_text
        return f"<WorkDetail {item_name}>"

    @property
    def work_item_name(self):
        """作業項目名を取得（マスタから取得or手入力値）"""
        if self.work_item:
            return self.work_item.name
        return self.work_item_text or ""

    def to_dict(self):
        """作業内容情報を辞書形式で返す"""
        return {
            "id": self.id,
            "work_item_id": self.work_item_id,
            "work_item_text": self.work_item_text,
            "work_item_name": self.work_item_name,
            "description": self.description,
            "confirmation": self.confirmation,
            "work_amount": self.work_amount,
            "report_id": self.report_id,
            "property_id": self.property_id,
            "air_conditioner_id": self.air_conditioner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
