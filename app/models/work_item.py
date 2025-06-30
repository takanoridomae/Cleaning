from app import db
from datetime import datetime


class WorkItem(db.Model):
    """作業項目マスターモデル"""

    __tablename__ = "work_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 作業項目名
    description = db.Column(db.Text)  # 説明
    work_amount = db.Column(db.Integer, default=0)  # 作業金額
    is_active = db.Column(db.Boolean, default=True)  # 有効/無効フラグ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<WorkItem {self.name}>"

    def to_dict(self):
        """作業項目情報を辞書形式で返す"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "work_amount": self.work_amount,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
