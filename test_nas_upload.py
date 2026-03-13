"""
NAS写真アップロードテスト

使用方法:
    python test_nas_upload.py
"""

import os
import sys
from pathlib import Path
from io import BytesIO

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Flaskアプリケーションの作成
from app import create_app

app = create_app()

def test_photo_upload():
    """写真アップロード機能のテスト"""
    print("=" * 70)
    print("NAS写真アップロードテスト")
    print("=" * 70)
    
    with app.app_context():
        # ダミー画像データを作成（1x1ピクセルのJPEG）
        # JPEG最小ヘッダー + データ
        dummy_image_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08'
            b'\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e'
            b'\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
            b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
            b'\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07'
            b'"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17'
            b'\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84'
            b'\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2'
            b'\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
            b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7'
            b'\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3'
            b'\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
            b'\xfe\xfe\x8a(\xff\xd9'
        )
        
        # Werkzeug FileStorageオブジェクトを模倣
        class DummyFile:
            def __init__(self, data, filename):
                self.data = data
                self.filename = filename
                self.position = 0
            
            def read(self):
                data = self.data[self.position:]
                self.position = len(self.data)
                return data
            
            def seek(self, position):
                self.position = position
        
        # テストファイル作成
        test_file = DummyFile(dummy_image_data, 'test_image.jpg')
        
        print("\n[1] テスト画像の作成")
        print("-" * 70)
        print(f"ファイル名: {test_file.filename}")
        print(f"ファイルサイズ: {len(dummy_image_data)} bytes")
        
        # file_handler の save_photo 関数をテスト
        print("\n[2] save_photo関数の実行")
        print("-" * 70)
        
        from app.utils.file_handler import save_photo
        
        try:
            saved_filename = save_photo(test_file, 'before')
            
            if saved_filename:
                print(f"✅ 保存成功: {saved_filename}")
                
                # ローカルファイルの確認
                local_path = os.path.join(app.config['UPLOAD_FOLDER'], 'before', saved_filename)
                if os.path.exists(local_path):
                    print(f"✅ ローカルファイル確認: {local_path}")
                    print(f"   ファイルサイズ: {os.path.getsize(local_path)} bytes")
                else:
                    print(f"⚠️ ローカルファイルが見つかりません: {local_path}")
                
                # NASファイルの確認
                print("\n[3] NAS保存の確認")
                print("-" * 70)
                from app.utils.nas_webdav import get_nas_client
                
                nas_client = get_nas_client()
                if nas_client.is_available():
                    remote_path = f"aircon_reports/before/{saved_filename}"
                    full_remote_path = f"{nas_client.base_path}/{remote_path}".replace('//', '/')
                    
                    try:
                        exists = nas_client.client.check(full_remote_path)
                        if exists:
                            print(f"✅ NASファイル確認: {full_remote_path}")
                            
                            # ファイルサイズを取得
                            info = nas_client.client.info(full_remote_path)
                            if 'size' in info:
                                print(f"   ファイルサイズ: {info['size']} bytes")
                        else:
                            print(f"❌ NASにファイルが見つかりません: {full_remote_path}")
                    except Exception as e:
                        print(f"❌ NAS確認エラー: {e}")
                else:
                    print("⚠️ NASが利用できません")
                
            else:
                print("❌ 保存失敗")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("テスト完了")
    print("=" * 70)


if __name__ == '__main__':
    test_photo_upload()

