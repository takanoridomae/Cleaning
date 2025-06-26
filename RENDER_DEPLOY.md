# Renderデプロイガイド

## 概要
このFlaskアプリケーションをRenderでデプロイするためのガイドです。

## デプロイ手順

### 1. Renderアカウントの準備
1. [Render](https://render.com)でアカウントを作成
2. GitHubアカウントと連携

### 2. 新しいWebサービスの作成
1. Renderダッシュボードで「New +」→「Web Service」を選択
2. GitHubリポジトリを接続
3. 以下の設定を入力：

#### 基本設定
- **Name**: `aircon-report` (任意)
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn --config gunicorn.conf.py wsgi:app`

#### 環境変数設定
以下の環境変数を「Environment」タブで設定してください：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `FLASK_ENV` | `production` | Flask環境設定 |
| `SECRET_KEY` | (自動生成) | セッション暗号化キー |
| `PRESERVE_DATA` | `true` | **重要**: データ保護モード有効化 |
| `PYTHONPATH` | `.` | Pythonパス設定 |

### 3. データ保護モードについて

#### PRESERVE_DATA=true の効果
- **既存データがある場合**: データベースの初期化をスキップ
- **データがない場合**: 最低限の初期化のみ実行
- **メリット**: デプロイ時のデータ消失を防止

#### 注意事項
- 初回デプロイ時は `PRESERVE_DATA=false` または未設定で開始
- データが蓄積された後に `PRESERVE_DATA=true` に変更
- 完全な初期化が必要な場合のみ `false` に戻す

### 4. デプロイ実行
1. 「Create Web Service」をクリック
2. ビルドプロセスを監視
3. デプロイ完了を確認

### 5. 初期セットアップ（初回のみ）
1. アプリケーションにアクセス
2. 管理者ユーザーの作成
3. 必要な初期データの投入

## トラブルシューティング

### ビルドエラーの場合
1. ビルドログを確認
2. `requirements.txt` の依存関係をチェック
3. `build.sh` の権限確認

### データベース関連エラー
1. SQLiteファイルの権限確認
2. `PRESERVE_DATA` 設定の確認
3. インスタンスディレクトリの存在確認

### 静的ファイルが表示されない場合
1. Renderの静的ファイル配信設定を確認
2. アプリケーション内での静的ファイルパスを確認

## 本番環境での注意事項

### セキュリティ
- 強力な `SECRET_KEY` の設定
- デバッグモードの無効化確認
- 環境変数の適切な管理

### パフォーマンス
- Gunicornワーカー数の調整
- データベースの定期バックアップ
- ログローテーションの設定

### モニタリング
- Renderのログ監視
- アプリケーションの応答時間確認
- エラー率の監視

## サポートファイル

### 作成されたファイル
- `build.sh`: ビルドスクリプト
- `wsgi.py`: WSGI エントリーポイント
- `gunicorn.conf.py`: Gunicorn設定
- `render.yaml`: 設定参考ファイル
- `RENDER_DEPLOY.md`: このファイル

### 更新されたファイル
- `requirements.txt`: gunicorn追加 