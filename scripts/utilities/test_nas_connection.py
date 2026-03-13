"""
NAS接続テストスクリプト

使用方法:
    python scripts/utilities/test_nas_connection.py
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def test_nas_connection():
    """NAS接続テスト"""
    print("=" * 60)
    print("NAS接続テスト")
    print("=" * 60)
    
    # 環境変数の確認
    print("\n[1] 環境変数の確認")
    print("-" * 60)
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
        print("\n⚠️ NAS機能が無効です。NAS_ENABLED=True に設定してください。")
        return
    
    if not all([nas_url, nas_username, nas_password]):
        print("\n❌ 必要な環境変数が設定されていません。")
        print("必要な環境変数: NAS_WEBDAV_URL, NAS_USERNAME, NAS_PASSWORD")
        return
    
    # NASクライアントの初期化
    print("\n[2] NASクライアントの初期化")
    print("-" * 60)
    try:
        from app.utils.nas_webdav import get_nas_client
        
        nas_client = get_nas_client()
        print("✅ NASクライアント初期化成功")
    except Exception as e:
        print(f"❌ NASクライアント初期化エラー: {e}")
        return
    
    # 接続テスト
    print("\n[3] NAS接続テスト")
    print("-" * 60)
    success, message = nas_client.test_connection()
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        return
    
    # テストファイルのアップロード
    print("\n[4] テストファイルのアップロード")
    print("-" * 60)
    test_content = b"Test file content from NAS connection test"
    test_filename = "test_file.txt"
    test_remote_path = f"aircon_reports/test/{test_filename}"
    
    try:
        success, error = nas_client.upload_file(test_content, test_remote_path)
        if success:
            print(f"✅ テストファイルアップロード成功: {test_remote_path}")
        else:
            print(f"❌ テストファイルアップロード失敗: {error}")
            return
    except Exception as e:
        print(f"❌ アップロードエラー: {e}")
        return
    
    # テストファイルのダウンロード
    print("\n[5] テストファイルのダウンロード")
    print("-" * 60)
    try:
        file_data, error = nas_client.download_file(test_remote_path)
        if file_data:
            print(f"✅ テストファイルダウンロード成功")
            print(f"   内容: {file_data.decode('utf-8')}")
            
            # 内容の検証
            if file_data == test_content:
                print("✅ ファイル内容が一致しました")
            else:
                print("⚠️ ファイル内容が一致しません")
        else:
            print(f"❌ テストファイルダウンロード失敗: {error}")
            return
    except Exception as e:
        print(f"❌ ダウンロードエラー: {e}")
        return
    
    # テストファイルの削除
    print("\n[6] テストファイルの削除")
    print("-" * 60)
    try:
        success, error = nas_client.delete_file(test_remote_path)
        if success:
            print(f"✅ テストファイル削除成功")
        else:
            print(f"❌ テストファイル削除失敗: {error}")
    except Exception as e:
        print(f"❌ 削除エラー: {e}")
    
    # 最終結果
    print("\n" + "=" * 60)
    print("✅ すべてのテストが完了しました")
    print("=" * 60)
    print("\nNASへの写真保存システムは正常に動作しています。")
    print("アプリケーションから写真をアップロードしてください。")


if __name__ == '__main__':
    test_nas_connection()

