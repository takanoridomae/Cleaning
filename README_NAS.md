# NAS写真保存システム - セットアップと使用方法

## 📋 概要

このシステムは、写真をUGREEN NASに保存する機能を追加したものです。
NAS接続が失敗した場合は、自動的にローカルストレージ（Renderの場合はPersistent Disk）にフォールバックします。

## 🎯 主な変更点

### 1. 新規追加ファイル

- `app/utils/nas_webdav.py` - NAS WebDAVクライアント
- `docs/NAS_SETUP_GUIDE.md` - 詳細なセットアップガイド
- `scripts/utilities/test_nas_connection.py` - NAS接続テストスクリプト
- `README_NAS.md` - このファイル

### 2. 更新ファイル

- `requirements.txt` - webdavclient3とrequestsを追加
- `app/utils/file_handler.py` - NAS保存機能と画像圧縮機能を追加
- `app/__init__.py` - NASから画像を取得する機能を追加

## 🚀 クイックスタート

### ステップ1: 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### ステップ2: 環境変数の設定

`.env` ファイルに以下を追加:

```bash
# NAS機能を有効化
NAS_ENABLED=True

# NAS WebDAV URL
NAS_WEBDAV_URL=http://100.69.218.15:5005

# NASログイン情報
NAS_USERNAME=Takanori
NAS_PASSWORD=your-password-here

# NAS保存先ベースパス
NAS_BASE_PATH=/home/eacon_keep_pict
```

### ステップ3: Tailscale VPNの起動

```bash
# 接続状態の確認
tailscale status

# 起動（必要な場合）
sudo tailscale up
```

### ステップ4: 接続テストの実行

```bash
python scripts/utilities/test_nas_connection.py
```

成功すると以下のような出力が表示されます:

```
============================================================
NAS接続テスト
============================================================

[1] 環境変数の確認
------------------------------------------------------------
NAS_ENABLED: True
NAS_WEBDAV_URL: http://100.69.218.15:5005
NAS_USERNAME: Takanori
NAS_PASSWORD: ***********
NAS_BASE_PATH: /home/dotaka_keep

[2] NASクライアントの初期化
------------------------------------------------------------
✅ NASクライアント初期化成功

[3] NAS接続テスト
------------------------------------------------------------
✅ NAS接続成功: http://100.69.218.15:5005/home/dotaka_keep

[4] テストファイルのアップロード
------------------------------------------------------------
✅ テストファイルアップロード成功: aircon_reports/test/test_file.txt

[5] テストファイルのダウンロード
------------------------------------------------------------
✅ テストファイルダウンロード成功
   内容: Test file content from NAS connection test
✅ ファイル内容が一致しました

[6] テストファイルの削除
------------------------------------------------------------
✅ テストファイル削除成功

============================================================
✅ すべてのテストが完了しました
============================================================

NASへの写真保存システムは正常に動作しています。
アプリケーションから写真をアップロードしてください。
```

## 💾 保存の仕組み

### 保存の優先順位

1. **NAS** (優先)
   - 容量: 無制限
   - 場所: `/home/eacon_keep_pict/aircon_reports/{before|after}/`
   - 接続: Tailscale VPN経由のWebDAV

2. **ローカルストレージ** (フォールバック)
   - 容量: 制限あり
   - 場所: `uploads/{before|after}/`
   - 接続: 直接アクセス

### 保存フロー

```
写真アップロード
    ↓
画像圧縮 (700x500px, JPEG 70%)
    ↓
┌─────────────────┐
│ NASに保存を試行  │
└─────────────────┘
    ↓
┌──────┐    ┌──────┐
│ 成功 │    │ 失敗 │
└──────┘    └──────┘
    ↓           ↓
    └───────────┘
         ↓
ローカルにも保存（バックアップまたはフォールバック）
```

### 画像の取得

```
画像リクエスト
    ↓
┌────────────────────┐
│ ローカルに存在？    │
└────────────────────┘
    ↓
┌─────┐      ┌─────┐
│ Yes │      │ No  │
└─────┘      └─────┘
    ↓            ↓
ローカルから    NASから
  配信          取得
    └──────┬─────┘
           ↓
      ユーザーに配信
```

## 📊 画像圧縮の仕様

- **最大サイズ**: 700px × 500px
- **フォーマット**: JPEG
- **品質**: 70%
- **圧縮率**: 約80-90%削減

### 圧縮前後の比較

| 項目 | 圧縮前 | 圧縮後 |
|-----|-------|-------|
| ファイルサイズ | 2-5MB | 100-500KB |
| 解像度 | 3000×4000px | 700×500px |
| 品質 | オリジナル | JPEG 70% |

## 🔒 セキュリティ

### 通信の暗号化

- Tailscale VPNトンネル内で通信が暗号化
- Basic認証もVPN内で安全に送信

### アクセス制御

- Tailscaleネットワーク内のデバイスのみアクセス可能
- NASの権限設定でフォルダーアクセスを制限

### ベストプラクティス

1. `.env` ファイルをGitにコミットしない
2. 強力なパスワードを使用
3. 定期的なNASバックアップの実施

## 📝 ログの確認

### 成功時のログ例

```
画像圧縮: 2048000 bytes → 153600 bytes (92% 削減)
✅ NAS保存成功: aircon_reports/before/abc123_1728912345.jpg
💾 ローカル保存成功: uploads/before/abc123_1728912345.jpg
```

### NAS利用不可時のログ例

```
💾 NASが利用できないため、ローカルストレージに保存します
💾 ローカル保存成功: uploads/before/abc123_1728912345.jpg
```

## 🔧 トラブルシューティング

### NAS接続エラー

**問題**: NASに接続できない

**確認事項**:
1. Tailscale VPNが起動しているか
   ```bash
   tailscale status
   ```

2. NASにpingが通るか
   ```bash
   ping 100.69.218.15
   ```

3. WebDAVサービスが起動しているか
   - NAS管理画面で確認

4. 環境変数が正しく設定されているか
   ```bash
   python scripts/utilities/test_nas_connection.py
   ```

### 認証エラー

**問題**: `401 Unauthorized` エラー

**解決方法**:
1. NAS_USERNAMEとNAS_PASSWORDを確認
2. NASのユーザー権限を確認
3. WebDAVサービスの認証設定を確認

### 画像が表示されない

**問題**: アップロードした画像が表示されない

**確認事項**:
1. ブラウザのコンソールでエラーを確認（F12）
2. サーバーログでエラーを確認
3. ファイルが実際に保存されているか確認:
   - ローカル: `uploads/before/` または `uploads/after/`
   - NAS: `/home/eacon_keep_pict/aircon_reports/before/` または `/after/`

## 🌐 Render環境での使用

### NASを使用する場合

RenderサーバーでNASを使用するには、RenderサーバーにTailscaleをインストールする必要があります。
これには追加のセットアップが必要です。

### NASを使用しない場合

環境変数を以下のように設定:

```bash
NAS_ENABLED=False
```

この場合、すべての写真はPersistent Diskに保存されます。

## 📦 既存写真のNAS移行

Renderや他の環境に保存されている既存の写真をNASに移行する方法については、
以下のドキュメントを参照してください:

### Render環境からの移行

1. **直接移行（Render Shell使用）**
   - `docs/RENDER_PHOTO_MIGRATION_GUIDE.md` を参照
   - Render環境でスクリプトを実行してNASに直接転送
   - ⚠️ Tailscale VPNアクセスが必要

2. **ローカルPC経由（推奨）**
   - `docs/RENDER_TO_NAS_MIGRATION_ALTERNATIVE.md` を参照
   - Renderから写真をダウンロード → ローカルPCでNASにアップロード
   - Tailscale VPNが使えない場合はこちらを使用

### ローカル環境からの移行

既にローカルに写真がある場合:

```bash
python migrate_existing_photos_to_nas.py
```

このスクリプトは `uploads/before/` と `uploads/after/` 内の写真をNASに移行します。

## 📚 関連ドキュメント

- `docs/NAS_SETUP_GUIDE.md` - 詳細なセットアップガイド
- `docs/RENDER_PHOTO_MIGRATION_GUIDE.md` - Render既存写真のNAS移行ガイド
- `docs/RENDER_TO_NAS_MIGRATION_ALTERNATIVE.md` - ローカルPC経由の代替移行方法
- `nas-photo-storage-system-rules.json` - システム仕様書

## ⚙️ 実装ファイル

### コア機能

- **NAS WebDAVクライアント**: `app/utils/nas_webdav.py`
  - NASへの接続、アップロード、ダウンロード、削除

- **ファイルハンドラー**: `app/utils/file_handler.py`
  - 画像圧縮
  - ハイブリッド保存（NAS + ローカル）
  - フォールバック処理

- **画像配信**: `app/__init__.py`
  - ローカル優先、NASフォールバックでの画像配信

### テスト・ユーティリティ

- **接続テスト**: `scripts/utilities/test_nas_connection.py`
  - NAS接続の診断とテスト

## 📞 サポート

問題が発生した場合:

1. テストスクリプトを実行:
   ```bash
   python scripts/utilities/test_nas_connection.py
   ```

2. ログを確認:
   - アプリケーションログ
   - Tailscaleログ
   - NASログ

3. 環境変数を確認:
   ```bash
   echo $NAS_ENABLED
   echo $NAS_WEBDAV_URL
   ```

---

**バージョン**: 1.0  
**最終更新**: 2025-10-14  
**互換性**: Python 3.8+, Flask 3.0+

