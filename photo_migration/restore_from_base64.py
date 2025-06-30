#!/usr/bin/env python3
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
    
    print(f"📁 チャンクファイル数: {len(chunk_files)}個")
    
    # base64データを結合
    base64_data = ""
    for chunk_file in chunk_files:
        print(f"   📄 読み込み中: {chunk_file.name}")
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
        print(f"   - ファイル名: {output_file}")
        print(f"   - サイズ: {file_size_mb:.2f}MB")
        
        return True
        
    except Exception as e:
        print(f"❌ 復元エラー: {e}")
        return False

if __name__ == "__main__":
    success = restore_zip_file()
    if success:
        print("🎉 ZIPファイルの復元が完了しました！")
        print("次のステップ: python extract_photos_on_render.py")
    else:
        print("❌ 復元に失敗しました")
        exit(1)
