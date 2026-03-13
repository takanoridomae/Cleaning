#!/usr/bin/env python3
"""
Render上の写真のURLリストを生成

このスクリプトはRender Shell上で実行し、
データベースに登録されているすべての写真のURLリストを生成します。

出力ファイル: photo_urls.txt

使用方法:
    python scripts/utilities/generate_photo_urls.py
"""
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.models.photo import Photo


def generate_urls():
    """写真URLリストを生成"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("写真URLリスト生成")
        print("=" * 70)
        
        # すべての写真を取得
        photos = Photo.query.all()
        
        if not photos:
            print("\n⚠️ データベースに写真が登録されていません")
            return
        
        print(f"\n📊 登録写真数: {len(photos)}個")
        
        # RenderのアプリケーションURL（環境変数から取得）
        base_url = os.environ.get('RENDER_EXTERNAL_URL')
        
        if not base_url:
            # 環境変数がない場合は手動入力を促す
            print("\n⚠️ RENDER_EXTERNAL_URL 環境変数が設定されていません")
            print("例: https://your-app-name.onrender.com")
            
            # Render環境かどうかをチェック
            is_render = os.environ.get('RENDER', 'False').lower() == 'true'
            
            if is_render:
                print("\nRender環境を検出しました。")
                print("Renderダッシュボードで確認できるアプリケーションURLを")
                print("RENDER_EXTERNAL_URL 環境変数に設定してください。")
                return
            else:
                # ローカル環境の場合はデフォルトURL
                base_url = 'http://localhost:5000'
                print(f"\nローカル環境のため、デフォルトURL {base_url} を使用します")
        
        print(f"\n🌐 ベースURL: {base_url}")
        
        # URLリストファイルを生成
        output_file = 'photo_urls.txt'
        
        before_count = 0
        after_count = 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for photo in photos:
                # 写真URLを生成
                url = f"{base_url}/uploads/{photo.photo_type}/{photo.filename}"
                
                # パイプ区切りで情報を記録
                # 形式: URL|photo_type|filename|report_id
                f.write(f"{url}|{photo.photo_type}|{photo.filename}|{photo.report_id}\n")
                
                if photo.photo_type == 'before':
                    before_count += 1
                else:
                    after_count += 1
        
        print(f"\n✅ URLリストを生成しました: {output_file}")
        print(f"\n📊 統計:")
        print(f"   施工前写真: {before_count}個")
        print(f"   施工後写真: {after_count}個")
        print(f"   合計: {len(photos)}個")
        
        print(f"\n📝 次のステップ:")
        print(f"   1. {output_file} の内容をコピー")
        print(f"   2. ローカルPCに同名ファイルとして保存")
        print(f"   3. download_photos_from_render.py を実行")
        
        print(f"\n💡 ファイル内容を表示:")
        print(f"   cat {output_file}")
        
        print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        generate_urls()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

