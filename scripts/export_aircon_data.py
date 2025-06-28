#!/usr/bin/env python3
"""
ローカルのair_conditionersテーブルのデータをエクスポートし、
Renderにデプロイされたデータベースにインポートするスクリプト
"""

import sqlite3
import json
import os
import sys
import requests
from datetime import datetime


def export_aircon_data(db_path="instance/aircon_report.db"):
    """
    ローカルのair_conditionersテーブルのデータをJSONファイルにエクスポート
    """
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式で結果を取得
        cursor = conn.cursor()

        # air_conditionersテーブルのデータを取得
        cursor.execute("SELECT * FROM air_conditioners ORDER BY id")
        rows = cursor.fetchall()

        # データを辞書形式に変換
        aircon_data = []
        for row in rows:
            aircon_data.append(dict(row))

        conn.close()

        # JSONファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"aircon_export_{timestamp}.json"

        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(aircon_data, f, ensure_ascii=False, indent=2, default=str)

        print(
            f"エクスポート完了: {len(aircon_data)}件のデータを {export_file} に保存しました"
        )
        print(f"ファイルサイズ: {os.path.getsize(export_file)} bytes")

        # データの概要を表示
        if aircon_data:
            print("\n=== データ概要 ===")
            print(f"最初のレコードID: {aircon_data[0].get('id', 'N/A')}")
            print(f"最後のレコードID: {aircon_data[-1].get('id', 'N/A')}")

            # メーカー別の集計
            manufacturers = {}
            for item in aircon_data:
                manufacturer = item.get("manufacturer", "Unknown")
                manufacturers[manufacturer] = manufacturers.get(manufacturer, 0) + 1

            print("\nメーカー別台数:")
            for manufacturer, count in manufacturers.items():
                print(f"  {manufacturer}: {count}台")

        return export_file

    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        return None
    except Exception as e:
        print(f"エクスポートエラー: {e}")
        return None


def upload_to_render(export_file, render_url, api_key=None):
    """
    エクスポートしたデータをRenderのAPIエンドポイントに送信

    Args:
        export_file: エクスポートファイルのパス
        render_url: RenderアプリのURL
        api_key: 認証用のAPIキー（必要に応じて）
    """
    try:
        with open(export_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # APIエンドポイントにPOSTリクエストを送信
        api_url = f"{render_url.rstrip('/')}/api/import/air_conditioners"

        headers = {
            "Content-Type": "application/json",
        }

        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            print(f"アップロード成功: {len(data)}件のデータをRenderに送信しました")
            return True
        else:
            print(f"アップロードエラー: HTTP {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False

    except requests.RequestException as e:
        print(f"ネットワークエラー: {e}")
        return False
    except Exception as e:
        print(f"アップロードエラー: {e}")
        return False


def create_import_script(export_file):
    """
    Renderサーバー上で実行するインポートスクリプトを生成
    """
    script_content = f'''#!/usr/bin/env python3
"""
Renderサーバー上でair_conditionersデータをインポートするスクリプト
"""

import json
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.air_conditioner import AirConditioner

def import_aircon_data():
    app = create_app()
    
    # JSONデータを読み込み
    with open('{export_file}', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with app.app_context():
        try:
            # 既存データの確認
            existing_count = AirConditioner.query.count()
            print(f"既存のair_conditionersレコード数: {{existing_count}}")
            
            imported_count = 0
            updated_count = 0
            
            for item in data:
                # IDを除いてデータを準備
                item_data = {{k: v for k, v in item.items() if k != 'id'}}
                
                # 既存レコードを確認（property_id, manufacturer, model_numberで判定）
                existing = AirConditioner.query.filter_by(
                    property_id=item_data.get('property_id'),
                    manufacturer=item_data.get('manufacturer'),
                    model_number=item_data.get('model_number')
                ).first()
                
                if existing:
                    # 既存レコードを更新
                    for key, value in item_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    updated_count += 1
                    print(f"更新: ID {{existing.id}} - {{existing.manufacturer}} {{existing.model_number}}")
                else:
                    # 新規レコードを作成
                    new_aircon = AirConditioner(**item_data)
                    db.session.add(new_aircon)
                    imported_count += 1
                    print(f"追加: {{new_aircon.manufacturer}} {{new_aircon.model_number}}")
            
            # データベースに保存
            db.session.commit()
            
            print(f"\\nインポート完了:")
            print(f"  新規追加: {{imported_count}}件")
            print(f"  更新: {{updated_count}}件")
            print(f"  総処理件数: {{len(data)}}件")
            
            # 最終的なレコード数を確認
            final_count = AirConditioner.query.count()
            print(f"\\n最終的なair_conditionersレコード数: {{final_count}}")
            
        except Exception as e:
            db.session.rollback()
            print(f"インポートエラー: {{e}}")
            raise

if __name__ == "__main__":
    import_aircon_data()
'''

    script_file = f"import_aircon_to_render.py"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"Renderサーバー用インポートスクリプトを作成しました: {script_file}")
    return script_file


def main():
    print("=== エアコンデータ エクスポート・インポートツール ===")

    # ローカルデータベースからエクスポート
    print("\\n1. ローカルデータベースからエクスポート中...")
    export_file = export_aircon_data()

    if not export_file:
        print("エクスポートに失敗しました")
        sys.exit(1)

    # Renderサーバー用インポートスクリプトを作成
    print("\\n2. Renderサーバー用インポートスクリプトを作成中...")
    import_script = create_import_script(export_file)

    print("\\n=== 次のステップ ===")
    print("1. 以下のファイルをRenderサーバーにアップロード:")
    print(f"   - {export_file}")
    print(f"   - {import_script}")
    print("\\n2. Renderサーバー上で以下のコマンドを実行:")
    print(f"   python {import_script}")
    print("\\n3. または、以下のコマンドでRenderに直接アップロード:")
    print(f"   python {__file__} --upload <RENDER_URL>")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--upload":
        render_url = sys.argv[2]
        export_file = export_aircon_data()
        if export_file:
            upload_to_render(export_file, render_url)
    else:
        main()
