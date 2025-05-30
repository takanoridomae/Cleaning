from app import create_app, db
from app.models.property import Property
from app.models.air_conditioner import AirConditioner
from app.models.report import Report
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from app.models.work_item import WorkItem
from flask_migrate import upgrade, migrate, init, Migrate
import sqlite3

# アプリケーションコンテキストを作成
app = create_app()
app_context = app.app_context()
app_context.push()

# マイグレーションを実行
print("マイグレーションを実行します...")
with app.app_context():
    # Flask-Migrateの初期化
    migrate_instance = Migrate(app, db)

    # propertiesテーブルのカラム削除
    # ALTERコマンドを直接実行
    with db.engine.connect() as conn:
        try:
            print("propertiesテーブルからproperty_typeカラムを削除...")
            conn.execute(db.text("ALTER TABLE properties DROP COLUMN property_type"))
            print("property_typeカラムを削除しました")
        except Exception as e:
            print(f"property_typeカラム削除エラー: {e}")

        try:
            print("propertiesテーブルからroomsカラムを削除...")
            conn.execute(db.text("ALTER TABLE properties DROP COLUMN rooms"))
            print("roomsカラムを削除しました")
        except Exception as e:
            print(f"roomsカラム削除エラー: {e}")

        # reportsテーブルからJSON形式のカラムを削除
        try:
            print("reportsテーブルのカラムを調整中...")

            # 既存のカラムのチェック
            db_path = "./instance/aircon_report.db"
            check_conn = sqlite3.connect(db_path)
            check_cursor = check_conn.cursor()
            check_cursor.execute("PRAGMA table_info(reports);")
            columns = [col[1] for col in check_cursor.fetchall()]
            check_conn.close()

            # 既存のdateカラムが存在する場合は更新せず、存在しない場合は追加
            if "date" not in columns:
                conn.execute(db.text("ALTER TABLE reports ADD COLUMN date DATE"))
                print("date カラムを追加しました")

            print("reportsテーブルの更新が完了しました")
        except Exception as e:
            print(f"reportsテーブル更新エラー: {e}")

        # work_detailsテーブルの調整
        try:
            print("work_detailsテーブルのカラムを調整中...")

            # work_detailsテーブルが存在するかチェック
            db_path = "./instance/aircon_report.db"
            check_conn = sqlite3.connect(db_path)
            check_cursor = check_conn.cursor()
            check_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='work_details';"
            )
            table_exists = check_cursor.fetchone() is not None

            if table_exists:
                # カラムの存在確認
                check_cursor.execute("PRAGMA table_info(work_details);")
                columns = [col[1] for col in check_cursor.fetchall()]

                # work_itemカラムが存在する場合、そのデータをwork_item_textに移行
                if "work_item" in columns and "work_item_text" not in columns:
                    # 念のためカラム追加
                    try:
                        conn.execute(
                            db.text(
                                "ALTER TABLE work_details ADD COLUMN work_item_text VARCHAR(100)"
                            )
                        )
                        print("work_item_text カラムを追加しました")
                    except Exception as e:
                        print(f"work_item_text カラム追加エラー: {e}")

                    # データ移行
                    try:
                        conn.execute(
                            db.text(
                                "UPDATE work_details SET work_item_text = work_item"
                            )
                        )
                        print(
                            "work_itemカラムからwork_item_textカラムへデータを移行しました"
                        )
                    except Exception as e:
                        print(f"データ移行エラー: {e}")

                # work_item_idカラムが存在しない場合は追加
                if "work_item_id" not in columns:
                    try:
                        conn.execute(
                            db.text(
                                "ALTER TABLE work_details ADD COLUMN work_item_id INTEGER"
                            )
                        )
                        print("work_item_id カラムを追加しました")
                    except Exception as e:
                        print(f"work_item_id カラム追加エラー: {e}")

                # air_conditioner_idカラムが存在しない場合は追加
                if "air_conditioner_id" not in columns:
                    try:
                        conn.execute(
                            db.text(
                                "ALTER TABLE work_details ADD COLUMN air_conditioner_id INTEGER"
                            )
                        )
                        print("air_conditioner_id カラムを追加しました")
                    except Exception as e:
                        print(f"air_conditioner_id カラム追加エラー: {e}")

                # property_idをNULLABLEに変更 (SQLiteでALTER COLUMNはサポートされていないため、
                # 既に作成済みのテーブルのNOT NULL制約は変更できません。
                # ただし、新しいレコードではNULLを許容するようになります)
                print(
                    "property_idカラムはNULLを許容するようになりました（既存のレコードは変更されません）"
                )

                # work_itemカラムの制約を変更するためのテーブル再作成
                if "work_item" in columns:
                    try:
                        print("work_itemカラムをNULLABLEに変更中...")

                        # バックアップテーブルが既に存在する場合は削除
                        try:
                            conn.execute(
                                db.text("DROP TABLE IF EXISTS work_details_backup")
                            )
                            print("既存のバックアップテーブルを削除しました")
                        except Exception as e:
                            print(f"バックアップテーブル削除エラー: {e}")

                        # 既存のデータをバックアップ
                        conn.execute(
                            db.text(
                                "CREATE TABLE work_details_backup AS SELECT * FROM work_details"
                            )
                        )
                        print("既存のデータをバックアップしました")

                        # テーブルの構造を取得
                        check_cursor.execute("PRAGMA table_info(work_details);")
                        table_info = check_cursor.fetchall()

                        # work_itemカラムのNOT NULL制約を除いた新しいテーブル作成
                        columns_def = []
                        for col in table_info:
                            col_name = col[1]
                            col_type = col[2]
                            if col_name == "work_item":
                                # NOT NULL制約を除去
                                columns_def.append(f"{col_name} {col_type}")
                            elif col[5] == 1:  # PrimaryKey
                                columns_def.append(f"{col_name} {col_type} PRIMARY KEY")
                            elif col[3] == 1:  # NOT NULL
                                columns_def.append(f"{col_name} {col_type} NOT NULL")
                            else:
                                columns_def.append(f"{col_name} {col_type}")

                        # テーブルをドロップして再作成
                        conn.execute(db.text("DROP TABLE work_details"))
                        create_table_sql = (
                            f"CREATE TABLE work_details ({', '.join(columns_def)})"
                        )
                        conn.execute(db.text(create_table_sql))
                        print("work_detailsテーブルを再作成しました")

                        # データを元のテーブルに戻す
                        conn.execute(
                            db.text(
                                "INSERT INTO work_details SELECT * FROM work_details_backup"
                            )
                        )
                        print("データを復元しました")

                        # バックアップテーブルを削除
                        conn.execute(db.text("DROP TABLE work_details_backup"))
                        print("バックアップテーブルを削除しました")

                        print("work_itemカラムのNULLABLE化が完了しました")
                    except Exception as e:
                        print(f"work_itemカラムのNULLABLE化エラー: {e}")

            check_conn.close()
            print("work_detailsテーブルの更新が完了しました")
        except Exception as e:
            print(f"work_detailsテーブル更新エラー: {e}")

    # 作業項目テーブルの作成
    try:
        print("work_itemsテーブルを作成...")
        db.metadata.create_all(bind=db.engine, tables=[WorkItem.__table__])

        # 初期データの登録
        print("作業項目の初期データを登録...")
        default_items = [
            "エアコンクリーニング",
            "フィルター洗浄",
            "内部洗浄",
            "熱交換器洗浄",
            "ファン洗浄",
            "ドレンパン洗浄",
            "防カビ処理",
            "動作確認",
            "冷媒補充",
            "部品交換",
        ]

        for item_name in default_items:
            # 既に存在するか確認
            existing = WorkItem.query.filter_by(name=item_name).first()
            if not existing:
                item = WorkItem(name=item_name, is_active=True)
                db.session.add(item)

        db.session.commit()
        print("work_itemsテーブルを作成し、初期データを登録しました")
    except Exception as e:
        print(f"work_itemsテーブル作成エラー: {e}")

    # 新しいテーブルの作成
    try:
        print("work_timesテーブルを作成...")
        db.metadata.create_all(bind=db.engine, tables=[WorkTime.__table__])
        print("work_timesテーブルを作成しました")
    except Exception as e:
        print(f"work_timesテーブル作成エラー: {e}")

    try:
        print("work_detailsテーブルを作成...")
        db.metadata.create_all(bind=db.engine, tables=[WorkDetail.__table__])
        print("work_detailsテーブルを作成しました")
    except Exception as e:
        print(f"work_detailsテーブル作成エラー: {e}")

    # air_conditionersテーブルの作成
    try:
        print("air_conditionersテーブルを作成...")
        db.metadata.create_all(bind=db.engine, tables=[AirConditioner.__table__])
        print("air_conditionersテーブルを作成しました")
    except Exception as e:
        print(f"air_conditionersテーブル作成エラー: {e}")

print("マイグレーション完了")

# SQLiteデータベースに接続して結果を確認
import sqlite3

db_path = "./instance/aircon_report.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# テーブル一覧を表示
print("\n=== テーブル一覧 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

# propertiesテーブルの構造を表示
print("\n=== propertiesテーブルの構造 ===")
cursor.execute("PRAGMA table_info(properties);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

# reportsテーブルの構造を表示
print("\n=== reportsテーブルの構造 ===")
cursor.execute("PRAGMA table_info(reports);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

# work_itemsテーブルの構造を表示
print("\n=== work_itemsテーブルの構造 ===")
cursor.execute("PRAGMA table_info(work_items);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

# work_itemsテーブルのデータを表示
print("\n=== work_itemsテーブルのデータ ===")
cursor.execute("SELECT * FROM work_items;")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("データがありません")

# work_timesテーブルの構造を表示
print("\n=== work_timesテーブルの構造 ===")
cursor.execute("PRAGMA table_info(work_times);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

# work_detailsテーブルの構造を表示
print("\n=== work_detailsテーブルの構造 ===")
cursor.execute("PRAGMA table_info(work_details);")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[0]}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")

conn.close()
app_context.pop()
