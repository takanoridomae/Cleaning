# NAS写真保存ロジック クイックリファレンス

他システムでの実装時に素早く参照できる要点まとめ

---

## 📌 システム概要

**3段階ハイブリッドストレージ**: NAS → ローカル → フォールバック

```
1. 優先: UGREEN NAS (WebDAV/Tailscale/無制限)
2. 併用: ローカルストレージ (開発環境)
3. 本番: NAS成功時はローカルスキップ
```

---

## 🔧 必須パッケージ

```txt
webdavclient3>=3.14.6
Pillow>=10.0.0
Flask>=2.3.0
```

---

## 🌍 環境変数

```bash
NAS_ENABLED=True
NAS_WEBDAV_URL=http://100.69.218.15:5005
NAS_USERNAME=your-username
NAS_PASSWORD=your-password
NAS_BASE_PATH=/home/eacon_keep_pict
UPLOAD_FOLDER=uploads
RENDER=False  # 本番環境フラグ
```

---

## 📁 フォルダ構造

```
NAS: /home/eacon_keep_pict/aircon_reports/{before|after}/{uuid}_{timestamp}.jpg
ローカル: uploads/{before|after}/{uuid}_{timestamp}.jpg
サムネイル: uploads/thumbnails/thumb_{uuid}_{timestamp}.jpg
```

---

## 💾 コア処理フロー

### 1. 写真保存 (`save_photo`)

```
[アップロード]
    ↓
[ファイル名生成] UUID + タイムスタンプ
    ↓
[画像圧縮] 700x500px, JPEG 70%
    ↓
[NAS保存試行] ← Tailscale VPN経由
    ↓
    ├─ 成功 → [本番環境?]
    │           ├─ Yes → ローカル保存スキップ
    │           └─ No  → ローカルにも保存
    │
    └─ 失敗 → [ローカル保存] (フォールバック)
```

### 2. 写真配信 (`serve_photo`)

```
[リクエスト]
    ↓
[ローカルに存在?]
    ├─ Yes → ローカルから配信
    │
    └─ No → [NASから取得]
              ├─ 成功 → NASから配信
              └─ 失敗 → 404エラー
```

### 3. 写真削除 (`delete_photo`)

```
[削除リクエスト]
    ↓
[NASから削除試行]
    ↓
[ローカルから削除]
    ↓
[サムネイル削除]
    ↓
[DB削除]
```

---

## 🔑 重要な実装ポイント

### シングルトンパターン

```python
_nas_client = None

def get_nas_client() -> NASWebDAVClient:
    global _nas_client
    if _nas_client is None:
        _nas_client = NASWebDAVClient()
    return _nas_client
```

### 画像圧縮

```python
# RGBA → RGB変換（透過対応）
if img.mode in ('RGBA', 'LA', 'P'):
    background = Image.new('RGB', img.size, (255, 255, 255))
    img = img.convert('RGBA') if img.mode == 'P' else img
    background.paste(img, mask=img.split()[-1])
    img = background

# リサイズ＋JPEG保存
img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
img.save(output, format='JPEG', quality=quality, optimize=True)
```

### ディレクトリ自動作成

```python
def _ensure_directory(self, remote_path: str) -> bool:
    if not self.client.check(remote_path):
        self.client.mkdir(remote_path)
    return True
```

### フルパス生成

```python
full_remote_path = f"{self.base_path}/{remote_path}".replace('//', '/')
# 例: /home/eacon_keep_pict/aircon_reports/before/abc123.jpg
```

---

## 🚨 エラーハンドリング

### 堅牢な保存処理

```python
nas_saved = False
try:
    nas_client = get_nas_client()
    if nas_client.is_available():
        success, error = nas_client.upload_file(data, path)
        nas_saved = success
except Exception as e:
    logger.error(f"NAS保存エラー: {e}")

# フォールバック
if not nas_saved or not is_render:
    # ローカル保存
    pass
```

### ログメッセージ

```
✅ NAS保存成功
⚠️ NAS保存失敗
❌ NAS保存エラー
💾 ローカル保存成功
🚀 Render環境: ローカル保存スキップ
```

---

## 🔐 セキュリティチェックリスト

- [ ] `.env`を`.gitignore`に追加
- [ ] Tailscale VPNで通信暗号化
- [ ] Basic認証をVPNトンネル内で送信
- [ ] UUID + タイムスタンプでファイル名の安全性確保
- [ ] NASユーザーに必要最小限の権限のみ付与
- [ ] 定期的なNASバックアップ

---

## 🛠️ トラブルシューティング早見表

| エラー | 原因 | 対処 |
|--------|------|------|
| NAS接続チェック失敗 | Tailscale未起動 | `tailscale status`で確認 |
| 401 Unauthorized | 認証情報エラー | ユーザー名/パスワード確認 |
| ディレクトリ作成失敗 | 権限不足 | NASの書き込み権限確認 |
| 画像圧縮エラー | Pillow未インストール | `pip install Pillow` |

---

## ⚡ パフォーマンス指標

| 項目 | 値 |
|------|-----|
| 圧縮率 | 80-90% |
| 画質 | JPEG 70% |
| 最大解像度 | 700x500px |
| NASアップロード | 1-3秒/枚 |
| ローカル保存 | 0.1-0.5秒/枚 |

---

## 📝 実装チェックリスト

### WebDAVクライアント (`nas_webdav.py`)
- [ ] `NASWebDAVClient`クラス
- [ ] `__init__`: 環境変数読み込み、クライアント初期化
- [ ] `_validate_config`: 設定検証
- [ ] `is_available`: 接続チェック
- [ ] `_ensure_directory`: ディレクトリ作成
- [ ] `upload_file`: アップロード
- [ ] `download_file`: ダウンロード
- [ ] `delete_file`: 削除
- [ ] `test_connection`: 接続テスト
- [ ] `get_nas_client`: シングルトン取得

### ファイルハンドラー (`file_handler.py`)
- [ ] `allowed_file`: 拡張子チェック
- [ ] `compress_image`: 画像圧縮
- [ ] `save_photo`: 写真保存（NAS優先）
- [ ] `create_thumbnail`: サムネイル作成
- [ ] `delete_photo`: 写真削除（両方）
- [ ] `get_photo_from_nas`: NASから取得

### ルート実装
- [ ] 写真アップロードエンドポイント
- [ ] 写真配信エンドポイント
- [ ] 写真削除エンドポイント

### 環境設定
- [ ] `.env`ファイル作成
- [ ] 環境変数設定
- [ ] Tailscale VPN設定
- [ ] NAS WebDAV有効化

---

## 🎯 最小実装例

### 1. WebDAVクライアント初期化

```python
from webdav3.client import Client

options = {
    'webdav_hostname': os.environ['NAS_WEBDAV_URL'],
    'webdav_login': os.environ['NAS_USERNAME'],
    'webdav_password': os.environ['NAS_PASSWORD'],
    'webdav_timeout': 30,
}
client = Client(options)
```

### 2. ファイルアップロード

```python
import io

buffer = io.BytesIO(file_data)
client.upload_to(buffer, '/home/eacon_keep_pict/aircon_reports/before/test.jpg')
```

### 3. ファイルダウンロード

```python
buffer = io.BytesIO()
client.download_from(buffer, '/home/eacon_keep_pict/aircon_reports/before/test.jpg')
file_data = buffer.getvalue()
```

### 4. ファイル削除

```python
client.clean('/home/eacon_keep_pict/aircon_reports/before/test.jpg')
```

---

## 📚 関連ドキュメント

- [完全ガイド](./NAS_PHOTO_STORAGE_LOGIC.md) - 詳細な実装ドキュメント
- [セットアップガイド](./NAS_SETUP_GUIDE.md) - 環境構築手順
- `app/utils/nas_webdav.py` - WebDAVクライアント実装
- `app/utils/file_handler.py` - ファイルハンドラー実装

---

## 💡 Tips

1. **開発環境**: NASとローカルの両方に保存 → デバッグしやすい
2. **本番環境**: NAS成功時はローカルスキップ → ディスク容量節約
3. **画像圧縮**: 必ず実施 → 80-90%容量削減
4. **ログ出力**: 絵文字で視認性向上 (✅❌💾🚀)
5. **エラー時**: 処理継続 → ユーザー体験を損なわない

---

**作成日**: 2025-01-17  
**バージョン**: 1.0  
**対象システム**: エアコンクリーニング報告書システム

