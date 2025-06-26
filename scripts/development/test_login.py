from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    print("=== ログイン機能テスト ===")

    # 管理者ユーザーを取得
    admin_user = User.query.filter_by(username="dotaka565").first()

    if admin_user is None:
        print("❌ 管理者ユーザーが見つかりません。")
    else:
        print(f"✅ ユーザーが見つかりました: {admin_user.username}")

        # Flask-Loginのメソッドをテスト
        print(f"ID: {admin_user.get_id()}")
        print(f"認証済み: {admin_user.is_authenticated()}")
        print(f"アクティブ: {admin_user.is_active()}")
        print(f"匿名: {admin_user.is_anonymous()}")

        # パスワードテスト
        test_password = "admin123"
        password_check = admin_user.check_password(test_password)
        print(
            f"パスワード検証 ('{test_password}'): {'✅ 正しい' if password_check else '❌ 間違い'}"
        )

        # パスワードハッシュを確認
        print(f"パスワードハッシュ: {admin_user.password_hash[:50]}...")

        # 権限チェック
        print(f"管理者権限: {'✅ あり' if admin_user.is_admin() else '❌ なし'}")
        print(f"編集権限: {'✅ あり' if admin_user.can_edit() else '❌ なし'}")

        # Userオブジェクトの基本情報
        print(f"\n--- ユーザー詳細 ---")
        print(f"ID: {admin_user.id}")
        print(f"ユーザー名: {admin_user.username}")
        print(f"表示名: {admin_user.name}")
        print(f"メール: {admin_user.email}")
        print(f"役割: {admin_user.role}")
        print(f"アクティブ: {admin_user.active}")

    print("\n=== 新しいテストユーザーでパスワード検証テスト ===")
    # 新しいテストユーザーを作成してパスワード機能をテスト
    test_user = User(
        username="test_user",
        email="test@example.com",
        name="テストユーザー",
        role="viewer",
    )
    test_password = "test123"
    test_user.set_password(test_password)

    print(
        f"新しいユーザーのパスワード検証: {'✅ 正しい' if test_user.check_password(test_password) else '❌ 間違い'}"
    )
    print(
        f"間違いパスワードの検証: {'❌ 通った(問題)' if test_user.check_password('wrong') else '✅ 正しく拒否'}"
    )
