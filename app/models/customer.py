from app import db
from datetime import datetime


class Customer(db.Model):
    """お客様情報モデル"""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    postal_code = db.Column(db.String(8))  # 郵便番号（ハイフンあり8文字）
    address = db.Column(db.String(200))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーションシップ
    properties = db.relationship("Property", backref="customer", lazy=True)

    def __repr__(self):
        return f"<Customer {self.name}>"

    def to_dict(self):
        """お客様情報を辞書形式で返す"""
        return {
            "id": self.id,
            "name": self.name,
            "company_name": self.company_name,
            "email": self.email,
            "phone": self.phone,
            "postal_code": self.postal_code,
            "address": self.address,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "property_count": len(self.properties) if self.properties else 0,
        }
