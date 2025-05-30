# Tests Directory

このディレクトリには、アプリケーションのテストファイルが含まれています。

## テストファイル一覧

### スケジュール関連テスト
- `test_schedule_integration.py` - スケジュール統合テスト
- `test_report_schedule_sync.py` - レポート・スケジュール同期テスト
- `test_sync_fix.py` - 同期修正テスト
- `test_report_delete_schedule_cancel.py` - レポート削除・スケジュールキャンセルテスト

## テスト実行方法

```bash
# 全テスト実行
python -m pytest tests/

# 特定のテストファイル実行
python -m pytest tests/test_schedule_integration.py

# より詳細な出力
python -m pytest tests/ -v
```

## 注意事項

- テスト実行前に必要な依存関係がインストールされていることを確認してください
- テスト用のデータベース設定が適切に行われていることを確認してください
- 本番データベースではなくテスト用データベースを使用してください 