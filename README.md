# エアコンクリーニング完了報告書システム

エアコンクリーニング作業の完了報告書を作成・管理するための社内Webシステムです。顧客情報、物件情報、報告書情報を一元管理し、報告書作成業務を効率化します。

## 機能

- **お客様管理:** お客様情報の登録、編集、削除、一覧表示
- **物件管理:** 物件情報の登録、編集、削除、一覧表示
- **報告書管理:** 報告書の新規作成、編集、削除、一覧表示
- **写真比較:** 施工前後の写真を比較表示する機能

## 技術スタック

- **フロントエンド:** HTML, CSS, JavaScript
- **バックエンド:** Python (Flaskフレームワーク)
- **データベース:** SQLite

## セットアップ手順

### 前提条件

- Python 3.8以上がインストールされていること

### インストール

1. リポジトリをクローン
   ```
   git clone <repository-url>
   cd eacon_report
   ```

2. 仮想環境を作成して有効化
   ```
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. 依存ライブラリのインストール
   ```
   pip install -r requirements.txt
   ```

4. データベースの初期化
   ```
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

5. アプリケーションの実行
   ```
   python run.py
   ```

6. ブラウザで以下のURLにアクセス
   ```
   http://localhost:5000
   ```

## プロジェクト構造

```
eacon_report/
├── app/                          # アプリケーションルート
│   ├── __init__.py               # アプリケーション初期化
│   ├── routes/                   # ルーティング
│   ├── controllers/              # コントローラ
│   ├── models/                   # データモデル
│   ├── services/                 # ビジネスロジック
│   ├── static/                   # 静的ファイル
│   ├── templates/                # HTMLテンプレート
│   └── utils/                    # ユーティリティ
├── instance/                     # インスタンス固有ファイル
│   └── aircon_report.db          # SQLiteデータベース
├── uploads/                      # アップロードファイル
├── migrations/                   # DB移行ファイル
├── tests/                        # テストファイル
│   ├── README.md                 # テスト実行ガイド
│   ├── test_schedule_integration.py
│   ├── test_report_schedule_sync.py
│   ├── test_sync_fix.py
│   └── test_report_delete_schedule_cancel.py
├── scripts/                      # データベース操作・開発支援スクリプト
│   ├── README.md                 # スクリプト使用ガイド
│   ├── migrations/               # マイグレーション関連
│   ├── backup/                   # バックアップ・復元関連
│   ├── db_tools/                 # データベース操作・修正
│   ├── development/              # 開発・テスト用スクリプト
│   └── utilities/                # ユーティリティスクリプト
├── docs/                         # ドキュメント
│   ├── README.md                 # ドキュメント一覧
│   ├── AIRCON_DATA_IMPORT_GUIDE.md
│   ├── ALL_DATA_IMPORT_GUIDE.md
│   ├── NOTIFICATION_SETUP.md
│   ├── RENDER_DEPLOY.md
│   ├── RENDER_EXECUTION_GUIDE.md
│   ├── RENDER_FILE_UPLOAD_GUIDE.md
│   ├── RENDER_SETUP_GUIDE.md
│   └── RENDER_SHELL_COMMANDS.md
├── db_backups/                   # データベースバックアップ
├── venv/                         # 仮想環境（gitignore対象）
├── .gitignore                    # Gitの除外設定
├── requirements.txt              # 依存ライブラリ
├── run.py                        # アプリケーション起動
└── README.md                     # プロジェクト説明
```

## 開発ガイドライン

- **ブランチ戦略:** GitFlowに準拠 (main, develop, feature/*, release/*, hotfix/*)
- **コミットメッセージ:** [種類]: メッセージ（例: feat: お客様登録フォームを追加）
- **コードスタイル:** PEP 8に準拠

## ライセンス

このプロジェクトは社内用システムであり、独自ライセンスに基づいて提供されています。

## データベースバックアップ機能

このシステムには、以下のデータベースバックアップ機能が実装されています：

### 自動バックアップ

1. **起動時バックアップ**  
   アプリケーション起動時に自動的にデータベースのバックアップを作成します。過去5回分のバックアップが保持されます。

2. **定期バックアップ**  
   毎日午前3時に自動的にデータベースのバックアップを作成します。過去30日分のバックアップが保持されます。

### 手動バックアップと復元

3. **手動バックアップ**  
   以下のコマンドで手動バックアップを作成できます：
   ```
   python scripts/backup/backup_db.py
   ```
   
   特定の場所にバックアップする場合：
   ```
   python scripts/backup/backup_db.py --output /path/to/backup/file.db
   ```

4. **バックアップからの復元**  
   以下のコマンドでバックアップから復元できます：
   ```
   python scripts/backup/restore_db.py --list
   ```
   
   特定のバックアップファイルから復元する場合：
   ```
   python scripts/backup/restore_db.py --backup /path/to/backup/file.db
   ```

すべてのバックアップは `db_backups` ディレクトリ内にタイプ別（startup、daily、manual、before_restore）に保存されます。

**注意**: データベース構造を変更する場合は、事前に必ずバックアップを作成してください。 # Cleaning
