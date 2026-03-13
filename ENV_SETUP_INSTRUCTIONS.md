# 環境変数設定手順

## NAS写真保存システムを有効にするための設定

プロジェクトルートに `.env` ファイルを作成し、以下の内容を追加してください。

```bash
# ============================================================
# NAS WebDAV設定（写真保存用）
# ============================================================

# NAS機能を有効にする（TrueまたはFalse）
NAS_ENABLED=True

# NAS WebDAV URL（TailscaleのIPアドレス:ポート番号）
NAS_WEBDAV_URL=http://100.69.218.15:5005

# NASログインユーザー名
NAS_USERNAME=Takanori

# NASログインパスワード
NAS_PASSWORD=あなたのパスワードをここに入力

# NAS保存先ベースパス
NAS_BASE_PATH=/home/eacon_keep_pict

# ============================================================
# その他の設定（既存の設定はそのまま維持）
# ============================================================

# Flask設定
SECRET_KEY=your-secret-key-here

# アップロードフォルダ設定（ローカルまたはPersistent Disk）
UPLOAD_FOLDER=uploads
```

## 設定後の確認

環境変数を設定したら、以下のコマンドで接続テストを実行してください：

```bash
python scripts/utilities/test_nas_connection.py
```

## 注意事項

1. **Tailscale VPNが必須**: NASにアクセスするには、Tailscale VPNが起動している必要があります
2. **.envファイルの管理**: `.env`ファイルは絶対にGitにコミットしないでください（.gitignoreに含まれています）
3. **パスワードのセキュリティ**: 強力なパスワードを使用してください

## NAS機能を無効にする場合

NAS機能を使用せず、ローカルストレージのみを使用する場合：

```bash
NAS_ENABLED=False
```

この場合、写真はすべて `uploads/` フォルダ（Renderの場合はPersistent Disk）に保存されます。

