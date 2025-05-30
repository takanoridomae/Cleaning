#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
備考欄テキスト解析機能のテストスクリプト

このスクリプトは、物件登録画面の備考欄に貼り付けられるテキストデータから
お客様名、郵便番号、住所を抽出するJavaScript機能のPython版テストです。
"""

import re
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


def parse_note_text(text):
    """
    備考欄のテキストデータを解析する関数

    Args:
        text (str): 備考欄のテキストデータ

    Returns:
        dict: 解析結果 {'customer_name': '', 'postal_code': '', 'address': '', 'cleaned_note': ''}
    """
    result = {"customer_name": "", "postal_code": "", "address": "", "cleaned_note": ""}

    # 改行で分割して行ごとに処理
    lines = text.split("\n")
    remaining_lines = []  # 残す行のリスト

    for line in lines:
        line = line.strip()
        should_remove = False  # この行を削除するかどうか

        # お客様名の抽出（フルネーム対応）
        if not result["customer_name"]:
            # パターン1: 1行目の6列目から開始されるお客様名（実際のデータ形式）- 優先処理
            if line.startswith("お客様名"):
                # 「お客様名　中馬孝司さん」の形式 - 6列目（インデックス5）から名前開始
                if len(line) > 5:
                    name_part = line[5:].strip()  # 6列目以降を取得
                    # フルネーム抽出（「さん」「様」まで含めて取得後に除去）
                    name_match = re.search(
                        r"([一-龯ひらがなカタカナA-Za-z\s　]+?)(?:[様さ]|$)", name_part
                    )
                    if name_match:
                        name = name_match.group(1).strip()
                        # 空白文字を除去してフルネームにする
                        name = re.sub(r"[\s　]+", "", name)
                        if len(name) >= 2:
                            result["customer_name"] = name
                            should_remove = True

            # パターン2: 「田中太郎様」「田中太郎さん」
            if not result["customer_name"] and not should_remove:
                name_match = re.search(
                    r"([一-龯ひらがなカタカナA-Za-z\s　]+?)[様さ]", line
                )
                if name_match:
                    name = name_match.group(1).strip()
                    # 空白文字を除去してフルネームにする
                    name = re.sub(r"[\s　]+", "", name)
                    result["customer_name"] = name
                    should_remove = True

            # パターン3: 従来の「お客様名：田中太郎」形式
            if not result["customer_name"] and not should_remove:
                name_match = re.search(
                    r"(?:お客様名|顧客名|氏名|名前)[\s　]*[：:][\s　]*([^\s　：:]+)",
                    line,
                )
                if name_match:
                    name = name_match.group(1).strip()
                    # 「様」「さん」が含まれている場合は除去
                    name = re.sub(r"[様さ]$", "", name)
                    # 2文字以上で、ラベル部分が含まれていない場合のみ採用
                    if len(name) >= 2 and not re.search(
                        r"(お客様名|顧客名|氏名|名前)", name
                    ):
                        result["customer_name"] = name
                        should_remove = True

            # パターン4: 「田中　太郎」（姓名が分かれている）
            if not result["customer_name"] and not should_remove:
                name_match = re.search(
                    r"^([一-龯]{1,4})\s+([一-龯ひらがなカタカナ]{1,6})$", line
                )
                if name_match:
                    result["customer_name"] = name_match.group(1) + name_match.group(2)
                    should_remove = True

        # 郵便番号の抽出
        if not result["postal_code"] and not should_remove:
            postal_match = re.search(r"(?:〒\s*)?(\d{3}-?\d{4})", line)
            if postal_match:
                postal = postal_match.group(1)
                # ハイフンがない場合は追加
                if "-" not in postal and len(postal) == 7:
                    postal = postal[:3] + "-" + postal[3:]
                result["postal_code"] = postal
                # 郵便番号のみの行の場合は削除
                if re.match(r"^\s*(?:〒\s*)?\d{3}-?\d{4}\s*$", line):
                    should_remove = True

        # 住所の抽出
        if not result["address"] and not should_remove:
            # パターン1: 「住所：東京都新宿区...」のような形式
            address_match = re.search(
                r"住所[\s　]*[：:][\s　]*(?:〒\s*\d{3}-?\d{4}[\s　]*)?(.+)", line
            )
            if address_match:
                result["address"] = address_match.group(1).strip()
                should_remove = True

            # パターン2: 都道府県で始まる行を住所として認識
            if not result["address"]:
                prefectures = [
                    "北海道",
                    "青森県",
                    "岩手県",
                    "宮城県",
                    "秋田県",
                    "山形県",
                    "福島県",
                    "茨城県",
                    "栃木県",
                    "群馬県",
                    "埼玉県",
                    "千葉県",
                    "東京都",
                    "神奈川県",
                    "新潟県",
                    "富山県",
                    "石川県",
                    "福井県",
                    "山梨県",
                    "長野県",
                    "岐阜県",
                    "静岡県",
                    "愛知県",
                    "三重県",
                    "滋賀県",
                    "京都府",
                    "大阪府",
                    "兵庫県",
                    "奈良県",
                    "和歌山県",
                    "鳥取県",
                    "島根県",
                    "岡山県",
                    "広島県",
                    "山口県",
                    "徳島県",
                    "香川県",
                    "愛媛県",
                    "高知県",
                    "福岡県",
                    "佐賀県",
                    "長崎県",
                    "熊本県",
                    "大分県",
                    "宮崎県",
                    "鹿児島県",
                    "沖縄県",
                ]

                for pref in prefectures:
                    if line.startswith(pref):
                        # 郵便番号部分を除去
                        address = line
                        address = re.sub(r"(?:〒\s*)?\d{3}-?\d{4}\s*", "", address)
                        result["address"] = address.strip()
                        should_remove = True
                        break

            # パターン3: 市区町村で始まる可能性のある行
            if not result["address"] and not should_remove:
                city_match = re.search(r"([市区町村郡].+)", line)
                if city_match:
                    result["address"] = city_match.group(1).strip()
                    should_remove = True

        # 削除対象外の行は保持する
        if not should_remove and line:  # 空行は除外
            # 訪問日時とカレンダーデータも削除対象とする
            if line.startswith("訪問日時") or line.startswith("カレンダー"):
                should_remove = True

            if not should_remove:
                remaining_lines.append(line)

    # 備考欄のクリーンアップ（抽出した情報以外を残す）
    result["cleaned_note"] = "\n".join(remaining_lines)

    # お客様名が抽出できない場合は「一般」を設定
    if not result["customer_name"]:
        result["customer_name"] = "一般"

    return result


def test_note_parsing():
    """備考欄テキスト解析のテストケース"""
    test_cases = [
        {
            "name": "くらしのマーケット形式1",
            "text": """田中太郎様
〒635-0052
奈良県大和高田市奥田34-7
電話番号: 090-1234-5678
サービス: エアコンクリーニング""",
        },
        {
            "name": "くらしのマーケット形式2",
            "text": """お客様名：山田花子
住所：〒123-4567 東京都新宿区西新宿1-1-1
連絡先：080-9876-5432
希望日時：2025年6月1日""",
        },
        {
            "name": "分離形式",
            "text": """佐藤　次郎
6350052
奈良県大和高田市奥田34-7
作業内容：壁掛けエアコン2台""",
        },
        {
            "name": "複合形式",
            "text": """氏名: 鈴木一郎さん
郵便番号: 530-0001
大阪府大阪市北区梅田1-1-1
備考: 午前中希望""",
        },
        {
            "name": "改行なし形式",
            "text": "高橋美咲様 〒060-0001 北海道札幌市中央区北1条西1丁目 連絡先090-1111-2222",
        },
        {
            "name": "実際のデータ形式",
            "text": """お客様名　中馬孝司さん
訪問日時　2025年6月1日 13:00
カレンダー1 / 13:00～15:00 (2時間)
住所　〒635-0052 奈良県大和高田市奥田34-7
電話番号　09023813132""",
        },
    ]

    print("=== 備考欄テキスト解析テスト ===")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nテストケース {i}: {test_case['name']}")
        print(f"入力テキスト:\n{test_case['text']}")
        print("-" * 40)

        result = parse_note_text(test_case["text"])

        print(f"お客様名: {result['customer_name']}")
        print(f"郵便番号: {result['postal_code']}")
        print(f"住所: {result['address']}")
        print(f"クリーンアップ後の備考:\n{result['cleaned_note']}")

        # 物件名の生成例
        if result["customer_name"]:
            property_name = result["customer_name"] + "様　自宅"
            print(f"生成される物件名: {property_name}")

        # 検証
        success_count = sum(
            1 for key, value in result.items() if key != "cleaned_note" and value
        )
        if success_count >= 3:
            print("✅ 解析成功（3項目以上抽出）")
        elif success_count >= 2:
            print("✅ 解析成功（2項目以上抽出）")
        elif success_count >= 1:
            print("⚠️  解析部分成功（1項目抽出）")
        else:
            print("❌ 解析失敗")


def test_property_name_generation():
    """物件名生成のテスト"""
    print("\n=== 物件名生成テスト ===")

    test_names = ["田中太郎", "山田花子", "佐藤次郎", "鈴木一郎", "高橋美咲"]

    for name in test_names:
        property_name = f"{name}様　自宅"
        print(f"{name} → {property_name}")


if __name__ == "__main__":
    # 通常のテスト（お客様名あり）
    test_text = """お客様名　中馬孝司さん
訪問日時　2025年6月1日 13:00
カレンダー1 / 13:00～15:00 (2時間)
住所　〒635-0052 奈良県大和高田市奥田34-7
電話番号　09023813132"""

    print("=== 通常のテスト実行（お客様名あり） ===")
    print(f"入力テキスト:\n{test_text}")
    print("-" * 50)

    result = parse_note_text(test_text)

    print(f"お客様名: '{result['customer_name']}'")
    print(f"郵便番号: '{result['postal_code']}'")
    print(f"住所: '{result['address']}'")
    print(f"クリーンアップ後の備考:\n{result['cleaned_note']}")

    if result["customer_name"]:
        property_name = result["customer_name"] + "様　自宅"
        print(f"生成される物件名: '{property_name}'")

    # お客様名が抽出できない場合のテスト
    test_text_no_customer = """訪問日時　2025年6月1日 13:00
カレンダー1 / 13:00～15:00 (2時間)
住所　〒635-0052 奈良県大和高田市奥田34-7
電話番号　09023813132"""

    print("\n=== お客様名が抽出できない場合のテスト ===")
    print(f"入力テキスト:\n{test_text_no_customer}")
    print("-" * 50)

    result_no_customer = parse_note_text(test_text_no_customer)

    print(f"お客様名: '{result_no_customer['customer_name']}'")
    print(f"郵便番号: '{result_no_customer['postal_code']}'")
    print(f"住所: '{result_no_customer['address']}'")
    print(f"クリーンアップ後の備考:\n{result_no_customer['cleaned_note']}")

    if result_no_customer["customer_name"]:
        property_name = result_no_customer["customer_name"] + "様　自宅"
        print(f"生成される物件名: '{property_name}'")

    print("\n=== 修正内容の確認 ===")
    print("1. フルネーム抽出: '中馬孝司' が正しく抽出されているか")
    print("2. お客様名が抽出できない場合: '一般' が設定されているか")
    print("3. 備考欄クリーンアップ: 電話番号のみが残っているか")

    print("\n=== 処理完了 ===")
