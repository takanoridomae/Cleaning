#!/usr/bin/env python3
"""
ユーザーの権限を確認するスクリプト
"""

import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app import create_app, db
from app.models.user import User


def check_user_permissions():
    app = create_app()

    with app.app_context():
        try:
            # 全ユーザーを取得
            users = User.query.all()

            print("=== ユーザー権限確認 ===")
            print(f"総ユーザー数: {len(users)}")
            print()

            for user in users:
                print(f"ユーザー名: {user.username}")
                print(f"メール: {user.email}")
                print(f"権限: {user.role}")
                print(f"有効: {'はい' if user.is_active else 'いいえ'}")
                print("-" * 30)

            # kumacaputenユーザーの詳細確認
            kumacaputen = User.query.filter_by(username="kumacaputen").first()
            if kumacaputen:
                print("\n=== kumacaputenユーザー詳細 ===")
                print(f"ID: {kumacaputen.id}")
                print(f"ユーザー名: {kumacaputen.username}")
                print(f"メール: {kumacaputen.email}")
                print(f"権限: {kumacaputen.role}")
                print(f"有効: {'はい' if kumacaputen.is_active else 'いいえ'}")
                print(
                    f"管理者権限: {'あり' if kumacaputen.role == 'admin' else 'なし'}"
                )
            else:
                print("\n❌ kumacaputenユーザーが見つかりません")

        except Exception as e:
            print(f"エラー: {e}")


if __name__ == "__main__":
    check_user_permissions()
