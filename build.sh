#!/usr/bin/env bash
# Render Build Script

set -o errexit  # exit on error

# パッケージのインストール
pip install -r requirements.txt

# データベースディレクトリの作成
mkdir -p instance

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

echo "ビルドが完了しました。" 