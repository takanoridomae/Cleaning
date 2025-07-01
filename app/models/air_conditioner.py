from app import db
from datetime import datetime
import pytz


class AirConditioner(db.Model):
    """エアコン情報モデル"""

    __tablename__ = "air_conditioners"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    # エアコン基本情報
    ac_type = db.Column(db.String(50))  # エアコン種別（壁掛け、天井埋込み、etc）
    manufacturer = db.Column(db.String(100))  # エアコンメーカー
    model_number = db.Column(db.String(100))  # エアコン品番
    quantity = db.Column(db.Integer, default=1)  # 台数
    location = db.Column(db.String(100))  # 設置場所

    # 料金情報
    unit_price = db.Column(db.Integer)  # 単価
    total_amount = db.Column(db.Integer)  # 金額

    # クリーニング情報
    cleaning_type = db.Column(db.String(50))  # クリーニング種別

    # その他
    note = db.Column(db.Text)  # 備考
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
        onupdate=lambda: datetime.now(pytz.timezone("Asia/Tokyo")).replace(tzinfo=None),
    )

    def __repr__(self):
        return f"<AirConditioner {self.id} - {self.manufacturer} {self.model_number}>"

    def to_dict(self):
        """エアコン情報を辞書形式で返す"""
        return {
            "id": self.id,
            "property_id": self.property_id,
            "ac_type": self.ac_type,
            "manufacturer": self.manufacturer,
            "model_number": self.model_number,
            "quantity": self.quantity,
            "location": self.location,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "cleaning_type": self.cleaning_type,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
