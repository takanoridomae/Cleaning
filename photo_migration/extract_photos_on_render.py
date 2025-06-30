#!/usr/bin/env python3
"""
Render上での写真データ展開スクリプト

使用方法:
1. 移行ZIPファイルをRenderにアップロード
2. このスクリプトを実行してZIPを展開
3. Persistent Diskに写真データを配置
"""

import os
import zipfile
import json
import shutil
from pathlib import Path

def extract_photos():
    """写真アーカイブを展開してPersistent Diskに配置"""
    
    # Persistent Diskパス
    persistent_disk = Path("/opt/render/project/src/uploads")
    
    if not persistent_disk.exists():
        print("❌ Persistent Diskが見つかりません")
        print("   Mount Path: /opt/render/project/src/uploads が設定されているか確認してください")
        return False
    
    # 移行ZIPファイルを検索
    zip_files = list(Path(".").glob("photo_migration_*.zip"))
    
    if not zip_files:
        print("❌ 移行ZIPファイルが見つかりません")
        print("   photo_migration_*.zip ファイルを同じディレクトリに配置してください")
        return False
    
    zip_file = zip_files[0]  # 最初に見つかったファイルを使用
    print(f"📦 移行ファイル: {zip_file}")
    
    # ZIPファイルを展開
    with zipfile.ZipFile(zip_file, 'r') as zipf:
        # メタデータを読み込み
        try:
            metadata_content = zipf.read("migration_metadata.json")
            metadata = json.loads(metadata_content.decode('utf-8'))
            
            print(f"📊 移行データ情報:")
            print(f"   - 総ファイル数: {metadata['total_files']}件")
            print(f"   - 総サイズ: {metadata['total_size_mb']}MB")
            print(f"   - 施工前: {metadata['before_count']}件")
            print(f"   - 施工後: {metadata['after_count']}件")
            
        except KeyError:
            print("⚠️  メタデータファイルが見つかりません（続行します）")
        
        # Persistent Diskに展開
        print("📂 Persistent Diskに写真を展開中...")
        zipf.extractall(persistent_disk)
    
    # 展開結果の確認
    before_dir = persistent_disk / "before"
    after_dir = persistent_disk / "after"
    
    before_count = len(list(before_dir.rglob("*.jpg"))) + len(list(before_dir.rglob("*.jpeg"))) + len(list(before_dir.rglob("*.png")))
    after_count = len(list(after_dir.rglob("*.jpg"))) + len(list(after_dir.rglob("*.jpeg"))) + len(list(after_dir.rglob("*.png")))
    
    print(f"✅ 写真データの移行が完了しました:")
    print(f"   - 施工前写真: {before_count}件")
    print(f"   - 施工後写真: {after_count}件")
    print(f"   - 配置先: {persistent_disk}")
    
    # 権限設定
    os.system(f"chmod -R 755 {persistent_disk}")
    
    return True

if __name__ == "__main__":
    success = extract_photos()
    if success:
        print("🎉 写真データの移行が正常に完了しました！")
    else:
        print("❌ 移行に失敗しました")
        exit(1)
