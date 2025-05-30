from app import create_app, db
import sqlite3
import os

# アプリケーションコンテキストを作成
app = create_app()
with app.app_context():
    # データベースファイルのパスを取得
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")

    # 相対パスを絶対パスに変換
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.instance_path, db_path)

    print(f"データベースパス: {db_path}")

    # SQLiteデータベースに接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # filepathカラムを追加
    try:
        cursor.execute("ALTER TABLE photos ADD COLUMN filepath VARCHAR(500)")
        print("filepathカラムが正常に追加されました")
    except Exception as e:
        print(f"エラー: {e}")

    # 変更をコミットして接続を閉じる
    conn.commit()
    conn.close()

    print("完了しました。サーバーを再起動してください。")
