#!/usr/bin/env python3
"""
Render上でのファイル結合スクリプト
分割されたファイルを元の形に結合します
"""

import os
from pathlib import Path

def merge_files():
    """分割ファイルを結合"""
    
    # 分割ファイルを検索
    current_dir = Path(".")
    part_files = sorted(list(current_dir.glob("photo_migration_*.part*")))
    
    if not part_files:
        print("❌ 分割ファイルが見つかりません")
        print("   photo_migration_*.part* ファイルを確認してください")
        return False
    
    # 結合ファイル名を決定
    base_name = part_files[0].name.split('.part')[0]
    output_file = f"{base_name}.zip"
    
    print(f"📦 ファイル結合情報:")
    print(f"   - 分割ファイル数: {len(part_files)}個")
    print(f"   - 出力ファイル: {output_file}")
    
    # ファイル結合
    total_size = 0
    with open(output_file, 'wb') as output:
        for part_file in part_files:
            print(f"   📁 結合中: {part_file.name}")
            with open(part_file, 'rb') as part:
                data = part.read()
                output.write(data)
                total_size += len(data)
    
    # 結果確認
    total_size_mb = total_size / (1024 * 1024)
    print(f"
✅ ファイル結合完了:")
    print(f"   - 結合ファイル: {output_file}")
    print(f"   - 総サイズ: {total_size_mb:.2f}MB")
    
    # 分割ファイルの削除（オプション）
    print("
🗑️  分割ファイルを削除しますか？ (y/N)")
    # 自動実行のため、削除はコメントアウト
    # for part_file in part_files:
    #     part_file.unlink()
    #     print(f"   削除: {part_file.name}")
    
    return True

if __name__ == "__main__":
    success = merge_files()
    if success:
        print("🎉 ファイル結合が正常に完了しました！")
        print("
次のステップ:")
        print("python extract_photos_on_render.py")
    else:
        print("❌ 結合に失敗しました")
        exit(1)
