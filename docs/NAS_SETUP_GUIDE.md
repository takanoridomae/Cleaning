# NAS写真保存システム セットアップガイド

## 概要

このシステムは、UGREEN NASをWebDAV経由で利用して写真を保存する機能を提供します。
NASが利用できない場合は自動的にローカルストレージ（Renderの場合はPersistent Disk）にフォールバックします。

## システム構成

### 保存の優先順位

1. **優先**: UGREEN NAS（容量無制限）
2. **フォールバック**: ローカルストレージ / Renderの Persistent Disk

### 主な機能

- ✅ WebDAV経由でNASに自動保存
- ✅ 画像の自動圧縮（最大700x500px, JPEG品質70%）
- ✅ NAS接続失敗時の自動フォールバック
- ✅ NASとローカルの両方からの画像取得
- ✅ 削除時のNASとローカル両方での削除

## セットアップ手順

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルを作成し、以下の設定を追加します:

```bash
# NAS機能を有効化
NAS_ENABLED=True

# NAS WebDAV URL（TailscaleのIPアドレス:ポート）
NAS_WEBDAV_URL=http://100.69.218.15:5005

# NASログイン情報
NAS_USERNAME=Takanori
NAS_PASSWORD=your-password-here

# NAS保存先ベースパス
NAS_BASE_PATH=/home/eacon_keep_pict
```

### 3. Tailscale VPNの起動（必須）

NASへのリモートアクセスにはTailscale VPNが必要です。

**Windows:**
```powershell
# Tailscaleの状態確認
tailscale status

# 起動していない場合
# システムトレイからTailscaleを起動
```

**Linux/Mac:**
```bash
# Tailscaleの状態確認
tailscale status

# 起動
sudo tailscale up
```

### 4. NAS WebDAVサービスの有効化

UGREEN NASの管理画面で以下を確認:

1. WebDAVサービスが有効になっていること
2. ポート5005でアクセス可能なこと
3. ユーザー権限が適切に設定されていること

### 5. 接続テスト

Pythonスクリプトで接続テストを実行:

```python
from app.utils.nas_webdav import get_nas_client

nas_client = get_nas_client()
success, message = nas_client.test_connection()

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

## NASフォルダ構造

写真は以下の構造でNASに保存されます:

```
/home/eacon_keep_pict/
└── aircon_reports/
    ├── before/
    │   ├── abc123_1234567890.jpg
    │   ├── def456_1234567891.jpg
    │   └── ...
    └── after/
        ├── ghi789_1234567892.jpg
        ├── jkl012_1234567893.jpg
        └── ...
```

## 使用方法

### 写真のアップロード

通常通りアプリケーションから写真をアップロードするだけです。
システムが自動的に以下を実行します:

1. 画像を圧縮（700x500px, JPEG 70%品質）
2. NASへのアップロードを試行
3. NAS接続失敗時はローカルストレージに保存
4. サムネイルの自動生成

### 写真の表示

写真のURLにアクセスすると、以下の順序で画像を取得します:

1. ローカルストレージに存在する場合 → ローカルから配信
2. ローカルにない場合 → NASから取得して配信

### 写真の削除

写真を削除すると、NASとローカルストレージの両方から削除されます。

## トラブルシューティング

### NAS接続エラー

**症状**: 写真がNASに保存されない

**対処法**:
1. Tailscale VPNが起動しているか確認
   ```bash
   tailscale status
   ```

2. NASのIPアドレスにアクセスできるか確認
   ```bash
   ping 100.69.218.15
   ```

3. NAS_WEBDAV_URLが正しいか確認
   ```bash
   echo $NAS_WEBDAV_URL
   ```

4. WebDAVサービスが起動しているか確認
   - NAS管理画面にログイン
   - サービス > WebDAV を確認

### 認証エラー

**症状**: `WebDAVアップロードエラー: 401 Unauthorized`

**対処法**:
1. NAS_USERNAMEとNAS_PASSWORDが正しいか確認
2. NASのユーザー権限を確認
3. WebDAVサービスの認証設定を確認

### ディレクトリ作成エラー

**症状**: `ディレクトリ作成失敗`

**対処法**:
1. NAS_BASE_PATHが存在するか確認
2. ユーザーに書き込み権限があるか確認
3. NASの容量が十分にあるか確認

## ログの確認

アプリケーションログで以下のメッセージを確認できます:

### 成功時のログ
```
✅ NAS保存成功: aircon_reports/before/abc123_1234567890.jpg
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

### NAS利用不可時のログ
```
💾 NASが利用できないため、ローカルストレージに保存します
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

### エラー時のログ
```
❌ NAS保存エラー: [エラーメッセージ]
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

## パフォーマンス

### 画像圧縮

- **元のサイズ**: 2-5MB (スマートフォン撮影)
- **圧縮後**: 100-500KB (約80-90%削減)
- **画質**: JPEG 70%品質（実用上問題なし）

### アップロード時間

- **NASへのアップロード**: 1-3秒/枚（Tailscale経由）
- **ローカル保存**: 0.1-0.5秒/枚

## セキュリティ

### 通信の暗号化

- Tailscale VPNトンネル内で通信が暗号化されます
- Basic認証の認証情報もVPNトンネル内で送信されます

### アクセス制御

- Tailscaleネットワーク内のデバイスのみアクセス可能
- NASの権限設定でフォルダーアクセスを制限可能

### ベストプラクティス

1. `.env` ファイルをGitにコミットしない（`.gitignore`に追加済み）
2. 強力なパスワードを使用
3. 定期的なNASバックアップの実施
4. Tailscaleのアクセス制御リストを適切に設定

## Render環境での設定

Renderにデプロイする場合:

1. **Environment Variables**に以下を設定:
   ```
   NAS_ENABLED=True
   NAS_WEBDAV_URL=http://100.69.218.15:5005
   NAS_USERNAME=Takanori
   NAS_PASSWORD=your-password
   NAS_BASE_PATH=/home/dotaka_keep
   ```

2. **注意**: RenderサーバーからTailscaleネットワークにアクセスできない場合、NASへの保存は失敗し、自動的にPersistent Diskにフォールバックします。

3. Renderサーバーでもnasを使用したい場合は、RenderサーバーにTailscaleをインストールする必要があります（別途設定が必要）。

## 関連ファイル

- `app/utils/nas_webdav.py` - NAS WebDAVクライアント
- `app/utils/file_handler.py` - ファイル保存・取得・削除
- `requirements.txt` - 必要なパッケージ（webdavclient3を含む）
- `.env.example` - 環境変数設定例

## サポート

問題が発生した場合は、以下を確認してください:

1. アプリケーションログ
2. Tailscale接続状態
3. NAS WebDAVサービス状態
4. 環境変数設定

それでも解決しない場合は、ログファイルを添えて報告してください。

