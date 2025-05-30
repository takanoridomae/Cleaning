from app import create_app
import os
import sqlite3
import datetime
import click

app = create_app()


def backup_database(destination=None, verbose=True):
    """
    データベースの手動バックアップを作成する関数

    Args:
        destination: バックアップファイルの保存先パス（指定しない場合はデフォルトの場所に保存）
        verbose: 詳細メッセージを表示するかどうか

    Returns:
        成功した場合はバックアップファイルのパス、失敗した場合はNone
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
            if verbose:
                print(f"エラー: データベースファイルが見つかりません: {db_path}")
            return None

        # バックアップファイル名と保存先の設定
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if destination:
            # 保存先が指定されている場合
            backup_file = destination
            # ディレクトリが存在しない場合は作成
            backup_dir = os.path.dirname(backup_file)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
        else:
            # デフォルトの保存先を使用
            backup_dir = os.path.join(
                os.path.dirname(app.root_path), "db_backups", "manual"
            )
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            backup_file = os.path.join(backup_dir, f"aircon_report_{timestamp}.db")

        # データベースをバックアップ
        try:
            # データベース接続を確立してバックアップを作成
            conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_file)

            conn.backup(backup_conn)

            backup_conn.close()
            conn.close()

            if verbose:
                print(f"データベースバックアップを作成しました: {backup_file}")

            return backup_file

        except Exception as e:
            if verbose:
                print(f"バックアップ作成中にエラーが発生しました: {e}")
            return None

    except Exception as e:
        if verbose:
            print(f"バックアップ処理中にエラーが発生しました: {e}")
        return None


@click.command()
@click.option("--output", "-o", help="バックアップファイルの保存先パス")
def main(output):
    """データベースの手動バックアップを作成するコマンドラインツール"""
    backup_file = backup_database(output)
    if backup_file:
        print(f"バックアップが正常に作成されました: {backup_file}")
    else:
        print("バックアップの作成に失敗しました")
        exit(1)


if __name__ == "__main__":
    main()
