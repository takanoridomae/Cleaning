"""
WSGI Entry Point for Render Deployment
"""

import os
import sys
from app import create_app

# アプリケーションの作成
app = create_app()

# ログ設定（Render環境用）
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    # コンソール出力用のハンドラー
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter)

    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("エアコンレポートアプリケーションが起動しました")

if __name__ == "__main__":
    # 開発環境での実行用
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
