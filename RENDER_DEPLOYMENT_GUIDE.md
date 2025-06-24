# Render デプロイメントガイド

## データベース保護とデプロイ制御

### 問題
GitHubにプッシュするたびにRenderで自動デプロイが実行され、データベースが初期化されてしまう。

### 解決策

## 1. 自動デプロイの無効化（推奨）

### Renderダッシュボードでの設定

1. **Renderダッシュボードにアクセス**
   - [https://dashboard.render.com](https://dashboard.render.com)

2. **サービスを選択**
   - 該当のWebサービス（Cleaning）をクリック

3. **設定を変更**
   - **Settings** タブをクリック
   - **Build & Deploy** セクションを探す
   - **Auto-Deploy** を **"No"** に変更
   - **Save Changes** をクリック

### 手動デプロイの方法

自動デプロイを無効化した後、必要に応じて以下の方法で手動デプロイを実行：

1. **Renderダッシュボード**
   - サービスページで **"Manual Deploy"** ボタンをクリック
   - **"Deploy latest commit"** を選択

2. **データインポート後のデプロイ**
   - データインポートが完了してから手動デプロイを実行
   - データが保護された状態でアプリケーションが更新される

## 2. 環境変数による制御（デフォルトで安全）

### 新しい制御方式

**重要**: アプリケーションは**デフォルトでDB初期化をスキップ**するよう変更されました。

#### 通常運用（推奨）
- **何も設定しない** = DB初期化はスキップされる
- データが完全に保護される
- 手動デプロイでもDB初期化されない

#### 初期化が必要な場合のみ
1. **Renderダッシュボード**
   - **Environment** タブをクリック

2. **一時的に環境変数を追加**
   - **Key**: `FORCE_DB_INIT`
   - **Value**: `true`
   - **Add Environment Variable** をクリック

3. **デプロイ実行**
   - この状態でデプロイするとDB初期化が実行される

4. **環境変数を削除**
   - 初期化完了後、`FORCE_DB_INIT`を**必ず削除**
   - これにより再び安全な状態に戻る

## 3. データインポート手順

### 完全なデータ移行手順

1. **基本データのインポート**
   ```bash
   python scripts/db_tools/import_to_render.py simple_export_20250624_185754.json
   ```

2. **報告書データのインポート**
   ```bash
   python scripts/db_tools/import_reports.py reports_export_20250624_191211.json
   ```

3. **安全確認**
   - `FORCE_DB_INIT`環境変数が**設定されていない**ことを確認
   - これによりデプロイ時のDB初期化が防止される

4. **手動デプロイ実行**
   - Renderダッシュボードから手動デプロイを実行
   - DB初期化はスキップされ、既存データが保護される

## 4. データ確認

### インポート後の確認コマンド

```bash
python -c "
from app import create_app, db
from app.models.user import User
from app.models.customer import Customer
from app.models.property import Property
from app.models.air_conditioner import AirConditioner
from app.models.report import Report
app = create_app()
with app.app_context():
    print(f'ユーザー: {User.query.count()}件')
    print(f'顧客: {Customer.query.count()}件')
    print(f'物件: {Property.query.count()}件')
    print(f'エアコン: {AirConditioner.query.count()}件')
    print(f'報告書: {Report.query.count()}件')
"
```

### 期待される結果

```
ユーザー: 2件
顧客: 3件
物件: 51件
エアコン: 106件
報告書: 51件
```

## 5. トラブルシューティング

### データが消失した場合

1. **データ再インポート**
   - 上記の手順でデータを再インポート

2. **自動デプロイ無効化確認**
   - Renderの設定で自動デプロイが無効になっているか確認

3. **環境変数確認**
   - `FORCE_DB_INIT`環境変数が**削除されている**ことを確認
   - 設定されている場合は削除する

### バックアップ

- ローカルのエクスポートファイルを必ず保管
- 定期的にRender環境からデータをエクスポート（今後実装予定）

## 推奨ワークフロー

1. **ローカル開発**
   - コード変更とテスト

2. **GitHubプッシュ**
   - 自動デプロイは無効のため、データは保護される

3. **手動デプロイ**
   - 必要に応じてRenderで手動デプロイを実行

4. **データ確認**
   - アプリケーションが正常に動作することを確認

この手順により、データを保護しながら安全にアプリケーションを更新できます。 