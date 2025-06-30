#!/usr/bin/env python3
"""
ZIPファイルをbase64エンコードして小さなチャンクに分割
GitHubの制限（100MB未満）でアップロード可能にする
"""

import base64
import math
from pathlib import Path


def create_base64_chunks():
    """ZIPファイルをbase64エンコードして分割"""

    zip_file = "photo_migration_20250630_210456.zip"

    if not Path(zip_file).exists():
        print(f"❌ {zip_file} が見つかりません")
        return False

    print(f"📦 {zip_file} をbase64エンコード中...")

    # ファイルを読み込んでbase64エンコード
    with open(zip_file, "rb") as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode("utf-8")

    # チャンクサイズ（50MBのbase64データ = 約37MBの元データ）
    chunk_size = 50 * 1024 * 1024  # 50MB
    total_chunks = math.ceil(len(base64_data) / chunk_size)

    print(f"📊 分割情報:")
    print(f"   - 元ファイルサイズ: {len(file_data)/1024/1024:.2f}MB")
    print(f"   - base64サイズ: {len(base64_data)/1024/1024:.2f}MB")
    print(f"   - チャンク数: {total_chunks}個")

    # チャンクファイルを作成
    for i in range(total_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(base64_data))
        chunk_data = base64_data[start:end]

        chunk_filename = f"photo_base64_chunk_{i+1:02d}.txt"
        with open(chunk_filename, "w", encoding="utf-8") as f:
            f.write(chunk_data)

        chunk_size_mb = len(chunk_data.encode("utf-8")) / 1024 / 1024
        print(f"   ✅ {chunk_filename} ({chunk_size_mb:.2f}MB)")

    # 復元スクリプトを作成
    restore_script = f'''#!/usr/bin/env python3
"""
base64チャンクからZIPファイルを復元
"""

import base64
from pathlib import Path

def restore_zip_file():
    """base64チャンクからZIPファイルを復元"""
    
    print("📦 base64チャンクからZIPファイルを復元中...")
    
    # チャンクファイルを収集
    chunk_files = sorted(list(Path(".").glob("photo_base64_chunk_*.txt")))
    
    if not chunk_files:
        print("❌ base64チャンクファイルが見つかりません")
        return False
    
    print(f"📁 チャンクファイル数: {{len(chunk_files)}}個")
    
    # base64データを結合
    base64_data = ""
    for chunk_file in chunk_files:
        print(f"   📄 読み込み中: {{chunk_file.name}}")
        with open(chunk_file, 'r', encoding='utf-8') as f:
            base64_data += f.read()
    
    # base64デコードしてZIPファイルを復元
    try:
        file_data = base64.b64decode(base64_data)
        
        output_file = "photo_migration_20250630_210456.zip"
        with open(output_file, 'wb') as f:
            f.write(file_data)
        
        file_size_mb = len(file_data) / 1024 / 1024
        print(f"✅ ZIPファイル復元完了:")
        print(f"   - ファイル名: {{output_file}}")
        print(f"   - サイズ: {{file_size_mb:.2f}}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 復元エラー: {{e}}")
        return False

if __name__ == "__main__":
    success = restore_zip_file()
    if success:
        print("🎉 ZIPファイルの復元が完了しました！")
        print("次のステップ: python extract_photos_on_render.py")
    else:
        print("❌ 復元に失敗しました")
        exit(1)
'''

    with open("restore_from_base64.py", "w", encoding="utf-8") as f:
        f.write(restore_script)

    print(f"\n✅ base64チャンク分割完了!")
    print(f"📄 復元スクリプト: restore_from_base64.py")
    print(f"\n📋 次のステップ:")
    print(f"1. git add photo_base64_chunk_*.txt restore_from_base64.py")
    print(f"2. git commit -m 'Add base64 chunks for photo migration'")
    print(f"3. git push origin main")
    print(f"4. Render Shell: python restore_from_base64.py")
    print(f"5. Render Shell: python extract_photos_on_render.py")

    return True


if __name__ == "__main__":
    create_base64_chunks()
