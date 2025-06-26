from app import create_app, db
from app.models.user import User
from datetime import datetime

app = create_app()

with app.app_context():
    print("=== 管理者パスワードリセット ===")

    # 管理者ユーザーを検索
    admin_user = User.query.filter_by(username="dotaka565").first()

    if admin_user is None:
        print("指定された管理者ユーザーが見つかりません。")
    else:
        print(f"管理者ユーザーが見つかりました: {admin_user.username}")

        # 新しいパスワードを設定
        new_password = "admin123"  # 初期パスワード

        try:
            # パスワードを更新
            admin_user.set_password(new_password)
            admin_user.updated_at = datetime.utcnow()

            # データベースに保存
            db.session.commit()

            print("✅ パスワードリセットが完了しました！")
            print(f"ユーザー名: {admin_user.username}")
            print(f"新しいパスワード: {new_password}")
            print("⚠️  セキュリティのため、ログイン後にパスワードを変更してください。")

        except Exception as e:
            db.session.rollback()
            print(f"❌ パスワードリセットに失敗しました: {str(e)}")

    print("\n=== パスワード確認テスト ===")
    # パスワードが正しく設定されたかテスト
    admin_user = User.query.filter_by(username="dotaka565").first()
    if admin_user and admin_user.check_password(new_password):
        print("✅ パスワード設定が正常に完了しています。")
    else:
        print("❌ パスワード設定に問題があります。")
