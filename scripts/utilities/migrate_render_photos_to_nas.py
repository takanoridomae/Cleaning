#!/usr/bin/env python3
"""
Render環境の既存写真をNASに移行するスクリプト

このスクリプトは以下を実行します：
1. Render Persistent Disk内の写真を検出
2. NAS接続を確認
3. 写真をNASにアップロード（既存の場合はスキップ）
4. Render上の写真は削除せず保持（バックアップとして）

使用方法:
    Render Shell上で実行:
    python scripts/utilities/migrate_render_photos_to_nas.py

前提条件:
    - Render環境にTailscaleがインストールされている、または
      NAS_WEBDAV_URLがRenderからアクセス可能なパブリックIPである
    - 環境変数が設定されている:
      NAS_ENABLED=True
      NAS_WEBDAV_URL=http://...
      NAS_USERNAME=...
      NAS_PASSWORD=...
      NAS_BASE_PATH=/home/eacon_keep_pict
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 環境変数の読み込み（Render環境では自動設定済み）
from dotenv import load_dotenv
load_dotenv()


def check_render_environment():
    """Render環境かどうかを確認"""
    is_render = os.environ.get('RENDER', 'False').lower() == 'true'
    return is_render


def print_header(text, char='='):
    """ヘッダーを表示"""
    width = 70
    print(f"\n{char * width}")
    print(f"{text}")
    print(f"{char * width}")


def print_section(text):
    """セクションヘッダーを表示"""
    print(f"\n{'─' * 70}")
    print(f"📋 {text}")
    print(f"{'─' * 70}")


def migrate_photos():
    """Render環境の既存写真をNASに移行"""
    
    print_header("Render既存写真のNAS移行")
    
    # 環境確認
    is_render = check_render_environment()
    if is_render:
        print("✅ Render環境を検出しました")
    else:
        print("⚠️  Render環境ではありません（ローカル環境での実行）")
    
    # Flaskアプリケーションの初期化
    try:
        from app import create_app
        from app.utils.nas_webdav import get_nas_client
        
        app = create_app()
    except Exception as e:
        print(f"❌ アプリケーション初期化エラー: {e}")
        return False
    
    with app.app_context():
        print_section("NAS接続確認")
        
        # NAS設定の表示
        nas_enabled = os.environ.get('NAS_ENABLED', 'False')
        nas_url = os.environ.get('NAS_WEBDAV_URL', '未設定')
        nas_username = os.environ.get('NAS_USERNAME', '未設定')
        nas_base_path = os.environ.get('NAS_BASE_PATH', '未設定')
        
        print(f"NAS_ENABLED: {nas_enabled}")
        print(f"NAS_WEBDAV_URL: {nas_url}")
        print(f"NAS_USERNAME: {nas_username}")
        print(f"NAS_BASE_PATH: {nas_base_path}")
        
        # NASクライアントの取得
        nas_client = get_nas_client()
        
        if not nas_client.is_available():
            print("\n❌ NASに接続できません")
            print("\n考えられる原因:")
            print("  1. NAS_ENABLED が True に設定されていない")
            print("  2. 環境変数が正しく設定されていない")
            print("  3. Render環境からTailscaleネットワークにアクセスできない")
            print("  4. NAS WebDAVサービスが起動していない")
            print("\n💡 代替案:")
            print("  docs/RENDER_PHOTO_MIGRATION_GUIDE.md を参照して")
            print("  ローカルPC経由での移行方法をご確認ください。")
            return False
        
        print(f"\n✅ NASに接続しました: {nas_client.webdav_url}")
        print(f"📂 ベースパス: {nas_client.base_path}")
        
        # アップロードフォルダの取得
        upload_folder = app.config['UPLOAD_FOLDER']
        print(f"\n📂 写真保存先: {upload_folder}")
        
        if not os.path.exists(upload_folder):
            print(f"❌ アップロードフォルダが存在しません: {upload_folder}")
            return False
        
        # 統計情報の初期化
        stats = {
            'total_migrated': 0,
            'total_failed': 0,
            'total_skipped': 0,
            'total_size_bytes': 0,
            'start_time': datetime.now()
        }
        
        # 各フォルダ（before/after）の写真を移行
        for photo_type in ['before', 'after']:
            print_section(f"施工{photo_type}写真の移行")
            
            local_folder = os.path.join(upload_folder, photo_type)
            
            if not os.path.exists(local_folder):
                print(f"⚠️ フォルダが存在しません: {local_folder}")
                continue
            
            # 画像ファイル一覧を取得（ディレクトリは除外）
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
            
            # 各ファイルを移行
            for i, filename in enumerate(files, 1):
                local_path = os.path.join(local_folder, filename)
                remote_path = f"aircon_reports/{photo_type}/{filename}"
                full_remote_path = f"{nas_client.base_path}/{remote_path}".replace('//', '/')
                
                try:
                    # NASに既に存在するかチェック
                    if nas_client.client.check(full_remote_path):
                        print(f"  {i:3d}/{len(files)} ⏭️  スキップ（既に存在）: {filename}")
                        stats['total_skipped'] += 1
                        continue
                    
                    # ローカルファイルを読み込む
                    with open(local_path, 'rb') as f:
                        file_data = f.read()
                    
                    file_size = len(file_data)
                    
                    # NASにアップロード
                    success, error = nas_client.upload_file(file_data, remote_path)
                    
                    if success:
                        file_size_kb = file_size / 1024
                        stats['total_migrated'] += 1
                        stats['total_size_bytes'] += file_size
                        print(f"  {i:3d}/{len(files)} ✅ 移行成功: {filename} ({file_size_kb:.1f} KB)")
                    else:
                        stats['total_failed'] += 1
                        print(f"  {i:3d}/{len(files)} ❌ 移行失敗: {filename}")
                        print(f"           エラー: {error}")
                        
                except Exception as e:
                    stats['total_failed'] += 1
                    print(f"  {i:3d}/{len(files)} ❌ エラー: {filename}")
                    print(f"           {type(e).__name__}: {e}")
        
        # 結果サマリーの表示
        elapsed_time = (datetime.now() - stats['start_time']).total_seconds()
        total_size_mb = stats['total_size_bytes'] / (1024 * 1024)
        
        print_header("移行結果", '=')
        print(f"✅ 移行成功: {stats['total_migrated']}個 ({total_size_mb:.2f} MB)")
        print(f"⏭️  スキップ: {stats['total_skipped']}個（既にNASに存在）")
        print(f"❌ 移行失敗: {stats['total_failed']}個")
        print(f"📊 合計: {stats['total_migrated'] + stats['total_skipped'] + stats['total_failed']}個")
        print(f"⏱️  処理時間: {elapsed_time:.1f}秒")
        
        if stats['total_migrated'] > 0:
            avg_speed = total_size_mb / elapsed_time if elapsed_time > 0 else 0
            print(f"📈 平均速度: {avg_speed:.2f} MB/秒")
        
        print("\n" + "=" * 70)
        
        if stats['total_failed'] > 0:
            print("\n⚠️ 一部の写真の移行に失敗しました。")
            print("   上記のエラーメッセージを確認してください。")
            return False
        elif stats['total_migrated'] > 0:
            print("\n🎉 すべての写真が正常にNASに移行されました！")
            print("\n📌 重要な注意事項:")
            print("  ✓ Render上の写真は削除されていません（バックアップとして保持）")
            print("  ✓ 今後の新規写真は自動的にNASに保存されます")
            print("  ✓ 既存写真はNASとRender両方から読み出し可能です")
            return True
        else:
            print("\n✨ すべての写真は既にNASに存在しています。")
            print("   移行は完了済みです。")
            return True


def main():
    """メイン処理"""
    print("\n" + "=" * 70)
    print("Render既存写真のNAS移行ツール")
    print("=" * 70)
    print("\n⚠️  この操作について:")
    print("  - Render Persistent Disk内の既存写真をNASにコピーします")
    print("  - Render上の写真は削除されません（バックアップとして保持）")
    print("  - 既にNASに存在する写真はスキップされます")
    print("  - NAS接続にはTailscale VPNまたはパブリックアクセスが必要です")
    
    # Render環境でのインタラクティブ入力のスキップ
    is_render = check_render_environment()
    
    if not is_render:
        # ローカル環境では確認を求める
        try:
            response = input("\n続行しますか？ (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("\n移行をキャンセルしました。")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n\n移行をキャンセルしました。")
            return
    else:
        print("\n✅ Render環境のため、自動的に続行します...")
    
    # 移行実行
    success = migrate_photos()
    
    if success:
        print("\n✅ 移行処理が正常に完了しました。")
        sys.exit(0)
    else:
        print("\n❌ 移行処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

