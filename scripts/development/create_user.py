from app import create_app, db
from app.models.user import User
from datetime import datetime

app = create_app()

with app.app_context():
    # 既存のユーザーをチェック
    user = User.query.filter_by(username='admin').first()
    
    if user is None:
        # 管理者ユーザーを作成
        admin = User(
            username='admin',
            email='admin@example.com',
            name='管理者',
            role='admin',
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        admin.set_password('admin123')
        
        # データベースに保存
        db.session.add(admin)
        db.session.commit()
        
        print('管理者ユーザーを作成しました')
        print('ユーザー名: admin')
        print('パスワード: admin123')
    else:
        print('管理者ユーザーは既に存在します')
        print('ユーザー名:', user.username) 