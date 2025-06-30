#!/usr/bin/env python3
"""
作業項目マスタ（work_items）に作業金額を設定するスクリプト
一般的なエアコンクリーニング業界の相場を基に金額を設定
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db
from app.models.work_item import WorkItem


def get_default_work_amounts():
    """作業項目別のデフォルト金額設定を返す"""
    return {
        # エアコンクリーニング関連
        "エアコンクリーニング": 12000,
        "通常クリーニング": 12000,
        "おそうじ機能付きクリーニング": 18000,
        "室外機クリーニング": 5000,
        # 洗浄作業別
        "洗浄_フィルター": 2000,
        "洗浄_ケース": 3000,
        "洗浄_熱交換器": 5000,
        "洗浄_ファン": 4000,
        "洗浄_室外機": 5000,
        "洗浄_ドレンパン": 3000,
        "洗浄_送風口": 2000,
        # 分解作業
        "分解_前面パネル": 1000,
        "分解_フィルター": 500,
        "分解_ファンカバー": 2000,
        # 確認・点検
        "動作確認": 1000,
        "点検": 1500,
        "清掃確認": 500,
        # その他作業
        "他_部品交換": 3000,
        "他_防カビ処理": 2000,
        "他_確認と修理": 5000,
        "他_抗菌コート": 3000,
        "他_消臭処理": 2000,
        # 追加サービス
        "抗菌コート": 3000,
        "消臭処理": 2000,
        "防カビスプレー": 1500,
    }


def analyze_current_work_items():
    """現在の作業項目を分析"""
    print("=== 現在の作業項目マスタの分析 ===")

    app = create_app()
    with app.app_context():
        try:
            work_items = WorkItem.query.order_by(WorkItem.name).all()

            print(f"作業項目総数: {len(work_items)}件")
            print("\n現在の作業項目一覧:")

            zero_amount_count = 0
            for item in work_items:
                status = "✓" if item.work_amount > 0 else "×"
                if item.work_amount == 0:
                    zero_amount_count += 1
                print(f"  {status} {item.name}: {item.work_amount:,}円")

            print(f"\n金額未設定の作業項目数: {zero_amount_count}件")

            return work_items

        except Exception as e:
            print(f"分析中にエラーが発生しました: {e}")
            return []


def set_work_item_amounts(dry_run=True):
    """作業項目に金額を設定"""
    action = "プレビュー" if dry_run else "実行"
    print(f"\n=== 作業項目金額設定の{action} ===")

    app = create_app()
    with app.app_context():
        try:
            default_amounts = get_default_work_amounts()
            work_items = WorkItem.query.all()

            updated_count = 0
            not_found_items = []

            for item in work_items:
                old_amount = item.work_amount

                # デフォルト金額設定から該当する金額を検索
                new_amount = None

                # 完全一致で検索
                if item.name in default_amounts:
                    new_amount = default_amounts[item.name]
                else:
                    # 部分一致で検索
                    for key, amount in default_amounts.items():
                        if key in item.name or item.name in key:
                            new_amount = amount
                            break

                if new_amount is not None and old_amount != new_amount:
                    print(f"  {item.name}: {old_amount:,}円 → {new_amount:,}円")

                    if not dry_run:
                        item.work_amount = new_amount
                        updated_count += 1
                elif new_amount is None and old_amount == 0:
                    not_found_items.append(item.name)
                    print(f"  ？ {item.name}: 該当する金額設定が見つかりません")

            if not_found_items:
                print(f"\n金額設定が見つからない作業項目:")
                for name in not_found_items:
                    print(f"  - {name}")
                print("\nこれらの項目には手動で金額を設定してください。")

            if not dry_run:
                db.session.commit()
                print(f"\n実際に更新された作業項目数: {updated_count}件")
            else:
                print(f"\nプレビュー完了。実際の更新は行いませんでした。")

            return True

        except Exception as e:
            if not dry_run:
                db.session.rollback()
            print(f"金額設定中にエラーが発生しました: {e}")
            return False


def suggest_manual_amounts():
    """手動設定が必要な項目に推奨金額を提案"""
    print("\n=== 手動設定推奨項目 ===")

    app = create_app()
    with app.app_context():
        try:
            default_amounts = get_default_work_amounts()
            work_items = WorkItem.query.filter_by(work_amount=0).all()

            suggestions = []

            for item in work_items:
                # デフォルト設定にない項目の推奨金額を提案
                if item.name not in default_amounts:
                    # キーワードベースで推奨金額を提案
                    if "クリーニング" in item.name:
                        suggestions.append(
                            (item.name, 12000, "一般的なクリーニング相場")
                        )
                    elif "洗浄" in item.name:
                        suggestions.append((item.name, 3000, "洗浄作業相場"))
                    elif "分解" in item.name:
                        suggestions.append((item.name, 1500, "分解作業相場"))
                    elif "確認" in item.name or "点検" in item.name:
                        suggestions.append((item.name, 1000, "確認・点検作業相場"))
                    elif "他_" in item.name:
                        suggestions.append((item.name, 3000, "その他作業相場"))
                    else:
                        suggestions.append((item.name, 2000, "一般作業相場"))

            if suggestions:
                print("推奨金額:")
                for name, amount, reason in suggestions:
                    print(f"  {name}: {amount:,}円 ({reason})")

                print("\n作業項目管理画面から手動で設定することをお勧めします。")
                print("URL: /reports/work_items")

        except Exception as e:
            print(f"推奨金額の提案中にエラーが発生しました: {e}")


def main():
    """メイン処理"""
    print("作業項目マスタ金額設定スクリプト")
    print("=" * 50)

    # 1. 現状分析
    work_items = analyze_current_work_items()

    if not work_items:
        print("作業項目が見つかりません。処理を終了します。")
        return

    # 2. プレビュー実行
    print("\n" + "=" * 50)
    if not set_work_item_amounts(dry_run=True):
        print("プレビューでエラーが発生しました。処理を中断します。")
        return

    # 3. 推奨金額の提案
    suggest_manual_amounts()

    # 4. 実行確認
    print("\n" + "=" * 50)
    response = input("実際に金額設定を実行しますか？ (y/N): ")

    if response.lower() != "y":
        print("金額設定をキャンセルしました。")
        return

    # 5. 実際の設定実行
    print("\n" + "=" * 50)
    if set_work_item_amounts(dry_run=False):
        print("\n作業項目マスタの金額設定が完了しました。")
        print("次に scripts/migrations/migrate_work_amounts.py を実行して")
        print("作業詳細レコードに金額を反映してください。")
    else:
        print("金額設定に失敗しました。")


if __name__ == "__main__":
    main()
