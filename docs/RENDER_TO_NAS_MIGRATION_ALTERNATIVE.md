# Render写真のNAS移行 - ローカルPC経由の代替方法

## 📋 概要

Render環境から直接NASにアクセスできない場合の代替移行手順です。
ローカルPCを経由して、Renderの写真をNASに移行します。

## 🎯 この方法が必要な場合

- Render環境からTailscale VPNにアクセスできない
- NASがパブリックIPでアクセス可能ではない
- Renderからの直接移行スクリプトが失敗する

## 📝 移行手順の概要

```
Render Persistent Disk
        ↓ (1) エクスポート
    ローカルPC
        ↓ (2) 移行スクリプト実行
      NAS
```

## 🚀 詳細手順

### 前提条件

1. **ローカルPC環境**
   - Pythonがインストールされている
   - Tailscale VPNが設定済み
   - プロジェクトのローカルコピーがある

2. **Render環境**
   - Shell接続が可能

3. **NAS環境**
   - ローカルPCからアクセス可能（Tailscale経由）

---

### ステップ1: Render上の写真データをエクスポート

#### 1-1. データベースから写真一覧を取得

1. **Render Shellに接続**
   ```bash
   # Renderダッシュボード > Shell
   ```

2. **写真一覧をエクスポート**
   ```bash
   python scripts/utilities/export_photo_metadata.py
   ```
   
   これにより `photo_metadata.json` が生成されます。

#### 1-2. 写真ファイルのアーカイブ作成

**方法A: 全写真を一括アーカイブ（小規模な場合）**

```bash
cd /opt/render/project/src
tar -czf photos_export.tar.gz uploads/before uploads/after
ls -lh photos_export.tar.gz
```

**方法B: 分割アーカイブ（大規模な場合）**

```bash
cd /opt/render/project/src

# 施工前写真
tar -czf photos_before.tar.gz uploads/before

# 施工後写真  
tar -czf photos_after.tar.gz uploads/after

# サイズ確認
ls -lh photos_*.tar.gz
```

⚠️ **注意**: Render Shellから直接ファイルダウンロードは困難なため、
以下のいずれかの方法でローカルPCに転送する必要があります。

---

### ステップ2: ローカルPCへの転送

Renderから直接ダウンロードできないため、以下の方法を使用します。

#### 方法A: 一時的なダウンロードエンドポイントを作成（推奨）

1. **一時ダウンロード用スクリプトを作成**

   ローカル環境で以下のファイルを作成:

   `scripts/utilities/create_download_endpoint.py`:
   ```python
   """
   Render上に一時的なダウンロードエンドポイントを作成
   
   使用方法:
   1. このスクリプトをRenderにデプロイ
   2. 専用URLにアクセスしてアーカイブをダウンロード
   3. ダウンロード後、エンドポイントを削除
   """
   # 実装内容は別途提供
   ```

#### 方法B: 写真を個別にダウンロード（確実だが時間がかかる）

1. **Renderアプリケーションにアクセス**
   - https://your-app.onrender.com/

2. **各報告書から写真を手動ダウンロード**
   - 報告書詳細画面を開く
   - 各写真を右クリック > 「名前を付けて画像を保存」
   
   ⚠️ **注意**: 写真が多い場合は非現実的です。

#### 方法C: データベースダンプから復元（高度な方法）

1. **データベースをエクスポート**
   ```bash
   # Render Shell上で
   python scripts/backup/backup_db.py
   ```

2. **Base64エンコードされた写真データを含むエクスポート**
   ```bash
   python scripts/export_all_data.py
   ```

3. **ローカルで復元**
   ```bash
   python scripts/utilities/restore_photos_from_export.py all_data_export.json
   ```

---

### ステップ3: 推奨方法 - 写真URLリストからダウンロード

最も実用的な方法は、写真のURLリストを作成してダウンロードすることです。

#### 3-1. Render Shell上で写真一覧を作成

以下のスクリプトを作成・実行します:

`scripts/utilities/generate_photo_urls.py`:

```python
#!/usr/bin/env python3
"""
Render上の写真のURLリストを生成

出力: photo_urls.txt
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app
from app.models.photo import Photo

def generate_urls():
    app = create_app()
    
    with app.app_context():
        photos = Photo.query.all()
        
        # RenderのアプリケーションURL（環境変数から取得）
        base_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        
        with open('photo_urls.txt', 'w') as f:
            for photo in photos:
                # 写真URLを生成
                url = f"{base_url}/uploads/{photo.photo_type}/{photo.filename}"
                # ファイル情報も含める
                f.write(f"{url}|{photo.photo_type}|{photo.filename}\n")
        
        print(f"✅ {len(photos)}個の写真URLを photo_urls.txt に出力しました")

if __name__ == '__main__':
    generate_urls()
```

**Render Shell上で実行:**
```bash
python scripts/utilities/generate_photo_urls.py
cat photo_urls.txt
```

#### 3-2. URLリストの内容をコピー

```bash
cat photo_urls.txt
```

出力をすべてコピーして、ローカルPCに `photo_urls.txt` として保存します。

#### 3-3. ローカルPCでダウンロードスクリプトを実行

以下のスクリプトをローカルPCで実行します:

`scripts/utilities/download_photos_from_render.py`:

```python
#!/usr/bin/env python3
"""
Renderから写真をダウンロード

使用方法:
    python scripts/utilities/download_photos_from_render.py photo_urls.txt
"""
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse

def download_photos(urls_file):
    """URLリストから写真をダウンロード"""
    
    # ダウンロード先ディレクトリ
    download_base = Path('downloads_from_render')
    download_base.mkdir(exist_ok=True)
    
    (download_base / 'before').mkdir(exist_ok=True)
    (download_base / 'after').mkdir(exist_ok=True)
    
    # URLリストを読み込む
    with open(urls_file, 'r') as f:
        lines = f.readlines()
    
    total = len(lines)
    success = 0
    failed = 0
    
    print(f"📥 {total}個の写真をダウンロードします...\n")
    
    for i, line in enumerate(lines, 1):
        try:
            parts = line.strip().split('|')
            url = parts[0]
            photo_type = parts[1]
            filename = parts[2]
            
            # ダウンロード先パス
            dest_path = download_base / photo_type / filename
            
            # 既に存在する場合はスキップ
            if dest_path.exists():
                print(f"  {i:3d}/{total} ⏭️  スキップ: {filename}")
                continue
            
            # ダウンロード実行
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # ファイル保存
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            print(f"  {i:3d}/{total} ✅ ダウンロード: {filename} ({size_kb:.1f} KB)")
            success += 1
            
        except Exception as e:
            print(f"  {i:3d}/{total} ❌ エラー: {filename} - {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"✅ 成功: {success}個")
    print(f"❌ 失敗: {failed}個")
    print(f"📂 保存先: {download_base.absolute()}")
    print(f"{'='*70}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法: python download_photos_from_render.py photo_urls.txt")
        sys.exit(1)
    
    download_photos(sys.argv[1])
```

**実行:**
```bash
python scripts/utilities/download_photos_from_render.py photo_urls.txt
```

---

### ステップ4: ローカルPCからNASに移行

ダウンロードが完了したら、既存の移行スクリプトを使用します。

1. **ダウンロードした写真を `uploads/` フォルダに配置**
   ```bash
   # Windows PowerShell
   Copy-Item -Path downloads_from_render\before\* -Destination uploads\before\
   Copy-Item -Path downloads_from_render\after\* -Destination uploads\after\
   
   # Linux/Mac
   cp downloads_from_render/before/* uploads/before/
   cp downloads_from_render/after/* uploads/after/
   ```

2. **NAS移行スクリプトを実行**
   ```bash
   python migrate_existing_photos_to_nas.py
   ```

3. **移行結果を確認**
   - NAS上の `/home/eacon_keep_pict/aircon_reports/` を確認
   - before/after フォルダに写真が保存されていることを確認

---

## ✅ 移行完了後の確認

### 確認事項

1. **NAS上の写真確認**
   - NAS管理画面で写真の存在を確認
   - 件数が一致することを確認

2. **ローカルアプリケーションでの動作確認**
   - ローカル環境でアプリケーションを起動
   - 報告書詳細画面で写真が表示されることを確認

3. **Renderバックアップの保持**
   - Render上の写真は削除せず保持
   - いつでも再ダウンロード可能

---

## 🔧 トラブルシューティング

### ダウンロードが途中で止まる

**対処法:**
- スクリプトを再実行（既にダウンロード済みの写真はスキップされる）
- タイムアウト時間を延長（`timeout=30` → `timeout=60`）

### 一部の写真がダウンロードできない

**対処法:**
1. 失敗したURLを確認
2. ブラウザで直接URLにアクセスして確認
3. Renderアプリケーションが稼働中か確認

### NAS移行時にエラーが発生

**対処法:**
1. Tailscale VPNが起動しているか確認
2. NAS接続テストを実行
   ```bash
   python scripts/utilities/test_nas_connection.py
   ```

---

## 📝 補足: より簡単な方法のスクリプト作成

必要に応じて、以下のスクリプトを作成できます:

1. **`generate_photo_urls.py`**: Render上で写真URLリストを生成
2. **`download_photos_from_render.py`**: ローカルPCで写真をダウンロード
3. **`verify_migration.py`**: 移行結果を検証

これらのスクリプトは、上記手順の自動化版として別途提供可能です。

---

**作成日**: 2025-10-14  
**対象**: Render → ローカルPC → NAS 移行  
**バージョン**: 1.0

