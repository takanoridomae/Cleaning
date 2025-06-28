#!/usr/bin/env python3
"""
kumacaputenユーザーに管理者権限を付与するスクリプト
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app import create_app, db
from app.models.user import User


def grant_admin_permissions():
    app = create_app()

    with app.app_context():
        try:
            # kumacaputenユーザーを検索
            user = User.query.filter_by(username="kumacaputen").first()

            if user:
                print(f"ユーザー発見: {user.username}")
                print(f"現在の権限: {user.role}")

                # 管理者権限を付与
                user.role = "admin"
                user.is_active = True

                db.session.commit()

                print("✅ 管理者権限を付与しました")
                print(f"新しい権限: {user.role}")

            else:
                print("❌ kumacaputenユーザーが見つかりません")
                print("新しい管理者ユーザーを作成しますか？")

                # 新しい管理者ユーザーを作成
                from werkzeug.security import generate_password_hash

                new_admin = User(
                    username="kumacaputen",
                    email="kumacaputen@example.com",
                    password_hash=generate_password_hash("admin123"),  # 仮パスワード
                    role="admin",
                    is_active=True,
                    name="管理者",
                )

                db.session.add(new_admin)
                db.session.commit()

                print("✅ 新しい管理者ユーザーを作成しました")
                print("ユーザー名: kumacaputen")
                print("パスワード: admin123")
                print("権限: admin")

        except Exception as e:
            db.session.rollback()
            print(f"エラー: {e}")


if __name__ == "__main__":
    grant_admin_permissions()
