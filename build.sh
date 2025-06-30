#!/usr/bin/env bash
# Render Build Script

set -o errexit  # exit on error

# パッケージのインストール
pip install -r requirements.txt

# データベースディレクトリの作成
mkdir -p instance

# Persistent Disk設定の確認と初期化
PERSISTENT_DISK_PATH="/opt/render/project/src/uploads"

echo "=== Persistent Disk 設定確認 ==="

if [ -d "$PERSISTENT_DISK_PATH" ]; then
    echo "✅ Persistent Diskが検出されました: $PERSISTENT_DISK_PATH"
    
    # 必要なサブディレクトリが存在しない場合は作成
    mkdir -p "$PERSISTENT_DISK_PATH/before"
    mkdir -p "$PERSISTENT_DISK_PATH/after" 
    mkdir -p "$PERSISTENT_DISK_PATH/thumbnails"
    mkdir -p "$PERSISTENT_DISK_PATH/PDF"
    
    # 権限設定
    chmod -R 755 "$PERSISTENT_DISK_PATH"
    
    # 既存ファイル数の確認
    BEFORE_COUNT=$(find "$PERSISTENT_DISK_PATH/before" -type f 2>/dev/null | wc -l)
    AFTER_COUNT=$(find "$PERSISTENT_DISK_PATH/after" -type f 2>/dev/null | wc -l)
    
    echo "📁 既存写真データ:"
    echo "   - 施工前写真: ${BEFORE_COUNT}件"
    echo "   - 施工後写真: ${AFTER_COUNT}件"
    
    if [ $((BEFORE_COUNT + AFTER_COUNT)) -gt 0 ]; then
        echo "🔄 既存の写真データが保護されます"
    else
        echo "📂 新規Persistent Diskです"
    fi
else
    echo "⚠️  Persistent Diskが検出されませんでした"
    echo "   デフォルトの一時的なuploadsディレクトリを作成します"
    echo "   ※ 再デプロイ時にファイルが削除される可能性があります"
    
    # フォールバック用のディレクトリ作成
    mkdir -p uploads/before
    mkdir -p uploads/after
    mkdir -p uploads/thumbnails
    mkdir -p uploads/PDF
fi

echo "=== データベース初期化 ==="

# 環境変数の確認とデータ保護モード
if [ "${PRESERVE_DATA}" = "true" ]; then
    echo "PRESERVE_DATA=true が設定されています。既存データ保護モードで実行します。"
    
    # データベースファイルが存在するかチェック
    if [ -f "instance/aircon_report.db" ]; then
        echo "既存のデータベースファイルが見つかりました。初期化をスキップします。"
    else
        echo "データベースファイルが存在しません。最低限の初期化を実行します。"
        python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
    fi
else
    echo "通常モードでデータベースを初期化します。"
    # データベースの初期化
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
fi

# デフォルト管理者の作成（環境変数で指定された場合）
if [ "${CREATE_DEFAULT_ADMIN}" = "true" ]; then
    echo "デフォルト管理者アカウントを作成します。"
    python -c "
from app import create_app, db
from app.models.user import User
from datetime import datetime
import os

app = create_app()
with app.app_context():
    # 既存の管理者をチェック
    admin_user = User.query.filter_by(role='admin').first()
    if admin_user is None:
        admin = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            name=os.environ.get('ADMIN_NAME', '管理者'),
            role='admin',
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print('デフォルト管理者アカウントを作成しました')
        print('ユーザー名:', admin.username)
        print('初期パスワード: 必ずログイン後に変更してください')
    else:
        print('管理者アカウントは既に存在します')
"
fi

echo "ビルドが完了しました。" 