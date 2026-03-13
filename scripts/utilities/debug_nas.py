"""
NASデバッグスクリプト - 詳細なエラー情報を表示
"""

import os
import sys
from pathlib import Path

# Windows環境での文字化け対策
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def debug_nas():
    """NAS接続の詳細デバッグ"""
    print("=" * 70)
    print("NAS詳細デバッグ")
    print("=" * 70)
    
    # 環境変数の確認
    print("\n[ステップ1] 環境変数の確認")
    print("-" * 70)
    nas_enabled = os.environ.get('NAS_ENABLED', 'False')
    nas_url = os.environ.get('NAS_WEBDAV_URL', '')
    nas_username = os.environ.get('NAS_USERNAME', '')
    nas_password = os.environ.get('NAS_PASSWORD', '')
    nas_base_path = os.environ.get('NAS_BASE_PATH', '')
    
    print(f"NAS_ENABLED: {nas_enabled}")
    print(f"NAS_WEBDAV_URL: {nas_url}")
    print(f"NAS_USERNAME: {nas_username}")
    print(f"NAS_PASSWORD: {'*' * len(nas_password) if nas_password else '(未設定)'}")
    print(f"NAS_BASE_PATH: {nas_base_path}")
    
    if nas_enabled.lower() != 'true':
        print("\n❌ NAS_ENABLED=True に設定してください")
        return
    
    if not all([nas_url, nas_username, nas_password, nas_base_path]):
        print("\n❌ 必要な環境変数が不足しています")
        return
    
    # WebDAV3のインポート確認
    print("\n[ステップ2] WebDAV3ライブラリの確認")
    print("-" * 70)
    try:
        from webdav3.client import Client
        from webdav3.exceptions import WebDavException
        print("✅ webdav3ライブラリがインストールされています")
    except ImportError as e:
        print(f"❌ webdav3ライブラリのインポートエラー: {e}")
        print("\n以下を実行してください:")
        print("  pip install webdavclient3")
        return
    
    # WebDAVクライアントの作成
    print("\n[ステップ3] WebDAVクライアントの作成")
    print("-" * 70)
    
    options = {
        'webdav_hostname': nas_url,
        'webdav_login': nas_username,
        'webdav_password': nas_password,
        'webdav_timeout': 30,
    }
    
    try:
        client = Client(options)
        print("✅ WebDAVクライアント作成成功")
    except Exception as e:
        print(f"❌ WebDAVクライアント作成エラー: {e}")
        return
    
    # ベースパスの存在確認
    print("\n[ステップ4] ベースパスの存在確認")
    print("-" * 70)
    print(f"確認対象: {nas_base_path}")
    
    try:
        exists = client.check(nas_base_path)
        if exists:
            print(f"✅ ベースパスが存在します: {nas_base_path}")
        else:
            print(f"❌ ベースパスが存在しません: {nas_base_path}")
            print("\n考えられる原因:")
            print("  1. パスが間違っている")
            print("  2. ユーザーに読み取り権限がない")
            print("\n別のパスを試してみます...")
            
            # ルートパスを確認
            print("\n[ルートパスの確認]")
            try:
                root_exists = client.check('/')
                print(f"✅ ルート(/)にアクセス可能")
            except Exception as e:
                print(f"❌ ルート(/)アクセスエラー: {e}")
            
            # /homeを確認
            print("\n[/homeの確認]")
            try:
                home_exists = client.check('/home')
                if home_exists:
                    print(f"✅ /homeが存在します")
                    
                    # /home配下のリストを取得
                    try:
                        items = client.list('/home')
                        print(f"\n/home配下のフォルダ一覧:")
                        for item in items:
                            print(f"  - {item}")
                    except Exception as e:
                        print(f"⚠️ /home配下のリスト取得エラー: {e}")
                else:
                    print(f"❌ /homeが存在しません")
            except Exception as e:
                print(f"❌ /homeアクセスエラー: {e}")
            
            return
    except WebDavException as e:
        print(f"❌ WebDAVエラー: {e}")
        print(f"   エラー詳細: {type(e).__name__}")
        return
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        return
    
    # ディレクトリ作成テスト
    print("\n[ステップ5] テストディレクトリの作成")
    print("-" * 70)
    test_dir = f"{nas_base_path}/test_directory"
    print(f"作成対象: {test_dir}")
    
    try:
        # 既に存在する場合は削除
        if client.check(test_dir):
            print(f"⚠️ テストディレクトリが既に存在します。削除します...")
            client.clean(test_dir)
        
        # ディレクトリ作成
        client.mkdir(test_dir)
        print(f"✅ ディレクトリ作成成功: {test_dir}")
        
        # 作成確認
        if client.check(test_dir):
            print(f"✅ ディレクトリの存在を確認しました")
            
            # クリーンアップ
            client.clean(test_dir)
            print(f"✅ テストディレクトリを削除しました")
        else:
            print(f"⚠️ ディレクトリが作成されませんでした")
            
    except WebDavException as e:
        print(f"❌ ディレクトリ作成エラー: {e}")
        print(f"\n考えられる原因:")
        print(f"  1. ユーザー '{nas_username}' に書き込み権限がない")
        print(f"  2. パス '{nas_base_path}' が正しくない")
        print(f"  3. NASの容量が不足している")
        print(f"\nNAS管理画面で以下を確認してください:")
        print(f"  - ユーザー '{nas_username}' の権限")
        print(f"  - フォルダー '{nas_base_path}' の存在と権限")
        print(f"  - WebDAVサービスの状態")
        return
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        import traceback
        print("\n詳細なエラー情報:")
        traceback.print_exc()
        return
    
    # aircon_reportsディレクトリの作成テスト
    print("\n[ステップ6] aircon_reportsディレクトリの作成")
    print("-" * 70)
    aircon_dir = f"{nas_base_path}/aircon_reports"
    print(f"作成対象: {aircon_dir}")
    
    try:
        if not client.check(aircon_dir):
            client.mkdir(aircon_dir)
            print(f"✅ aircon_reportsディレクトリ作成成功")
        else:
            print(f"✅ aircon_reportsディレクトリは既に存在します")
        
        # before/afterディレクトリの作成
        for subdir in ['before', 'after']:
            full_path = f"{aircon_dir}/{subdir}"
            if not client.check(full_path):
                client.mkdir(full_path)
                print(f"✅ {subdir}ディレクトリ作成成功")
            else:
                print(f"✅ {subdir}ディレクトリは既に存在します")
        
    except Exception as e:
        print(f"❌ aircon_reportsディレクトリ作成エラー: {e}")
        return
    
    print("\n" + "=" * 70)
    print("✅ すべてのチェックが完了しました！")
    print("=" * 70)
    print("\nNASは正常に動作しています。")
    print("写真アップロード機能を使用できます。")


if __name__ == '__main__':
    debug_nas()

