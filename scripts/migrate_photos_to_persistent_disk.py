#!/usr/bin/env python3
"""
写真データのPersistent Disk移行スクリプト

既存のローカル写真データをRenderのPersistent Diskに移行するためのツール
ローカル環境で実行して、写真ファイルをZIPアーカイブとして準備し、
Renderにアップロード可能な形式にします。
"""

import os
import sys
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def scan_local_photos():
    """
    ローカルのuploadsディレクトリから写真ファイルをスキャン

    Returns:
        dict: 写真ファイルの情報
    """
    uploads_dir = project_root / "uploads"
    photo_info = {"before": [], "after": [], "total_size": 0, "total_files": 0}

    if not uploads_dir.exists():
        print("❌ uploadsディレクトリが見つかりません")
        return photo_info

    # beforeフォルダのスキャン
    before_dir = uploads_dir / "before"
    if before_dir.exists():
        for file_path in before_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
            ]:
                size = file_path.stat().st_size
                relative_path = file_path.relative_to(before_dir)

                photo_info["before"].append(
                    {
                        "path": str(file_path),
                        "relative_path": str(relative_path),
                        "size": size,
                        "name": file_path.name,
                    }
                )
                photo_info["total_size"] += size
                photo_info["total_files"] += 1

    # afterフォルダのスキャン
    after_dir = uploads_dir / "after"
    if after_dir.exists():
        for file_path in after_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
            ]:
                size = file_path.stat().st_size
                relative_path = file_path.relative_to(after_dir)

                photo_info["after"].append(
                    {
                        "path": str(file_path),
                        "relative_path": str(relative_path),
                        "size": size,
                        "name": file_path.name,
                    }
                )
                photo_info["total_size"] += size
                photo_info["total_files"] += 1

    return photo_info


def create_migration_archive():
    """
    写真データの移行用ZIPアーカイブを作成

    Returns:
        str: 作成されたZIPファイルのパス
    """
    photo_info = scan_local_photos()

    if photo_info["total_files"] == 0:
        print("📂 移行対象の写真ファイルが見つかりません")
        return None

    # 出力ディレクトリの作成
    output_dir = project_root / "photo_migration"
    output_dir.mkdir(exist_ok=True)

    # ZIPファイル名（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"photo_migration_{timestamp}.zip"
    zip_path = output_dir / zip_filename

    # メタデータファイルの作成
    metadata = {
        "migration_date": datetime.now().isoformat(),
        "total_files": photo_info["total_files"],
        "total_size_mb": round(photo_info["total_size"] / (1024 * 1024), 2),
        "before_count": len(photo_info["before"]),
        "after_count": len(photo_info["after"]),
        "files": photo_info,
    }

    metadata_path = output_dir / "migration_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"📦 移行アーカイブを作成中: {zip_filename}")
    print(f"   - 施工前写真: {len(photo_info['before'])}件")
    print(f"   - 施工後写真: {len(photo_info['after'])}件")
    print(f"   - 総サイズ: {metadata['total_size_mb']}MB")

    # ZIPアーカイブの作成
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # メタデータファイルを追加
        zipf.write(metadata_path, "migration_metadata.json")

        # 写真ファイルを追加
        for photo in photo_info["before"]:
            archive_path = f"before/{photo['relative_path']}"
            zipf.write(photo["path"], archive_path)

        for photo in photo_info["after"]:
            archive_path = f"after/{photo['relative_path']}"
            zipf.write(photo["path"], archive_path)

    print(f"✅ 移行アーカイブが作成されました: {zip_path}")
    print(f"📄 メタデータファイル: {metadata_path}")

    return str(zip_path)


def create_render_upload_script():
    """
    Render上でアーカイブを展開するスクリプトを作成

    Returns:
        str: 作成されたスクリプトのパス
    """
    script_content = '''#!/usr/bin/env python3
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
'''

    output_dir = project_root / "photo_migration"
    output_dir.mkdir(exist_ok=True)

    script_path = output_dir / "extract_photos_on_render.py"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # 実行権限を付与
    os.chmod(script_path, 0o755)

    print(f"📜 Render用展開スクリプトを作成: {script_path}")

    return str(script_path)


def main():
    """メイン処理"""
    print("=== 写真データ Persistent Disk 移行ツール ===\\n")

    # 現在の写真データをスキャン
    print("🔍 ローカル写真データをスキャン中...")
    photo_info = scan_local_photos()

    if photo_info["total_files"] == 0:
        print("📂 移行対象の写真ファイルが見つかりませんでした")
        print(
            "   uploads/before/ または uploads/after/ に写真ファイルがあることを確認してください"
        )
        return

    print(f"\\n📊 スキャン結果:")
    print(f"   - 施工前写真: {len(photo_info['before'])}件")
    print(f"   - 施工後写真: {len(photo_info['after'])}件")
    print(f"   - 総サイズ: {round(photo_info['total_size'] / (1024 * 1024), 2)}MB")

    # 移行アーカイブの作成
    print("\\n📦 移行アーカイブを作成中...")
    archive_path = create_migration_archive()

    if not archive_path:
        print("❌ アーカイブの作成に失敗しました")
        return

    # Render用スクリプトの作成
    print("\\n📜 Render用展開スクリプトを作成中...")
    script_path = create_render_upload_script()

    print("\\n" + "=" * 50)
    print("🎉 移行準備が完了しました！")
    print("\\n📋 次のステップ:")
    print("1. Renderにアクセスしてサービスを選択")
    print("2. Shellタブを開く")
    print("3. 以下のファイルをRenderにアップロード:")
    print(f"   - {os.path.basename(archive_path)}")
    print(f"   - {os.path.basename(script_path)}")
    print("4. Render Shell上で実行:")
    print(f"   python {os.path.basename(script_path)}")
    print("\\n💡 SCPまたはwormholeコマンドでファイル転送可能です")


if __name__ == "__main__":
    main()
