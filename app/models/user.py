from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """ユーザーモデル"""
    
    __tablename__ = 'users'
    
    # 権限レベル定数
    ROLE_ADMIN = 'admin'
    ROLE_ALL_ACCESS = 'all_access'
    ROLE_EDITOR = 'editor'
    ROLE_VIEWER = 'viewer'
    ROLE_USER = 'user'  # 下位互換性のため残す
    
    ROLES = {
        ROLE_ADMIN: '管理者',
        ROLE_ALL_ACCESS: 'すべて可能',
        ROLE_EDITOR: '修正のみ可能',
        ROLE_VIEWER: '閲覧のみ可能',
        ROLE_USER: '一般ユーザー'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='viewer')  # デフォルトを閲覧のみに変更
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """パスワードハッシュを生成して保存"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """パスワードを検証"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """管理者権限を持つかチェック"""
        return self.role == self.ROLE_ADMIN
    
    def can_view(self):
        """閲覧権限を持つかチェック"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_ALL_ACCESS, self.ROLE_EDITOR, self.ROLE_VIEWER, self.ROLE_USER]
    
    def can_edit(self):
        """編集権限を持つかチェック"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_ALL_ACCESS, self.ROLE_EDITOR]
    
    def can_delete(self):
        """削除権限を持つかチェック"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_ALL_ACCESS]
    
    def can_create(self):
        """作成権限を持つかチェック"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_ALL_ACCESS]
    
    def get_role_display_name(self):
        """権限の表示名を取得"""
        return self.ROLES.get(self.role, self.role)
    
    def to_dict(self):
        """ユーザー情報を辞書形式で返す"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'role_display': self.get_role_display_name(),
            'active': self.active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 