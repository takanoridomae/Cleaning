# Utilities Directory

このディレクトリには、アプリケーションの直接的な機能とは関係のない、開発・運用・メンテナンス用のスクリプトが含まれています。

## ファイル一覧

### データ確認・検証スクリプト
- `check_aircon_count.py` - エアコンデータの件数確認用スクリプト
- `check_work_items.py` - 作業項目データの確認用スクリプト

### データ移行・インポートスクリプト
- `import_aircon_to_render.py` - Renderへのエアコンデータインポート用スクリプト

### NAS写真移行スクリプト
- `migrate_render_photos_to_nas.py` - Render環境の既存写真をNASに移行（Render Shell上で実行）
- `generate_photo_urls.py` - Render上の写真URLリストを生成（Render Shell上で実行）
- `download_photos_from_render.py` - RenderからローカルPCに写真をダウンロード
- `test_nas_connection.py` - NAS接続テスト用スクリプト

### テスト・デバッグスクリプト
- `test_date_conversion.py` - 日付変換処理のテスト用スクリプト
- `test_order_details_fix.py` - 注文詳細修正のテスト用スクリプト

## 使用方法

各スクリプトは、プロジェクトルートから以下のように実行できます：

```bash
python scripts/utilities/[スクリプト名].py
```

## 注意事項

- これらのスクリプトは本番環境での使用前に、必ず開発環境でテストしてください
- データベースに変更を加えるスクリプトは、事前にバックアップを取得してから実行してください 