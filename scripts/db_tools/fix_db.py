import sqlite3
import os

# データベースのパス
db_path = "./instance/aircon_report.db"

# データベースが存在することを確認
if not os.path.exists(db_path):
    print(f"データベースファイルが見つかりません: {db_path}")
    exit(1)

# データベースに接続
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # テーブルのカラム情報を取得
    print("work_detailsテーブルの現在の構造:")
    cursor.execute("PRAGMA table_info(work_details);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # バックアップテーブルを削除（既に存在していれば）
    cursor.execute("DROP TABLE IF EXISTS work_details_backup;")

    # 現在のテーブルをバックアップ
    cursor.execute("CREATE TABLE work_details_backup AS SELECT * FROM work_details;")
    print("既存のテーブルをバックアップしました")

    # work_itemカラムのNOT NULL制約を除いた新しいテーブル定義を作成
    columns_def = []
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        if col_name == "work_item" or col_name == "property_id":
            # work_itemとproperty_idカラムのNOT NULL制約を削除
            columns_def.append(f"{col_name} {col_type}")
        elif col[5] == 1:  # PrimaryKey
            columns_def.append(f"{col_name} {col_type} PRIMARY KEY")
        elif col[3] == 1:  # NOT NULL
            columns_def.append(f"{col_name} {col_type} NOT NULL")
        else:
            columns_def.append(f"{col_name} {col_type}")

    # 元のテーブルを削除
    cursor.execute("DROP TABLE work_details;")

    # 新しいテーブルを作成（work_itemのNOT NULL制約なし）
    create_table_sql = f"CREATE TABLE work_details ({', '.join(columns_def)});"
    print(f"新しいテーブル定義: {create_table_sql}")
    cursor.execute(create_table_sql)

    # バックアップからデータを復元
    cursor.execute("INSERT INTO work_details SELECT * FROM work_details_backup;")
    print("データを復元しました")

    # 結果の確認
    print("\nwork_detailsテーブルの新しい構造:")
    cursor.execute("PRAGMA table_info(work_details);")
    columns = cursor.fetchall()
    for col in columns:
        print(
            f"{col[0]}: {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}"
        )

    # バックアップテーブルを削除
    cursor.execute("DROP TABLE work_details_backup;")
    print("バックアップテーブルを削除しました")

    # 変更を確定
    conn.commit()
    print("テーブルの修正が完了しました")

except Exception as e:
    conn.rollback()
    print(f"エラーが発生しました: {e}")
finally:
    conn.close()
