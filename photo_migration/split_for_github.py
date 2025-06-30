#!/usr/bin/env python3
"""
GitHub用ファイル分割スクリプト
336MBのZIPファイルを90MB以下のチャンクに分割してGitHubにアップロード可能にします
"""

import os
import math
from pathlib import Path


def split_file(file_path, chunk_size_mb=90):
    """
    ファイルを指定サイズのチャンクに分割

    Args:
        file_path: 分割するファイルのパス
        chunk_size_mb: チャンクサイズ（MB）
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ ファイルが見つかりません: {file_path}")
        return False

    # ファイルサイズ情報
    file_size = file_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    # 必要なチャンク数を計算
    num_chunks = math.ceil(file_size / chunk_size_bytes)

    print(f"📦 ファイル分割情報:")
    print(f"   - 元ファイル: {file_path.name}")
    print(f"   - ファイルサイズ: {file_size_mb:.2f}MB")
    print(f"   - チャンクサイズ: {chunk_size_mb}MB")
    print(f"   - 分割数: {num_chunks}個")

    # 分割実行
    with open(file_path, "rb") as source_file:
        for chunk_num in range(num_chunks):
            # チャンクファイル名
            chunk_filename = f"{file_path.stem}.part{chunk_num + 1:02d}"
            chunk_path = file_path.parent / chunk_filename

            # チャンクサイズの計算（最後のチャンクは小さくなる可能性）
            if chunk_num == num_chunks - 1:
                # 最後のチャンク
                remaining_size = file_size - (chunk_num * chunk_size_bytes)
                current_chunk_size = remaining_size
            else:
                current_chunk_size = chunk_size_bytes

            # チャンクファイルの作成
            with open(chunk_path, "wb") as chunk_file:
                data = source_file.read(current_chunk_size)
                chunk_file.write(data)

            chunk_size_mb_actual = current_chunk_size / (1024 * 1024)
            print(f"   ✅ 作成: {chunk_filename} ({chunk_size_mb_actual:.2f}MB)")

    print(f"\n🎉 ファイル分割完了！")
    return True


def create_merge_script():
    """
    Render上でファイルを結合するスクリプトを作成
    """
    merge_script_content = '''#!/usr/bin/env python3
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
    print(f"\n✅ ファイル結合完了:")
    print(f"   - 結合ファイル: {output_file}")
    print(f"   - 総サイズ: {total_size_mb:.2f}MB")
    
    # 分割ファイルの削除（オプション）
    print("\n🗑️  分割ファイルを削除しますか？ (y/N)")
    # 自動実行のため、削除はコメントアウト
    # for part_file in part_files:
    #     part_file.unlink()
    #     print(f"   削除: {part_file.name}")
    
    return True

if __name__ == "__main__":
    success = merge_files()
    if success:
        print("🎉 ファイル結合が正常に完了しました！")
        print("\n次のステップ:")
        print("python extract_photos_on_render.py")
    else:
        print("❌ 結合に失敗しました")
        exit(1)
'''

    script_path = Path("merge_on_render.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(merge_script_content)

    print(f"📜 結合スクリプトを作成: {script_path}")
    return str(script_path)


def main():
    """メイン処理"""
    print("=== GitHub用ファイル分割ツール ===\n")

    # ZIPファイルを検索
    zip_files = list(Path(".").glob("photo_migration_*.zip"))

    if not zip_files:
        print("❌ 移行ZIPファイルが見つかりません")
        return

    zip_file = zip_files[0]

    # ファイル分割
    print("📦 ファイル分割を開始...")
    success = split_file(zip_file, chunk_size_mb=90)

    if not success:
        print("❌ ファイル分割に失敗しました")
        return

    # 結合スクリプトの作成
    print("\n📜 Render用結合スクリプトを作成...")
    merge_script = create_merge_script()

    # .gitignoreの確認と更新
    gitignore_path = Path("../.gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_content = f.read()

        if "photo_migration/" not in gitignore_content:
            print("\n📝 .gitignoreに除外設定を追加しています...")
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Photo migration files (temporary)\n")
                f.write("photo_migration/*.zip\n")
                f.write("photo_migration/*.part*\n")

    print("\n" + "=" * 50)
    print("🎉 GitHub用ファイル分割が完了しました！")
    print("\n📋 次のステップ:")
    print("1. GitHubに分割ファイルをプッシュ:")
    print("   git add photo_migration/")
    print("   git commit -m 'Add split photo migration files'")
    print("   git push origin main")
    print("\n2. Render Shellで実行:")
    print("   python merge_on_render.py")
    print("   python extract_photos_on_render.py")
    print("\n3. 完了後にファイル削除:")
    print("   git rm photo_migration/*.part*")
    print("   git commit -m 'Remove temporary migration files'")


if __name__ == "__main__":
    main()
