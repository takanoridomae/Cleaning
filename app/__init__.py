from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from markupsafe import Markup
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# データベースインスタンスの作成
db = SQLAlchemy()
migrate = Migrate()


def create_app(test_config=None):
    # アプリケーションの作成と設定
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI="sqlite:///"
        + os.path.join(app.instance_path, "aircon_report.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_timeout": 30,  # 接続プールタイムアウト
            "pool_recycle": 3600,  # 接続の再利用間隔（1時間）
            "pool_pre_ping": True,  # 接続の事前チェック
            "connect_args": {
                "timeout": 30,  # SQLite接続タイムアウト
                "check_same_thread": False,  # マルチスレッド対応
            },
        },
        UPLOAD_FOLDER=os.path.join(os.path.dirname(app.root_path), "uploads"),
        # Mail設定
        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
        MAIL_USE_TLS=os.environ.get("MAIL_USE_TLS", "True").lower() == "true",
        MAIL_USE_SSL=os.environ.get("MAIL_USE_SSL", "False").lower() == "true",
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get("MAIL_DEFAULT_SENDER"),
        # 通知設定
        NOTIFICATION_ENABLED=os.environ.get("NOTIFICATION_ENABLED", "True").lower()
        == "true",
        NOTIFICATION_CHECK_INTERVAL=int(
            os.environ.get("NOTIFICATION_CHECK_INTERVAL", 60)
        ),
    )

    if test_config is None:
        # インスタンス設定を読み込む（存在する場合）
        app.config.from_pyfile("config.py", silent=True)
    else:
        # テスト設定を読み込む
        app.config.from_mapping(test_config)

    # インスタンスフォルダが確実に存在するようにする
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # アップロードフォルダが確実に存在するようにする
    try:
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "before"))
        os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "after"))
    except OSError:
        pass

    # データベース初期化
    db.init_app(app)
    migrate.init_app(app, db)

    # Jinja2フィルターの登録
    @app.template_filter("nl2br")
    def nl2br_filter(text):
        """テキスト内の改行をHTMLのbrタグに変換するフィルター"""
        if text:
            return Markup(text.replace("\n", "<br>"))
        return ""

    # モデルのインポート（循環インポートを避けるため、ここで行う）
    from app.models import (
        user,
        customer,
        property,
        report,
        photo,
        air_conditioner,
        schedule,
    )

    # ルートの登録
    from app.routes import (
        main,
        auth,
        customers,
        properties,
        reports,
        air_conditioners,
        schedules,
        notifications,
        admin_import,
    )

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(properties.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(air_conditioners.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(notifications.bp)
    app.register_blueprint(admin_import.bp)

    app.add_url_rule("/", endpoint="index")

    # エラーハンドラーの登録
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error/500.html"), 500

    # アップロードされた写真を提供するルートを追加
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        upload_folder = os.path.join(os.path.dirname(app.root_path), "uploads")
        return send_from_directory(upload_folder, filename)

    # 通知スケジューラーの初期化
    if not app.config.get("TESTING", False):
        try:
            from app.services.scheduler_service import scheduler_service

            scheduler_service.start()
        except Exception as e:
            print(f"スケジューラー開始エラー: {e}")

    return app
