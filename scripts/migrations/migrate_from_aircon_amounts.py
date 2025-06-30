#!/usr/bin/env python3
"""
air_conditionersテーブルのtotal_amountを基に作業詳細に金額を設定するデータ移行スクリプト
既存の作業詳細で work_amount が 0 または NULL で、air_conditioner_id が設定されているレコードを対象とする
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db
from app.models.work_detail import WorkDetail
from app.models.work_item import WorkItem
from app.models.air_conditioner import AirConditioner


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

            # エアコンが紐づいている作業詳細レコード数
            with_aircon_count = WorkDetail.query.filter(
                WorkDetail.air_conditioner_id.isnot(None)
            ).count()
            print(f"エアコンが紐づく作業詳細レコード数: {with_aircon_count}件")

            # 更新対象レコード数（エアコンIDがあり、作業金額が0またはNULL）
            target_count = WorkDetail.query.filter(
                WorkDetail.air_conditioner_id.isnot(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).count()
            print(
                f"更新対象レコード数（エアコンID有り、作業金額0円またはNULL）: {target_count}件"
            )

            # エアコンIDが設定されていない作業詳細
            no_aircon_count = WorkDetail.query.filter(
                WorkDetail.air_conditioner_id.is_(None)
            ).count()
            print(f"エアコンID未設定レコード数: {no_aircon_count}件")

            # エアコンテーブルの金額状況
            from sqlalchemy import func

            ac_total_amount = (
                AirConditioner.query.with_entities(
                    func.sum(AirConditioner.total_amount)
                ).scalar()
                or 0
            )
            ac_avg_amount = (
                AirConditioner.query.with_entities(
                    func.avg(AirConditioner.total_amount)
                ).scalar()
                or 0
            )
            ac_count = AirConditioner.query.count()

            print(f"\nエアコンテーブルの金額状況:")
            print(f"  エアコン総数: {ac_count}件")
            print(f"  金額合計: {ac_total_amount:,}円")
            print(f"  平均金額: {ac_avg_amount:,.0f}円")

            # 更新対象の詳細分析
            if target_count > 0:
                print("\n=== 更新対象の詳細分析 ===")
                target_details = (
                    WorkDetail.query.join(AirConditioner)
                    .filter(
                        WorkDetail.air_conditioner_id.isnot(None),
                        (WorkDetail.work_amount == 0)
                        | (WorkDetail.work_amount.is_(None)),
                    )
                    .limit(10)
                    .all()
                )

                print("更新対象レコードのサンプル（最初の10件）:")
                for detail in target_details:
                    ac = detail.air_conditioner
                    work_item_name = (
                        detail.work_item.name
                        if detail.work_item
                        else detail.work_item_text or "未設定"
                    )
                    print(f"  報告書ID: {detail.report_id}, 作業項目: {work_item_name}")
                    print(
                        f"    エアコン: {ac.manufacturer} {ac.model_number} ({ac.location})"
                    )
                    print(f"    エアコン金額: {ac.total_amount:,}円")

            return target_count

        except Exception as e:
            print(f"分析中にエラーが発生しました: {e}")
            return 0


def calculate_work_amount_from_aircon(aircon_total_amount, work_count_for_aircon):
    """エアコンの金額を作業数で分割して作業金額を計算"""
    if work_count_for_aircon == 0:
        return 0

    # エアコンの金額を作業数で等分割
    work_amount = int(aircon_total_amount / work_count_for_aircon)

    # 最低金額を保証（1000円未満は1000円にする）
    if work_amount < 1000 and aircon_total_amount > 0:
        work_amount = 1000

    return work_amount


def migrate_from_aircon_amounts(dry_run=True):
    """エアコン金額からの作業金額データ移行実行"""
    action = "プレビュー" if dry_run else "実行"
    print(f"=== エアコン金額からの作業金額データ移行の{action} ===")

    app = create_app()
    with app.app_context():
        try:
            # 更新対象のレコードを取得
            target_details = WorkDetail.query.filter(
                WorkDetail.air_conditioner_id.isnot(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).all()

            print(f"更新対象レコード数: {len(target_details)}件")

            if len(target_details) == 0:
                print("更新対象のレコードがありません")
                return True

            # エアコンごとの作業数をカウント
            aircon_work_counts = {}
            for detail in target_details:
                ac_id = detail.air_conditioner_id
                if ac_id not in aircon_work_counts:
                    aircon_work_counts[ac_id] = 0
                aircon_work_counts[ac_id] += 1

            updated_count = 0
            total_migrated_amount = 0

            print(f"\nエアコンごとの作業分割:")
            for detail in target_details:
                ac = detail.air_conditioner
                old_amount = detail.work_amount or 0
                work_count = aircon_work_counts[ac.id]
                new_amount = calculate_work_amount_from_aircon(
                    ac.total_amount, work_count
                )

                work_item_name = (
                    detail.work_item.name
                    if detail.work_item
                    else detail.work_item_text or "未設定"
                )

                print(f"  報告書ID: {detail.report_id}, 作業項目: {work_item_name}")
                print(
                    f"    エアコン金額: {ac.total_amount:,}円 ÷ {work_count}作業 = {new_amount:,}円"
                )

                if not dry_run:
                    detail.work_amount = new_amount
                    updated_count += 1

                total_migrated_amount += new_amount

            if not dry_run:
                db.session.commit()
                print(f"\n実際に更新されたレコード数: {updated_count}件")
                print(f"移行された金額の合計: {total_migrated_amount:,}円")
            else:
                print(f"\nプレビュー完了。実際の更新は行いませんでした。")
                print(f"移行予定金額の合計: {total_migrated_amount:,}円")
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
                WorkDetail.air_conditioner_id.isnot(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).count()

            print(f"全作業詳細レコード数: {total_count}件")
            print(f"作業金額が0円またはNULLのレコード数: {zero_amount_count}件")
            print(
                f"未更新レコード数（エアコンID有り、作業金額0円またはNULL）: {target_remaining}件"
            )

            # 作業金額の合計を確認
            from sqlalchemy import func

            work_total_amount = (
                db.session.query(func.sum(WorkDetail.work_amount)).scalar() or 0
            )
            aircon_total_amount = (
                db.session.query(func.sum(AirConditioner.total_amount)).scalar() or 0
            )

            print(f"全作業金額の合計: {work_total_amount:,}円")
            print(f"エアコン金額の合計: {aircon_total_amount:,}円")
            print(f"金額差異: {abs(work_total_amount - aircon_total_amount):,}円")

            if target_remaining == 0:
                print("✓ データ移行が正常に完了しました")
                return True
            else:
                print("⚠ 一部のレコードが未更新です")
                return False

        except Exception as e:
            print(f"検証中にエラーが発生しました: {e}")
            return False


def handle_no_aircon_details():
    """エアコンIDが設定されていない作業詳細の対応提案"""
    print("=== エアコンID未設定作業詳細の対応 ===")

    app = create_app()
    with app.app_context():
        try:
            no_aircon_details = WorkDetail.query.filter(
                WorkDetail.air_conditioner_id.is_(None),
                (WorkDetail.work_amount == 0) | (WorkDetail.work_amount.is_(None)),
            ).all()

            if len(no_aircon_details) == 0:
                print("エアコンID未設定で金額が0円の作業詳細はありません")
                return

            print(f"エアコンID未設定で金額が0円の作業詳細: {len(no_aircon_details)}件")

            # 作業項目別の集計
            work_item_summary = {}
            for detail in no_aircon_details:
                work_item_name = (
                    detail.work_item.name
                    if detail.work_item
                    else detail.work_item_text or "未設定"
                )
                if work_item_name not in work_item_summary:
                    work_item_summary[work_item_name] = 0
                work_item_summary[work_item_name] += 1

            print("作業項目別の未設定件数:")
            for item_name, count in work_item_summary.items():
                print(f"  {item_name}: {count}件")

            print("\n対応方法:")
            print("1. 報告書編集画面で適切なエアコンを選択")
            print("2. 作業項目マスタで金額を設定し、作業項目選択で自動反映")
            print("3. 手動で作業金額を入力")

        except Exception as e:
            print(f"エラーが発生しました: {e}")


def main():
    """メイン処理"""
    print("エアコン金額からの作業詳細金額データ移行スクリプト")
    print("=" * 60)

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
    print("\n" + "=" * 60)
    if not migrate_from_aircon_amounts(dry_run=True):
        print("プレビューでエラーが発生しました。処理を中断します。")
        return

    # 4. エアコンID未設定作業詳細の対応提案
    print("\n" + "=" * 60)
    handle_no_aircon_details()

    # 5. 実行確認
    print("\n" + "=" * 60)
    response = input("実際にデータ移行を実行しますか？ (y/N): ")

    if response.lower() != "y":
        print("データ移行をキャンセルしました。")
        return

    # 6. 実際の移行実行
    print("\n" + "=" * 60)
    if migrate_from_aircon_amounts(dry_run=False):
        # 7. 結果検証
        print("\n" + "=" * 60)
        verify_migration()
        print(f"\nバックアップテーブル: {backup_table}")
        print("データ移行が完了しました。")

        # 8. 後続処理の案内
        print("\n次のステップ:")
        print("1. エアコンID未設定の作業詳細は手動で対応してください")
        print("2. 受注明細一覧で金額が正しく表示されることを確認してください")
        print("3. 今後の新規作業は作業項目マスタの金額が自動設定されます")
    else:
        print("データ移行に失敗しました。")


if __name__ == "__main__":
    main()
