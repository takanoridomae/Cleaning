# ローカル起動ガイド

## 📋 概要

このガイドでは、Windows環境でエアコンクリーニング報告書システムをローカルで起動する方法を説明します。

## 🚀 起動方法

### 方法1: 簡単起動（推奨）

最も簡単な起動方法です。ダブルクリックするだけで起動できます。

1. **`start_local.bat`** をダブルクリック
2. ブラウザで `http://localhost:5000` にアクセス

### 方法2: 詳細チェック付き起動

NAS接続テストやデータベースバックアップなど、詳細なチェックを行いながら起動します。

1. **`start_local_with_check.bat`** をダブルクリック
2. 画面の指示に従って進める
3. ブラウザで `http://localhost:5000` にアクセス

### 方法3: 手動起動

```powershell
# 1. 仮想環境のアクティベート
.\venv\Scripts\activate

# 2. アプリケーションの起動
python run.py
```

## 📦 初回セットアップ

### 1. Python環境の準備

Pythonがインストールされていない場合:
- [Python公式サイト](https://www.python.org/downloads/)からPython 3.8以上をダウンロード
- インストール時に「Add Python to PATH」にチェックを入れる

### 2. 仮想環境の作成

```powershell
# プロジェクトルートディレクトリに移動
cd C:\eacon_report_nas_local

# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
.\venv\Scripts\activate

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定（NAS使用の場合）

プロジェクトルートに `.env` ファイルを作成:

```bash
# NAS機能を有効化
NAS_ENABLED=True

# NAS WebDAV URL（TailscaleのIPアドレス:ポート）
NAS_WEBDAV_URL=http://100.69.218.15:5005

# NASログイン情報
NAS_USERNAME=Takanori
NAS_PASSWORD=あなたのパスワード

# NAS保存先ベースパス
NAS_BASE_PATH=/home/eacon_keep_pict
```

詳細は `ENV_SETUP_INSTRUCTIONS.md` を参照してください。

### 4. Tailscale VPNの起動（NAS使用の場合のみ）

NASを使用する場合は、Tailscale VPNを起動してください。

**確認方法:**
```powershell
tailscale status
```

**起動方法:**
- システムトレイのTailscaleアイコンをクリック
- または、Tailscaleアプリケーションを起動

## 🔧 各起動スクリプトの違い

### `start_local.bat`（シンプル版）

**特徴:**
- 最小限のチェックのみ実行
- 起動が速い
- 自動で全ての処理を実行

**実行内容:**
1. 仮想環境のアクティベート
2. データベースファイルの確認
3. 環境変数ファイルの確認
4. Tailscale接続の確認
5. Flaskアプリケーションの起動

**こんな時に使用:**
- 日常的な起動
- 設定がすでに完了している場合
- 素早く起動したい場合

### `start_local_with_check.bat`（詳細版）

**特徴:**
- 詳細なチェックを実行
- インタラクティブな操作が可能
- トラブルシューティングに便利

**実行内容:**
1. 仮想環境のアクティベート（ない場合は作成を提案）
2. データベースのバックアップ作成
3. 環境変数の詳細確認（サンプル表示機能）
4. Tailscale接続の詳細確認
5. NAS接続テスト（オプション）
6. Flaskアプリケーションの起動

**こんな時に使用:**
- 初回起動時
- 問題が発生した場合
- NAS接続を確認したい場合
- データベースバックアップを取りたい場合

## 🌐 アクセス方法

### ローカルからのアクセス

ブラウザで以下のURLにアクセス:
- `http://localhost:5000`
- `http://127.0.0.1:5000`

### ネットワーク上の他のデバイスからのアクセス

1. このPCのIPアドレスを確認:
   ```powershell
   ipconfig
   ```
   `IPv4 アドレス` をメモ（例: 192.168.1.100）

2. ブラウザで以下のURLにアクセス:
   ```
   http://192.168.1.100:5000
   ```

## 🛑 停止方法

### バッチファイルで起動した場合

1. コマンドプロンプトウィンドウをアクティブにする
2. `Ctrl + C` を押す
3. "バッチ ジョブを終了しますか (Y/N)?" → `Y` を入力
4. ウィンドウを閉じる

### 手動起動した場合

1. コマンドプロンプトで `Ctrl + C` を押す
2. ウィンドウを閉じる

## 📊 データベースについて

### データベースファイルの場所

```
instance/aircon_report.db
```

### バックアップの場所

```
db_backups/
├── startup/     # 起動時のバックアップ（最新5つ保持）
├── daily/       # 日次バックアップ（30日分保持）
└── manual/      # 手動バックアップ（最新10個保持）
```

### バックアップのタイミング

- **起動時**: `start_local_with_check.bat` 使用時に自動作成
- **日次**: 毎日午前3時に自動作成（アプリケーション起動中）
- **手動**: バックアップスクリプトを実行

## 💾 NAS写真保存システムについて

### NASを使用する場合

1. `.env` ファイルで `NAS_ENABLED=True` に設定
2. Tailscale VPNを起動
3. NAS接続テストを実行:
   ```powershell
   python scripts\utilities\test_nas_connection.py
   ```

詳細は以下のドキュメントを参照:
- `README_NAS.md` - NASシステムの概要
- `docs/NAS_SETUP_GUIDE.md` - セットアップガイド
- `ENV_SETUP_INSTRUCTIONS.md` - 環境変数設定

### NASを使用しない場合

1. `.env` ファイルで `NAS_ENABLED=False` に設定
2. または `.env` ファイルを作成しない
3. すべての写真は `uploads/` フォルダに保存されます

## 🔍 トラブルシューティング

### 問題1: 仮想環境が見つからない

**エラーメッセージ:**
```
❌ エラー: 仮想環境が見つかりません。
```

**解決方法:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 問題2: ポート5000が使用中

**エラーメッセージ:**
```
Address already in use
```

**解決方法:**

**方法A: 他のアプリケーションを終了**
```powershell
# ポート5000を使用しているプロセスを確認
netstat -ano | findstr :5000

# タスクマネージャーでそのプロセスを終了
```

**方法B: 別のポートで起動**

`run.py` の最終行を編集:
```python
# 変更前
app.run(debug=True, host="0.0.0.0")

# 変更後（ポート8080を使用）
app.run(debug=True, host="0.0.0.0", port=8080)
```

### 問題3: NASに接続できない

**確認事項:**
1. Tailscale VPNが起動しているか
   ```powershell
   tailscale status
   ```

2. NASにpingが通るか
   ```powershell
   ping 100.69.218.15
   ```

3. `.env` ファイルの設定が正しいか

4. NAS接続テストを実行
   ```powershell
   python scripts\utilities\test_nas_connection.py
   ```

### 問題4: データベースエラー

**エラーメッセージ:**
```
database is locked
```

**解決方法:**
1. 他のアプリケーションでデータベースを開いていないか確認
2. アプリケーションを再起動
3. データベースファイルを修復:
   ```powershell
   python scripts\db_tools\fix_database.py
   ```

### 問題5: パッケージが見つからない

**エラーメッセージ:**
```
ModuleNotFoundError: No module named 'flask'
```

**解決方法:**
```powershell
# 仮想環境をアクティベート
.\venv\Scripts\activate

# パッケージを再インストール
pip install -r requirements.txt
```

## 📝 ログの確認

アプリケーションのログは、起動したコマンドプロンプトウィンドウに表示されます。

### NAS保存成功時のログ例

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

## 🔐 セキュリティに関する注意

### .envファイルの管理

- `.env` ファイルには機密情報（パスワード）が含まれます
- Gitにコミットしないでください（`.gitignore` で除外済み）
- バックアップする場合は、安全な場所に保管してください

### データベースのバックアップ

- 定期的にバックアップを取ることを推奨します
- バックアップは `db_backups/` フォルダに保存されます
- 重要なデータは外部ストレージにもバックアップしてください

## 📚 関連ドキュメント

- `README.md` - プロジェクト全体の説明
- `README_NAS.md` - NAS写真保存システムの説明
- `ENV_SETUP_INSTRUCTIONS.md` - 環境変数設定ガイド
- `docs/NAS_SETUP_GUIDE.md` - NAS詳細セットアップガイド
- `.cursor/rules/kouzou.mdc` - プロジェクト構造

## 💡 ヒント

### デバッグモードについて

`run.py` はデバッグモードで起動します:
- コードの変更が自動的に反映されます
- 詳細なエラーメッセージが表示されます
- **本番環境では使用しないでください**

### 開発時の便利なツール

```powershell
# データベースの内容を確認
python scripts\db_tools\check_db.py

# データベースの統計情報を表示
python scripts\db_tools\check_data_statistics.py

# ユーザー権限を確認
python scripts\check_user_permissions.py
```

## 🆘 サポート

問題が解決しない場合は、以下の情報を記録してサポートに連絡してください:

1. エラーメッセージの全文
2. 起動スクリプトの実行結果
3. Python バージョン (`python --version`)
4. OS バージョン
5. `.env` ファイルの設定（パスワード部分は伏せる）

---

**バージョン**: 1.0  
**最終更新**: 2025-10-14  
**対象OS**: Windows 10/11

