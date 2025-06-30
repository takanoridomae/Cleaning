# Renderデプロイガイド

## 概要
このFlaskアプリケーションをRenderでデプロイするためのガイドです。

## 🚨 重要：写真データの永続化について

**問題：** Renderのエフェメラルファイルシステムにより、再デプロイ時に写真ファイルが削除されます。

**解決策：** 以下のいずれかを選択してください：

### オプション1: Persistent Disk（推奨）
- **必要なプラン：** Starter以上（$7/月〜）
- **コスト：** ディスク容量に応じて追加料金
- **設定：** 
  1. 有料プランにアップグレード
  2. Disksページでディスク追加
  3. マウントパス：`/opt/render/project/src/uploads`
  4. サイズ：1GB以上

### オプション2: AWS S3
- **コスト：** 使用量に応じて従量課金
- **設定：** 環境変数でAWS認証情報を設定
- **メリット：** CDN配信、高可用性

### オプション3: 無料プランでの制限事項
- 写真データは一時的（再デプロイで消失）
- デモンストレーション用途のみ推奨

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
- **Build Command**: `./build.sh` (推奨) または `pip install -r requirements.txt` (シンプル)
- **Start Command**: `gunicorn --config gunicorn.conf.py wsgi:app`

#### 環境変数設定
以下の環境変数を「Environment」タブで設定してください：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `FLASK_ENV` | `production` | Flask環境設定 |
| `SECRET_KEY` | (自動生成) | セッション暗号化キー |
| `PRESERVE_DATA` | `true` | **重要**: データ保護モード有効化 |
| `PYTHONPATH` | `.` | Pythonパス設定 |

#### 📁 写真データ用環境変数（オプション）

**AWS S3を使用する場合：**
| 変数名 | 値例 | 説明 |
|--------|-----|------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | AWS アクセスキー |
| `AWS_SECRET_ACCESS_KEY` | `abc123...` | AWS シークレットキー |
| `AWS_REGION` | `ap-northeast-1` | AWSリージョン |
| `AWS_S3_BUCKET_NAME` | `aircon-photos` | S3バケット名 |

#### 🔑 管理者アカウント設定（重要）

**方法A: 自動作成（推奨）**
以下の環境変数を追加設定：

| 変数名 | 値例 | 説明 |
|--------|-----|------|
| `CREATE_DEFAULT_ADMIN` | `true` | 自動管理者作成を有効 |
| `ADMIN_USERNAME` | `dotaka565` | 管理者ユーザー名 |
| `ADMIN_PASSWORD` | `your-secure-password` | 管理者パスワード |
| `ADMIN_EMAIL` | `dotaka565@yahoo.co.jp` | 管理者メール |
| `ADMIN_NAME` | `管理者` | 管理者表示名 |

**方法B: Web初回セットアップ**
- 環境変数を設定しない場合
- デプロイ後に `/auth/setup-admin` でアカウント作成

#### ⚠️ データベース初期化時の注意

- **初回デプロイ**: データベースは空の状態
- **再デプロイ**: `PRESERVE_DATA=true`で既存データ保護
- **完全リセット**: `PRESERVE_DATA=false`で初期化（データ消失）

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

#### Build Commandの選択肢

**推奨: `./build.sh`**
- データベースの自動初期化
- [データ保護モード対応][[memory:4470672458899265998]]
- ディレクトリの自動作成
- エラーハンドリング

**シンプル: `pip install -r requirements.txt`**
- 依存関係のインストールのみ
- 手動でのデータベース初期化が必要
- 初回デプロイ後に手動セットアップが必要 

## 推奨手順

1. **デプロイを完了させる**
2. **方法1を使用**: `https://your-app-name.onrender.com/auth/setup-admin` にアクセス
3. **管理者アカウントを作成**
4. **ログインして動作確認**

この方法が最も安全で確実です。どちらの方法を使用されますか？ 