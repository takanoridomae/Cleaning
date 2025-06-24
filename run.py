from app import create_app, db
import click
from flask.cli import with_appcontext
import os
import shutil
import datetime
import time
import sqlite3

app = create_app()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """データベースを初期化し、テーブルを作成します。"""
    db.create_all()
    click.echo("データベースを初期化しました。")


app.cli.add_command(init_db_command)


def create_db_backup(app, backup_type="startup"):
    """
    データベースのバックアップを作成する関数
    backup_type: "startup"(起動時), "daily"(日次), "manual"(手動)
    """
    try:
        # データベースパスを取得
        with app.app_context():
            db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if db_path.startswith("sqlite:///"):
                db_path = db_path[10:]  # sqlite:/// を削除
                # URIパラメータ（?timeout=30など）を除去
                if "?" in db_path:
                    db_path = db_path.split("?")[0]
            else:
                db_path = "instance/aircon_report.db"  # デフォルトパス

        # 絶対パスに変換
        if not os.path.isabs(db_path):
            db_path = os.path.join(app.root_path, "..", db_path)

        # データベースファイルの存在確認
        if not os.path.exists(db_path):
            print(f"警告: データベースファイルが見つかりません: {db_path}")
            return False

        # バックアップディレクトリの作成
        backup_dir = os.path.join(os.path.dirname(app.root_path), "db_backups")
        backup_type_dir = os.path.join(backup_dir, backup_type)

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        if not os.path.exists(backup_type_dir):
            os.makedirs(backup_type_dir)

        # バックアップファイル名の作成（タイムスタンプ付き）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_type_dir, f"aircon_report_{timestamp}.db")

        # データベースの一時的なロックを避けるためにコピーを作成
        try:
            # データベース接続を確立してバックアップを作成（タイムアウト設定）
            conn = sqlite3.connect(db_path, timeout=30.0)
            backup_conn = sqlite3.connect(backup_file, timeout=30.0)

            # WALモードでの整合性を保つために、まずチェックポイントを実行
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            # バックアップを作成
            conn.backup(backup_conn)

            backup_conn.close()
            conn.close()

            print(f"データベースバックアップを作成しました: {backup_file}")

            # バックアップの数を制限（タイプごとに異なる保存数）
            max_backups = {
                "startup": 5,  # 起動時は最新5つを保持
                "daily": 30,  # 日次は30日分を保持
                "manual": 10,  # 手動は最新10個を保持
            }

            # 古いバックアップを削除
            backups = sorted(
                [
                    os.path.join(backup_type_dir, f)
                    for f in os.listdir(backup_type_dir)
                    if f.endswith(".db")
                ]
            )

            if len(backups) > max_backups.get(backup_type, 5):
                for old_backup in backups[: -max_backups.get(backup_type, 5)]:
                    os.remove(old_backup)
                    print(f"古いバックアップを削除しました: {old_backup}")

            return True

        except Exception as e:
            print(f"バックアップ作成中にエラーが発生しました: {e}")
            return False

    except Exception as e:
        print(f"バックアップ処理中にエラーが発生しました: {e}")
        return False


# スケジュールされたデイリーバックアップを開始するスレッド
def start_daily_backup_thread():
    """毎日午前3時にバックアップを実行するスレッドを開始"""
    import threading

    def run_daily_backup():
        while True:
            # 現在時刻を取得
            now = datetime.datetime.now()

            # 次の午前3時までの秒数を計算
            target_time = datetime.datetime(now.year, now.month, now.day, 3, 0, 0)
            if now.hour >= 3:
                target_time += datetime.timedelta(days=1)

            # 次の実行時間までスリープ
            sleep_seconds = (target_time - now).total_seconds()
            time.sleep(sleep_seconds)

            # バックアップを実行
            print(f"日次バックアップを開始します: {datetime.datetime.now()}")
            create_db_backup(app, "daily")

    # デーモンスレッドとして起動
    backup_thread = threading.Thread(target=run_daily_backup, daemon=True)
    backup_thread.start()
    print("日次バックアップスケジューラを起動しました")


def init_database():
    """本番環境でのデータベース初期化（既存データ保護）"""
    with app.app_context():
        try:
            # データベースファイルが存在しない場合、テーブルを作成
            db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if db_path.startswith("sqlite:///"):
                db_path = db_path[10:]  # sqlite:/// を削除
                if "?" in db_path:
                    db_path = db_path.split("?")[0]

            tables_created = False
            needs_initial_data = False

            if not os.path.exists(db_path):
                print("データベースファイルが存在しません。テーブルを作成します...")
                db.create_all()
                tables_created = True
                needs_initial_data = True
                print("データベースの初期化が完了しました。")
            else:
                # テーブルが存在するかチェック
                try:
                    from app.models.customer import Customer
                    from app.models.user import User

                    customer_count = Customer.query.count()
                    user_count = User.query.count()

                    print(
                        f"既存データベース確認: ユーザー{user_count}件, 顧客{customer_count}件"
                    )

                    # データが存在する場合は初期化をスキップ
                    if user_count > 0:
                        print("既存データが検出されました。初期化をスキップします。")
                        return  # 初期化処理を完全にスキップ
                    else:
                        needs_initial_data = True

                except Exception as e:
                    print(f"テーブル確認エラー: {e}")
                    print("テーブルが存在しません。テーブルを作成します...")
                    db.create_all()
                    tables_created = True
                    needs_initial_data = True
                    print("データベースの初期化が完了しました。")

            # 初期ユーザーを作成（データが存在しない場合のみ）
            if needs_initial_data:
                create_initial_user(True)

        except Exception as e:
            print(f"データベース初期化エラー: {e}")


def create_initial_user(force_create=False):
    """初期管理者ユーザーを作成"""
    try:
        from app.models.user import User
        from datetime import datetime

        # 既存のユーザーをチェック
        user_count = User.query.count()

        # 既存のadminユーザーをチェック
        existing_admin = User.query.filter_by(username="admin").first()

        if user_count == 0 or (force_create and not existing_admin):
            # 管理者ユーザーを作成
            admin = User(
                username="admin",
                email="admin@example.com",
                name="管理者",
                role="admin",
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            admin.set_password("admin123")

            # データベースに保存
            db.session.add(admin)
            db.session.commit()

            print("初期管理者ユーザーを作成しました")
            print("ユーザー名: admin")
            print("パスワード: admin123")
            print("※本番運用前に必ずパスワードを変更してください")
        elif existing_admin:
            print(f"管理者ユーザー（admin）は既に存在します")
        else:
            print(f"ユーザーは既に存在します（{user_count}人）")

    except Exception as e:
        print(f"初期ユーザー作成エラー: {e}")


if __name__ == "__main__":
    # 本番環境でのデータベース初期化制御
    # FORCE_DB_INIT環境変数が明示的に設定された場合のみ初期化を実行
    if os.environ.get("RENDER"):
        if os.environ.get("FORCE_DB_INIT") == "true":
            print("FORCE_DB_INIT環境変数により、データベース初期化を強制実行...")
            init_database()
        else:
            print("Render環境: データベース初期化はスキップされます")
            print("※初期化が必要な場合は FORCE_DB_INIT=true を設定してください")

    # デプロイ時はポート番号を環境変数から取得
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
