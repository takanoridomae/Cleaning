#!/usr/bin/env python3
"""
作業詳細レコードの作業金額を作業項目マスタから一括設定するデータ移行スクリプト
既存の作業詳細で work_amount が 0 または NULL で、work_item_id が設定されているレコードを対象とする
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db
from app.models.work_detail import WorkDetail
from app.models.work_item import WorkItem


def backup_work_details():
    """作業詳細データのバックアップを作成"""
    print("=== 作業詳細データのバックアップを作成中 ===")

    app = create_app()
    with app.app_context():
        try:
            # バックアップテーブル名（タイムスタンプ付き）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_table_name = f"work_details_backup_{timestamp}"

            with db.engine.connect() as connection:
                # 既存のバックアップテーブルを確認
                result = connection.execute(
                    db.text(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{backup_table_name}'"
                    )
                )
                if result.fetchone():
                    print(f"バックアップテーブル {backup_table_name} は既に存在します")
                    return backup_table_name

                # バックアップテーブルを作成
                connection.execute(
                    db.text(
                        f"CREATE TABLE {backup_table_name} AS SELECT * FROM work_details"
                    )
                )
                connection.commit()

                # バックアップされたレコード数を確認
                result = connection.execute(
                    db.text(f"SELECT COUNT(*) FROM {backup_table_name}")
                )
                backup_count = result.scalar()

                print(f"バックアップテーブル {backup_table_name} を作成しました")
                print(f"バックアップされたレコード数: {backup_count}件")

                return backup_table_name

        except Exception as e:
            print(f"バックアップ作成中にエラーが発生しました: {e}")
            return None


def analyze_migration_targets():
    """データ移行対象の分析"""
    print("=== データ移行対象の分析 ===")

    app = create_app()
    with app.app_context():
        try:
            # 全作業詳細レコード数
            total_count = WorkDetail.query.count()
            print(f"全作業詳細レコード数: {total_count}件")

            # work_amount が 0 または NULL のレコード数
            zero_amount_count = WorkDetail.query.filter(
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None))
            ).count()
            print(f"作業金額が0円またはNULLのレコード数: {zero_amount_count}件")

            # work_item_id が設定されていて、work_amount が 0 または NULL のレコード数
            target_count = WorkDetail.query.filter(
                WorkDetail.work_item_id.isnot(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).count()
            print(
                f"更新対象レコード数（work_item_id有り、作業金額0円またはNULL）: {target_count}件"
            )

            # work_item_id が NULL のレコード数
            no_work_item_count = WorkDetail.query.filter(
                WorkDetail.work_item_id.is_(None)
            ).count()
            print(f"作業項目ID未設定レコード数: {no_work_item_count}件")

            # 更新対象の詳細分析
            if target_count > 0:
                print("\n=== 更新対象の詳細分析 ===")
                target_details = (
                    WorkDetail.query.join(WorkItem)
                    .filter(
                        WorkDetail.work_item_id.isnot(None),
                        (WorkDetail.work_amount == 0)
                        | (WorkDetail.work_amount.is_(None)),
                    )
                    .all()
                )

                work_item_summary = {}
                for detail in target_details:
                    work_item_name = detail.work_item.name
                    work_item_amount = detail.work_item.work_amount

                    if work_item_name not in work_item_summary:
                        work_item_summary[work_item_name] = {
                            "count": 0,
                            "amount": work_item_amount,
                        }
                    work_item_summary[work_item_name]["count"] += 1

                print("作業項目別の更新対象:")
                for item_name, info in work_item_summary.items():
                    print(f"  {item_name}: {info['count']}件 → {info['amount']}円")

            return target_count

        except Exception as e:
            print(f"分析中にエラーが発生しました: {e}")
            return 0


def migrate_work_amounts(dry_run=True):
    """作業金額のデータ移行実行"""
    action = "プレビュー" if dry_run else "実行"
    print(f"=== 作業金額データ移行の{action} ===")

    app = create_app()
    with app.app_context():
        try:
            # 更新対象のレコードを取得
            target_details = (
                WorkDetail.query.join(WorkItem)
                .filter(
                    WorkDetail.work_item_id.isnot(None),
                    (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
                )
                .all()
            )

            print(f"更新対象レコード数: {len(target_details)}件")

            if len(target_details) == 0:
                print("更新対象のレコードがありません")
                return True

            updated_count = 0

            for detail in target_details:
                old_amount = detail.work_amount or 0
                new_amount = detail.work_item.work_amount

                print(
                    f"レポートID: {detail.report_id}, 作業項目: {detail.work_item.name}, {old_amount}円 → {new_amount}円"
                )

                if not dry_run:
                    detail.work_amount = new_amount
                    updated_count += 1

            if not dry_run:
                db.session.commit()
                print(f"\n実際に更新されたレコード数: {updated_count}件")
            else:
                print(f"\nプレビュー完了。実際の更新は行いませんでした。")
                print("実際に更新する場合は dry_run=False で実行してください")

            return True

        except Exception as e:
            if not dry_run:
                db.session.rollback()
            print(f"データ移行中にエラーが発生しました: {e}")
            return False


def verify_migration():
    """データ移行結果の検証"""
    print("=== データ移行結果の検証 ===")

    app = create_app()
    with app.app_context():
        try:
            # 移行後の状況確認
            total_count = WorkDetail.query.count()
            zero_amount_count = WorkDetail.query.filter(
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None))
            ).count()
            target_remaining = WorkDetail.query.filter(
                WorkDetail.work_item_id.isnot(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).count()

            print(f"全作業詳細レコード数: {total_count}件")
            print(f"作業金額が0円またはNULLのレコード数: {zero_amount_count}件")
            print(
                f"未更新レコード数（work_item_id有り、作業金額0円またはNULL）: {target_remaining}件"
            )

            # 作業金額の合計を確認
            from sqlalchemy import func

            total_amount = (
                db.session.query(func.sum(WorkDetail.work_amount)).scalar() or 0
            )
            print(f"全作業金額の合計: {total_amount:,}円")

            if target_remaining == 0:
                print("✓ データ移行が正常に完了しました")
                return True
            else:
                print("⚠ 一部のレコードが未更新です")
                return False

        except Exception as e:
            print(f"検証中にエラーが発生しました: {e}")
            return False


def main():
    """メイン処理"""
    print("作業詳細レコードの作業金額データ移行スクリプト")
    print("=" * 50)

    # 1. 現状分析
    target_count = analyze_migration_targets()

    if target_count == 0:
        print("更新対象のレコードがありません。処理を終了します。")
        return

    # 2. バックアップ作成
    backup_table = backup_work_details()
    if not backup_table:
        print("バックアップの作成に失敗しました。処理を中断します。")
        return

    # 3. プレビュー実行
    print("\n" + "=" * 50)
    if not migrate_work_amounts(dry_run=True):
        print("プレビューでエラーが発生しました。処理を中断します。")
        return

    # 4. 実行確認
    print("\n" + "=" * 50)
    response = input("実際にデータ移行を実行しますか？ (y/N): ")

    if response.lower() != "y":
        print("データ移行をキャンセルしました。")
        return

    # 5. 実際の移行実行
    print("\n" + "=" * 50)
    if migrate_work_amounts(dry_run=False):
        # 6. 結果検証
        print("\n" + "=" * 50)
        verify_migration()
        print(f"\nバックアップテーブル: {backup_table}")
        print("データ移行が完了しました。")
    else:
        print("データ移行に失敗しました。")


if __name__ == "__main__":
    main()
