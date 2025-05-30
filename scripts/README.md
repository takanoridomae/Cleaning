# Scripts Directory

このディレクトリには、データベース操作、テスト、開発支援用のPythonスクリプトが整理されています。

## ディレクトリ構成

### `migrations/`
データベーススキーマの変更やマイグレーション関連のスクリプト
- `add_reception_fields.py` - 受付フィールド追加
- `add_filepath_column.py` - ファイルパスカラム追加
- `add_note_column.py` - ノートカラム追加
- `add_work_time_note.py` - 作業時間ノート追加
- `create_photo_relations.py` - 写真リレーション作成
- `create_schedule_table.py` - スケジュールテーブル作成
- `run_migration.py` - マイグレーション実行スクリプト

### `backup/`
データベースのバックアップと復元関連のスクリプト
- `backup_db.py` - データベースバックアップ
- `restore_db.py` - データベース復元

### `db_tools/`
データベースの確認、修正、メンテナンス用のスクリプト
- `check_db.py` - データベース確認
- `check_tables.py` - テーブル確認
- `clean_orphaned_photos.py` - 孤立写真クリーンアップ
- `fix_ac_data.py` - エアコンデータ修正
- `fix_database.py` - データベース修正
- `fix_db.py` - データベース修正
- `fix_property_id.py` - プロパティID修正
- `fix_work_time_table.py` - 作業時間テーブル修正
- `rebuild_aircon_data.py` - エアコンデータ再構築

### `development/`
開発・テスト用の一時的なスクリプト
- `check_schedules.py` - スケジュール確認
- `create_test_schedule.py` - テストスケジュール作成
- `create_test_schedules.py` - テストスケジュール複数作成
- `create_user.py` - ユーザー作成
- `direct_add_note.py` - ノート直接追加

## 使用方法

各スクリプトは個別に実行可能です：

```bash
# 例：データベースバックアップ
python scripts/backup/backup_db.py

# 例：マイグレーション実行
python scripts/migrations/run_migration.py

# 例：データベース確認
python scripts/db_tools/check_db.py
```

## 注意事項

- 本番環境での実行前には必ずバックアップを取ってください
- データベースファイルは `instance/aircon_report.db` です
- スクリプト実行前に依存関係を確認してください 