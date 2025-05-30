import sqlite3
import os
from datetime import datetime

# データベースのパス
db_path = "./instance/aircon_report.db"

# バックアップファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"./instance/aircon_report_backup_{timestamp}.db"

# データベースが存在することを確認
if not os.path.exists(db_path):
    print(f"データベースファイルが見つかりません: {db_path}")
    exit(1)

# バックアップの作成
import shutil

shutil.copy2(db_path, backup_path)
print(f"データベースをバックアップしました: {backup_path}")

# データベースに接続
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # 列名でアクセスできるように設定
cursor = conn.cursor()

try:
    # レポートとwork_detailsの不整合を修正
    print("===== work_detailsテーブルのproperty_idとair_conditioner_idの修正 =====")

    # レポートとwork_detailsを取得
    cursor.execute(
        """
        SELECT wd.id as work_detail_id, wd.report_id, wd.property_id as wd_property_id, 
               wd.air_conditioner_id, r.property_id as report_property_id
        FROM work_details wd
        JOIN reports r ON wd.report_id = r.id
    """
    )
    records = cursor.fetchall()

    property_mismatches = 0
    ac_invalid = 0

    # 各レコードをチェックして修正
    for record in records:
        work_detail_id = record["work_detail_id"]
        wd_property_id = record["wd_property_id"]
        report_property_id = record["report_property_id"]
        air_conditioner_id = record["air_conditioner_id"]

        # property_idの不一致チェック
        property_mismatch = False
        if wd_property_id != report_property_id:
            property_mismatch = True
            property_mismatches += 1
            print(
                f"work_detail_id={work_detail_id}: property_id不一致 (work_detail: {wd_property_id}, report: {report_property_id})"
            )

        # air_conditioner_idの有効性チェック
        ac_exists = True
        if air_conditioner_id is not None:
            cursor.execute(
                "SELECT id, property_id FROM air_conditioners WHERE id = ?",
                (air_conditioner_id,),
            )
            ac_record = cursor.fetchone()

            if ac_record is None:
                ac_exists = False
                ac_invalid += 1
                print(
                    f"work_detail_id={work_detail_id}: 無効なair_conditioner_id={air_conditioner_id}"
                )
            elif ac_record["property_id"] != report_property_id:
                ac_exists = False
                ac_invalid += 1
                print(
                    f"work_detail_id={work_detail_id}: air_conditioner_id={air_conditioner_id}のproperty_id不一致 (エアコン: {ac_record['property_id']}, レポート: {report_property_id})"
                )

        # 修正が必要な場合
        if property_mismatch or not ac_exists:
            # property_idを報告書の物件IDで更新
            cursor.execute(
                """
                UPDATE work_details
                SET property_id = ?,
                    air_conditioner_id = ?
                WHERE id = ?
            """,
                (
                    report_property_id,
                    air_conditioner_id if ac_exists else None,
                    work_detail_id,
                ),
            )
            print(
                f"work_detail_id={work_detail_id}を修正: property_id={report_property_id}, air_conditioner_id={air_conditioner_id if ac_exists else None}"
            )

    # 結果サマリー
    print(f"\n修正サマリー:")
    print(f"- property_id不一致: {property_mismatches}件")
    print(f"- 無効なair_conditioner_id: {ac_invalid}件")

    # air_conditioner_idがNULLのレコードを確認
    cursor.execute(
        "SELECT COUNT(*) as count FROM work_details WHERE air_conditioner_id IS NULL"
    )
    null_count = cursor.fetchone()["count"]
    print(f"- air_conditioner_idがNULL: {null_count}件")

    # 変更を確定
    conn.commit()
    print("\nデータベースの修正が完了しました")

except Exception as e:
    conn.rollback()
    print(f"エラーが発生しました: {e}")
finally:
    conn.close()
