from app import create_app, db
import sqlite3
import os

app = create_app()


def fix_database():
    # アプリケーション設定からデータベースパスを取得
    with app.app_context():
        db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_path.startswith("sqlite:///"):
            db_path = db_path[10:]  # sqlite:/// を削除
        else:
            db_path = "instance/aircon_report.db"  # デフォルトパス

    # 絶対パスに変換
    if not os.path.isabs(db_path):
        db_path = os.path.join(app.root_path, "..", db_path)

    print(f"データベースパス: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return

    # SQLiteデータベースに直接接続
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # work_detailsテーブルの構造を確認
        cursor.execute("PRAGMA table_info(work_details)")
        columns = cursor.fetchall()
        print("work_detailsテーブルの構造:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # 現在のデータを表示
        cursor.execute(
            "SELECT id, work_item_id, work_item_text, description, confirmation, report_id, property_id, air_conditioner_id FROM work_details"
        )
        rows = cursor.fetchall()
        print("\n現在のデータ:")
        for row in rows:
            print(f"ID: {row[0]}, air_conditioner_id: {row[7]}, property_id: {row[6]}")

        # エアコン情報を表示
        cursor.execute(
            "SELECT id, manufacturer, model_number, location, property_id FROM air_conditioners"
        )
        acs = cursor.fetchall()
        print("\nエアコン情報:")
        for ac in acs:
            print(f"ID: {ac[0]}, {ac[1]} {ac[2]} ({ac[3]}), 物件ID: {ac[4]}")

        # 作業内容データのエアコンIDに基づいてproperty_idを更新
        cursor.execute(
            """
            UPDATE work_details 
            SET property_id = (
                SELECT property_id 
                FROM air_conditioners 
                WHERE work_details.air_conditioner_id = air_conditioners.id
            )
            WHERE air_conditioner_id IS NOT NULL
        """
        )

        # 更新されたレコード数を表示
        print(f"\n{cursor.rowcount}件のレコードを更新しました。")

        # 更新後のデータを表示
        cursor.execute("SELECT id, air_conditioner_id, property_id FROM work_details")
        updated_rows = cursor.fetchall()
        print("\n更新後のデータ:")
        for row in updated_rows:
            print(f"ID: {row[0]}, air_conditioner_id: {row[1]}, property_id: {row[2]}")

        # 変更を保存
        conn.commit()
        print("\nデータベースの更新が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    fix_database()
