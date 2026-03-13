"""
既存のローカル写真をNASに移行するスクリプト

使用方法:
    python migrate_existing_photos_to_nas.py
"""

import os
import sys
from pathlib import Path

# Windows環境での文字化け対策
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def migrate_photos():
    """既存のローカル写真をNASに移行"""
    print("=" * 70)
    print("既存写真のNAS移行")
    print("=" * 70)
    
    from app import create_app
    from app.utils.nas_webdav import get_nas_client
    
    app = create_app()
    
    with app.app_context():
        nas_client = get_nas_client()
        
        if not nas_client.is_available():
            print("❌ NASに接続できません")
            print("移行を中止します。")
            return
        
        print(f"✅ NASに接続しました: {nas_client.webdav_url}")
        
        upload_folder = app.config['UPLOAD_FOLDER']
        
        total_migrated = 0
        total_failed = 0
        total_skipped = 0
        
        for photo_type in ['before', 'after']:
            print(f"\n{'=' * 70}")
            print(f"[{photo_type.upper()}] 施工{photo_type}写真の移行")
            print('=' * 70)
            
            local_folder = os.path.join(upload_folder, photo_type)
            
            if not os.path.exists(local_folder):
                print(f"⚠️ フォルダが存在しません: {local_folder}")
                continue
            
            # ローカルフォルダ内のファイル一覧（ディレクトリは除外）
            all_items = os.listdir(local_folder)
            files = []
            for item in all_items:
                item_path = os.path.join(local_folder, item)
                # ファイルのみを対象とし、ディレクトリは除外
                if os.path.isfile(item_path):
                    # 画像ファイルのみを対象
                    if item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF')):
                        files.append(item)
            
            if not files:
                print(f"📭 移行対象の写真がありません")
                continue
            
            print(f"📊 移行対象: {len(files)}個の写真\n")
            
            for i, filename in enumerate(files, 1):
                local_path = os.path.join(local_folder, filename)
                remote_path = f"aircon_reports/{photo_type}/{filename}"
                full_remote_path = f"{nas_client.base_path}/{remote_path}".replace('//', '/')
                
                try:
                    # NASに既に存在するかチェック
                    if nas_client.client.check(full_remote_path):
                        print(f"  {i:3d}. ⏭️  スキップ（既に存在）: {filename}")
                        total_skipped += 1
                        continue
                    
                    # ファイルを読み込む
                    with open(local_path, 'rb') as f:
                        file_data = f.read()
                    
                    # NASにアップロード
                    success, error = nas_client.upload_file(file_data, remote_path)
                    
                    if success:
                        file_size_kb = len(file_data) / 1024
                        print(f"  {i:3d}. ✅ 移行成功: {filename} ({file_size_kb:.1f} KB)")
                        total_migrated += 1
                    else:
                        print(f"  {i:3d}. ❌ 移行失敗: {filename} - {error}")
                        total_failed += 1
                        
                except Exception as e:
                    print(f"  {i:3d}. ❌ エラー: {filename} - {e}")
                    total_failed += 1
        
        # 結果サマリー
        print(f"\n{'=' * 70}")
        print("移行結果")
        print('=' * 70)
        print(f"✅ 移行成功: {total_migrated}個")
        print(f"⏭️  スキップ: {total_skipped}個（既にNASに存在）")
        print(f"❌ 移行失敗: {total_failed}個")
        print(f"📊 合計: {total_migrated + total_skipped + total_failed}個")
        
        if total_failed > 0:
            print("\n⚠️ 一部の写真の移行に失敗しました。")
            print("   エラーメッセージを確認してください。")
        elif total_migrated > 0:
            print("\n🎉 すべての写真が正常にNASに移行されました！")
            print("\n注意:")
            print("  - ローカルの写真は削除されていません")
            print("  - 今後も両方から読み出し可能です")
        else:
            print("\n✨ すべての写真は既にNASに存在しています。")


if __name__ == '__main__':
    print("\n⚠️  この操作は既存のローカル写真をNASにコピーします。")
    print("   ローカルの写真は削除されません。")
    
    response = input("\n続行しますか？ (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_photos()
    else:
        print("\n移行をキャンセルしました。")

