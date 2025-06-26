from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    print("=== 管理者アカウント確認 ===")

    # 全管理者ユーザーを検索
    admin_users = User.query.filter_by(role="admin").all()

    if not admin_users:
        print("管理者アカウントが見つかりません。")
    else:
        print(f"管理者アカウント数: {len(admin_users)}")
        print("\n--- 管理者アカウント詳細 ---")

        for i, admin in enumerate(admin_users, 1):
            print(f"\n{i}. 管理者アカウント:")
            print(f"   ID: {admin.id}")
            print(f"   ユーザー名: {admin.username}")
            print(f"   表示名: {admin.name}")
            print(f"   メールアドレス: {admin.email}")
            print(f"   役割: {admin.role}")
            print(f"   アクティブ: {'はい' if admin.active else 'いいえ'}")
            print(f"   作成日時: {admin.created_at}")
            print(f"   更新日時: {admin.updated_at}")

    # 全ユーザー数も表示
    total_users = User.query.count()
    print(f"\n--- 全体統計 ---")
    print(f"総ユーザー数: {total_users}")

    # アクティブな管理者数
    active_admins = User.query.filter_by(role="admin", active=True).count()
    print(f"アクティブな管理者数: {active_admins}")
