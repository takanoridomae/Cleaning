from app import create_app
import os
import sqlite3
import shutil
import datetime
import click
import glob

app = create_app()


def list_backups():
    """利用可能なバックアップファイルの一覧を表示する"""
    # バックアップディレクトリのパスを取得
    backup_root = os.path.join(os.path.dirname(app.root_path), "db_backups")

    if not os.path.exists(backup_root):
        print("バックアップディレクトリが見つかりません")
        return []

    # すべてのバックアップファイルを検索
    all_backups = []

    # 各タイプのバックアップディレクトリをチェック
    for backup_type in ["startup", "daily", "manual"]:
        backup_dir = os.path.join(backup_root, backup_type)
        if os.path.exists(backup_dir):
            # .dbファイルを検索
            db_files = glob.glob(os.path.join(backup_dir, "*.db"))
            # ファイル名でソート
            db_files.sort(reverse=True)

            for db_file in db_files:
                backup_time = os.path.getmtime(db_file)
                backup_time_str = datetime.datetime.fromtimestamp(backup_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                backup_size = os.path.getsize(db_file) / (1024 * 1024)  # MBに変換

                all_backups.append(
                    {
                        "path": db_file,
                        "type": backup_type,
                        "time": backup_time,
                        "time_str": backup_time_str,
                        "size": backup_size,
                        "filename": os.path.basename(db_file),
                    }
                )

    # 時間でソート（新しい順）
    all_backups.sort(key=lambda x: x["time"], reverse=True)
    return all_backups


def restore_database(backup_file, target_db=None, backup_current=True, verbose=True):
    """
    バックアップからデータベースを復元する関数

    Args:
        backup_file: 復元に使用するバックアップファイルのパス
        target_db: 復元先のデータベースパス（指定しない場合は現在のDBを上書き）
        backup_current: 現在のDBをバックアップするかどうか
        verbose: 詳細メッセージを表示するかどうか

    Returns:
        成功した場合はTrue、失敗した場合はFalse
    """
    try:
        # バックアップファイルの存在確認
        if not os.path.exists(backup_file):
            if verbose:
                print(f"エラー: バックアップファイルが見つかりません: {backup_file}")
            return False

        # 現在のデータベースのパスを取得
        with app.app_context():
            current_db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            if current_db_path.startswith("sqlite:///"):
                current_db_path = current_db_path[10:]  # sqlite:/// を削除
            else:
                current_db_path = "instance/aircon_report.db"  # デフォルトパス

        # 絶対パスに変換
        if not os.path.isabs(current_db_path):
            current_db_path = os.path.join(app.root_path, "..", current_db_path)

        # 復元先のDBパスを設定
        if target_db is None:
            target_db = current_db_path

        # 現在のDBをバックアップ
        if backup_current and os.path.exists(target_db):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(
                os.path.dirname(app.root_path), "db_backups", "before_restore"
            )

            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            current_backup = os.path.join(
                backup_dir, f"aircon_report_before_restore_{timestamp}.db"
            )

            try:
                # データベース接続を確立して現在のDBをバックアップ
                conn = sqlite3.connect(target_db)
                backup_conn = sqlite3.connect(current_backup)

                conn.backup(backup_conn)

                backup_conn.close()
                conn.close()

                if verbose:
                    print(f"復元前の現在のDBをバックアップしました: {current_backup}")
            except Exception as e:
                if verbose:
                    print(f"現在のDBのバックアップ中にエラーが発生しました: {e}")
                    print(
                        "警告: 元のデータベースのバックアップに失敗しましたが、復元処理を続行します"
                    )

        # データベースの復元
        try:
            # アプリケーションがデータベースを使用している場合があるため、コピー前に接続を閉じる
            with app.app_context():
                db_session = getattr(app, "db_session", None)
                if db_session:
                    db_session.remove()

            # バックアップからデータベースを復元
            src_conn = sqlite3.connect(backup_file)
            dest_conn = sqlite3.connect(target_db)

            src_conn.backup(dest_conn)

            src_conn.close()
            dest_conn.close()

            if verbose:
                print(f"データベースを正常に復元しました: {backup_file} -> {target_db}")

            return True

        except Exception as e:
            if verbose:
                print(f"データベース復元中にエラーが発生しました: {e}")
            return False

    except Exception as e:
        if verbose:
            print(f"復元処理中にエラーが発生しました: {e}")
        return False


@click.command()
@click.option("--list", "-l", is_flag=True, help="利用可能なバックアップ一覧を表示")
@click.option("--backup", "-b", help="復元に使用するバックアップファイルのパス")
@click.option(
    "--target",
    "-t",
    help="復元先のデータベースパス（指定しない場合は現在のDBを上書き）",
)
@click.option("--no-backup-current", is_flag=True, help="現在のDBをバックアップしない")
def main(list, backup, target, no_backup_current):
    """データベースのバックアップから復元するコマンドラインツール"""
    if list:
        # バックアップ一覧を表示
        backups = list_backups()
        if not backups:
            print("利用可能なバックアップが見つかりません")
            return

        print("利用可能なバックアップ:")
        for i, backup in enumerate(backups):
            print(
                f"{i+1}. [{backup['type']}] {backup['filename']} ({backup['time_str']}, {backup['size']:.2f}MB)"
            )

        # 復元するバックアップを選択
        choice = input(
            "\n復元するバックアップを選択してください（番号）、またはキャンセルする場合は q を入力: "
        )
        if choice.lower() == "q":
            print("復元操作をキャンセルしました")
            return

        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(backups):
                selected_backup = backups[choice_idx]

                # 確認
                print(
                    f"\n選択されたバックアップ: {selected_backup['filename']} ({selected_backup['time_str']})"
                )
                confirm = input("このバックアップから復元を行いますか？ [y/N]: ")

                if confirm.lower() == "y":
                    success = restore_database(
                        selected_backup["path"], target, not no_backup_current
                    )
                    if not success:
                        print("バックアップからの復元に失敗しました")
                        exit(1)
                else:
                    print("復元操作をキャンセルしました")
            else:
                print("無効な選択です")
        except ValueError:
            print("無効な入力です")

    elif backup:
        # バックアップファイルが直接指定された場合
        if not os.path.exists(backup):
            print(f"エラー: 指定されたバックアップファイルが見つかりません: {backup}")
            exit(1)

        # 確認
        print(f"バックアップファイル {backup} からデータベースを復元します")
        if not target:
            print("警告: 現在のデータベースが上書きされます")

        confirm = input("続行しますか？ [y/N]: ")
        if confirm.lower() == "y":
            success = restore_database(backup, target, not no_backup_current)
            if not success:
                print("バックアップからの復元に失敗しました")
                exit(1)
        else:
            print("復元操作をキャンセルしました")
    else:
        # 引数が指定されていない場合
        print(
            "利用可能なバックアップを表示するには --list オプションを使用してください"
        )
        print(
            "特定のバックアップから復元するには --backup オプションを使用してください"
        )


if __name__ == "__main__":
    main()
