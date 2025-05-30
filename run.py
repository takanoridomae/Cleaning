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
            # データベース接続を確立してバックアップを作成
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_file)

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


if __name__ == "__main__":
    # 起動時にバックアップを作成
    create_db_backup(app, "startup")

    # 日次バックアップスレッドを開始
    start_daily_backup_thread()

    # アプリケーションを起動
    app.run(debug=True, host="0.0.0.0")
