from app import db
from datetime import datetime


class Photo(db.Model):
    """写真モデル"""

    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    photo_type = db.Column(db.String(10), nullable=False)  # 'before' または 'after'
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200))
    caption = db.Column(db.String(200))
    room_name = db.Column(db.String(100))  # 撮影場所（部屋名等）
    photo_set_id = db.Column(db.String(50))  # 施工前後の写真をグループ化するID
    aircon_model = db.Column(db.String(100))  # エアコン機種
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    filepath = db.Column(db.String(500))  # 階層化されたファイルパス（相対パス）

    # 外部キー
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=False)
    air_conditioner_id = db.Column(
        db.Integer, db.ForeignKey("air_conditioners.id"), nullable=True
    )  # エアコンとの紐づけ
    work_item_id = db.Column(
        db.Integer, db.ForeignKey("work_items.id"), nullable=True
    )  # 作業項目との紐づけ

    # リレーションシップ
    air_conditioner = db.relationship("AirConditioner", backref="photos", lazy=True)
    work_item = db.relationship("WorkItem", backref="photos", lazy=True)

    def __repr__(self):
        return f"<Photo {self.photo_type} - {self.filename}>"

    def to_dict(self):
        """写真情報を辞書形式で返す"""
        return {
            "id": self.id,
            "photo_type": self.photo_type,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "caption": self.caption,
            "room_name": self.room_name,
            "photo_set_id": self.photo_set_id,
            "aircon_model": self.aircon_model,
            "air_conditioner_id": self.air_conditioner_id,
            "work_item_id": self.work_item_id,
            "note": self.note,
            "report_id": self.report_id,
            "filepath": self.filepath,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def file_path(self):
        """写真ファイルパスを返す"""
        from flask import current_app
        import os

        # filepathが設定されている場合はそれを使用
        if self.filepath:
            return os.path.join(current_app.config["UPLOAD_FOLDER"], self.filepath)

        # 後方互換性のためにlegacyパスも提供
        folder = "before" if self.photo_type == "before" else "after"
        return os.path.join(current_app.config["UPLOAD_FOLDER"], folder, self.filename)
