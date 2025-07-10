# スケジュール通知機能セットアップガイド

## 概要

このガイドでは、エアコンクリーニング完了報告書システムのスケジュール通知機能の設定方法を説明します。
この機能により、Gmailを使用してスケジュールの開始前リマインダーや開始通知を自動送信できます。

## 前提条件

- Googleアカウント（Gmail）
- 2段階認証が有効化されたGoogleアカウント
- アプリパスワードの作成権限

## セットアップ手順

### 1. Gmailアプリパスワードの作成

1. **Googleアカウントにログイン**
   - [Google Account Settings](https://myaccount.google.com/) にアクセス

2. **2段階認証の有効化**
   - 「セキュリティ」タブを選択
   - 「2段階認証プロセス」を有効化

3. **アプリパスワードの生成**
   - 「セキュリティ」→「アプリパスワード」を選択
   - アプリを選択：「メール」
   - デバイスを選択：「その他（カスタム名）」
   - 名前：「エアコン報告書システム」
   - **16文字のパスワードをメモ**（スペースなしで保存）

### 2. 環境変数ファイルの作成

1. **プロジェクトルートに .env ファイルを作成**
   ```bash
   # プロジェクトルートディレクトリ
   touch .env
   ```

2. **.env ファイルに以下の内容を追加**
   ```bash
   # 基本設定
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development

   # データベース設定
   DATABASE_URL=sqlite:///instance/aircon_report.db

   # Gmail SMTP設定（通知機能）
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USE_SSL=False
   MAIL_USERNAME=your-gmail-address@gmail.com
   MAIL_PASSWORD=your-16-digit-app-password
   MAIL_DEFAULT_SENDER=your-gmail-address@gmail.com

   # 通知設定
   NOTIFICATION_ENABLED=True
   NOTIFICATION_CHECK_INTERVAL=60
   ```

3. **実際の値に置き換え**
   - `your-gmail-address@gmail.com` → 実際のGmailアドレス
   - `your-16-digit-app-password` → 手順1で取得した16文字のアプリパスワード
   - `your-secret-key-here` → ランダムな文字列

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

新しく追加された依存関係：
- `Flask-Mail==0.9.1` - メール送信機能
- `APScheduler==3.10.4` - バックグラウンドタスク実行

### 4. アプリケーションの起動

```bash
python run.py
```

### 5. 通知機能の動作確認

1. **システムにログイン**
   - 管理者権限のユーザーでログイン

2. **通知管理画面にアクセス**
   - ナビゲーションメニューから「通知管理」を選択
   - URL: `http://localhost:5000/notifications/`

3. **設定状況の確認**
   - 「設定完了」バッジが表示されることを確認
   - 緑色のチェックマークが表示されることを確認

4. **テストメール送信**
   - 「テストメール送信」ボタンをクリック
   - 設定したGmailアドレスにテストメールが届くことを確認

## 機能説明

### 自動通知機能

**リマインダー通知**
- スケジュール開始の指定分数前（デフォルト：30分前）
- 通知が有効な未完了スケジュールが対象

**開始通知**
- スケジュール開始時刻から5分以内
- リアルタイムでの開始確認

### 手動通知機能

**個別通知送信**
- スケジュール詳細画面から手動送信
- リマインダー・開始通知・完了通知の選択可能

**一括通知チェック**
- 通知管理画面から手動実行
- 送信対象スケジュールの一括チェック

### 通知送信先

**自動判定される送信先**
1. スケジュール作成者のメールアドレス
2. 関連する顧客のメールアドレス

## トラブルシューティング

### 設定が「未完了」と表示される場合

1. **.env ファイルの確認**
   - ファイルがプロジェクトルートに存在するか
   - 必要な環境変数がすべて設定されているか
   - スペルミスがないか

2. **Gmailアプリパスワードの確認**
   - 16文字すべてが正しく入力されているか
   - スペースが含まれていないか
   - 2段階認証が有効になっているか

3. **アプリケーションの再起動**
   ```bash
   # アプリケーションを停止（Ctrl+C）
   # 再起動
   python run.py
   ```

### テストメールが送信されない場合

1. **ネットワーク接続の確認**
   - インターネット接続が正常か
   - ファイアウォールでSMTPポート（587）がブロックされていないか

2. **Gmail設定の確認**
   - アプリパスワードが正しく生成されているか
   - アカウントが一時的にロックされていないか

3. **ログの確認**
   - コンソール出力でエラーメッセージを確認
   - 詳細なエラー情報を確認

### 自動通知が送信されない場合

1. **スケジューラーの状態確認**
   - アプリケーションログでスケジューラーの開始を確認
   - 通知管理画面で次回実行時刻を確認

2. **スケジュール設定の確認**
   - 通知が有効になっているか（`notification_enabled=True`）
   - 通知タイミングが適切か（`notification_minutes`）
   - スケジュールが未完了ステータスか

## セキュリティ注意事項

### .env ファイルの管理

- **.env ファイルは `.gitignore` に含まれている**
  - Gitリポジトリにコミットされません
  - 機密情報の漏洩を防止

- **本番環境での管理**
  - サーバー環境では適切な権限設定
  - 定期的なアプリパスワードの更新を推奨

### アプリパスワードの管理

- **定期的な更新**
  - 3～6ヶ月ごとの更新を推奨

- **安全な保管**
  - パスワード管理ツールでの保管
  - 平文でのファイル保存は避ける

## 設定例

### 開発環境用 .env
```bash
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/aircon_report.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=test@gmail.com
MAIL_PASSWORD=abcdefghijklmnop
MAIL_DEFAULT_SENDER=test@gmail.com
NOTIFICATION_ENABLED=True
NOTIFICATION_CHECK_INTERVAL=60
```

### 本番環境での推奨設定
```bash
SECRET_KEY=complex-random-secret-key-for-production
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/aircon_report.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=notifications@yourdomain.com
MAIL_PASSWORD=your-secure-app-password
MAIL_DEFAULT_SENDER=notifications@yourdomain.com
NOTIFICATION_ENABLED=True
NOTIFICATION_CHECK_INTERVAL=300
```

## サポート

設定に関するお問い合わせや不明点がある場合は、システム管理者にご連絡ください。 