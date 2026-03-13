"""
NASに保存されている写真を確認するスクリプト
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


def check_nas_photos():
    """NASに保存されている写真を確認"""
    print("=" * 70)
    print("NAS保存写真の確認")
    print("=" * 70)
    
    from app.utils.nas_webdav import get_nas_client
    
    nas_client = get_nas_client()
    
    if not nas_client.is_available():
        print("❌ NASに接続できません")
        print("\n確認事項:")
        print("  1. Tailscale VPNが起動しているか")
        print("  2. .envファイルの設定が正しいか")
        return
    
    print(f"✅ NASに接続しました: {nas_client.webdav_url}")
    print(f"   ベースパス: {nas_client.base_path}")
    
    # 各フォルダを確認
    for photo_type in ['before', 'after']:
        print(f"\n{'=' * 70}")
        print(f"[{photo_type.upper()}] 施工{photo_type}写真")
        print('=' * 70)
        
        folder_path = f"{nas_client.base_path}/aircon_reports/{photo_type}"
        
        try:
            # フォルダの存在確認
            if not nas_client.client.check(folder_path):
                print(f"⚠️ フォルダが存在しません: {folder_path}")
                continue
            
            # ファイル一覧を取得
            files = nas_client.client.list(folder_path)
            
            # ファイルをフィルタリング（.jpgや.jpeg のみ）
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            
            if image_files:
                print(f"✅ {len(image_files)}個の画像ファイルが見つかりました\n")
                
                # 最初の10個を表示
                for i, filename in enumerate(image_files[:10], 1):
                    # ファイル情報を取得
                    file_path = f"{folder_path}/{filename}"
                    try:
                        info = nas_client.client.info(file_path)
                        size = info.get('size', 'N/A')
                        modified = info.get('modified', 'N/A')
                        
                        # サイズをKBに変換
                        if isinstance(size, (int, float)):
                            size_kb = size / 1024
                            size_str = f"{size_kb:.1f} KB"
                        else:
                            size_str = str(size)
                        
                        print(f"  {i:2d}. {filename}")
                        print(f"      サイズ: {size_str}")
                        if modified != 'N/A':
                            print(f"      更新日時: {modified}")
                        print()
                    except Exception as e:
                        print(f"  {i:2d}. {filename}")
                        print(f"      (詳細情報取得エラー: {e})")
                        print()
                
                if len(image_files) > 10:
                    print(f"  ... 他 {len(image_files) - 10} 個のファイル")
            else:
                print(f"📭 画像ファイルが見つかりません")
                print(f"   (フォルダ内のファイル数: {len(files)})")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # 合計を表示
    print(f"\n{'=' * 70}")
    print("まとめ")
    print('=' * 70)
    
    total_before = 0
    total_after = 0
    
    try:
        before_path = f"{nas_client.base_path}/aircon_reports/before"
        if nas_client.client.check(before_path):
            before_files = nas_client.client.list(before_path)
            total_before = len([f for f in before_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        
        after_path = f"{nas_client.base_path}/aircon_reports/after"
        if nas_client.client.check(after_path):
            after_files = nas_client.client.list(after_path)
            total_after = len([f for f in after_files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
        
        print(f"施工前写真: {total_before}個")
        print(f"施工後写真: {total_after}個")
        print(f"合計: {total_before + total_after}個")
        
    except Exception as e:
        print(f"⚠️ 合計計算エラー: {e}")


if __name__ == '__main__':
    check_nas_photos()

