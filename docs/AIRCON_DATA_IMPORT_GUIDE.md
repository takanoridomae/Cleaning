# エアコンデータ Renderインポートガイド

## 概要
ローカルデータベースのair_conditionersテーブル（114件）をRenderにデプロイされたデータベースにインポートする手順です。

## 準備されたファイル
- `aircon_export_20250628_210003.json` - エクスポートされたエアコンデータ（114件）
- `import_aircon_to_render.py` - Renderサーバー用インポートスクリプト

## データの概要
- **総件数**: 114件
- **メーカー別内訳**:
  - ダイキン: 35台
  - パナソニック: 21台
  - 東芝: 11台
  - シャープ: 9台
  - 日立: 9台
  - 富士通: 8台
  - ナショナル: 5台
  - 三菱: 4台
  - ミツビシ: 4台
  - 三菱重工: 2台
  - CORONA: 2台
  - その他: 4台

## インポート方法

### 方法1: Renderサーバー上で直接実行（推奨）

#### ステップ1: ファイルのアップロード
1. Renderダッシュボードにログイン
2. 対象のWebサービスを選択
3. 「Shell」タブを開く
4. 以下のファイルをサーバーにアップロード:
   ```
   aircon_export_20250628_210003.json
   import_aircon_to_render.py
   ```

#### ステップ2: Renderシェルでの実行
```bash
# Renderシェルで以下のコマンドを実行
python import_aircon_to_render.py
```

#### 期待される出力例:
```
既存のair_conditionersレコード数: 0
追加: ダイキン AS-C22K-W
追加: パナソニック CS-X280D
...
インポート完了:
  新規追加: 114件
  更新: 0件
  総処理件数: 114件

最終的なair_conditionersレコード数: 114
```

### 方法2: APIエンドポイント経由

#### 前提条件
- Renderアプリが稼働中であること
- APIエンドポイント `/air_conditioners/api/import` が利用可能であること

#### 実行方法
```bash
# ローカルから実行
python scripts/export_aircon_data.py --upload https://your-render-app.onrender.com
```

または、curlコマンドで直接送信:
```bash
curl -X POST https://your-render-app.onrender.com/air_conditioners/api/import \
  -H "Content-Type: application/json" \
  -d @aircon_export_20250628_210003.json
```

## 重要な注意事項

### データ保護について
- **PRESERVE_DATA=true**が設定されていることを確認 [[memory:4470672458899265998]]
- インポート前に既存データのバックアップを推奨
- 重複データは自動的に更新されます（property_id, manufacturer, model_numberで判定）

### インポート前の確認事項
1. **property_idの整合性**: 
   - ローカルとRenderのpropertiesテーブルのIDが一致しているか確認
   - 不一致の場合は事前にpropertyデータの同期が必要

2. **データベースの状態確認**:
   ```python
   # Renderシェルで実行
   python -c "
   from app import create_app, db
   from app.models.air_conditioner import AirConditioner
   app = create_app()
   with app.app_context():
       print(f'既存レコード数: {AirConditioner.query.count()}')
   "
   ```

### トラブルシューティング

#### エラー: "property_id is required"
- propertyデータが不足している可能性
- 先にpropertiesテーブルのデータをインポートしてください

#### エラー: "ModuleNotFoundError"
- Renderシェルで`export PYTHONPATH=.`を実行
- または`python -m app.import_script`で実行

#### エラー: "Database is locked"
- アプリケーションを一時停止してから実行
- または複数回に分けてインポート

## 検証方法

### インポート後の確認
```python
# Renderシェルで実行
python -c "
from app import create_app, db
from app.models.air_conditioner import AirConditioner
app = create_app()
with app.app_context():
    count = AirConditioner.query.count()
    print(f'総レコード数: {count}')
    
    # メーカー別集計
    from sqlalchemy import func
    manufacturers = db.session.query(
        AirConditioner.manufacturer, 
        func.count(AirConditioner.id)
    ).group_by(AirConditioner.manufacturer).all()
    
    print('メーカー別台数:')
    for manufacturer, count in manufacturers:
        print(f'  {manufacturer}: {count}台')
"
```

### Webアプリでの確認
1. Renderアプリにアクセス
2. 物件一覧から任意の物件を選択
3. エアコン情報が正しく表示されることを確認

## バックアップとロールバック

### 事前バックアップ（推奨）
```bash
# Renderシェルで実行
python scripts/backup/backup_db.py
```

### ロールバック方法
インポートに問題がある場合:
```python
# Renderシェルで実行
from app import create_app, db
from app.models.air_conditioner import AirConditioner
app = create_app()
with app.app_context():
    # インポートしたデータを削除（注意：慎重に実行）
    AirConditioner.query.delete()
    db.session.commit()
    print("air_conditionersテーブルをクリアしました")
```

## サポート情報

### 作成されたファイル
- `scripts/export_aircon_data.py` - エクスポート・インポートツール
- `aircon_export_20250628_210003.json` - エクスポートデータ
- `import_aircon_to_render.py` - Renderサーバー用インポートスクリプト
- `AIRCON_DATA_IMPORT_GUIDE.md` - この手順書

### 関連するコード変更
- `app/routes/air_conditioners.py` - APIエンドポイント追加

## 実行ログの例

```
=== エアコンデータ エクスポート・インポートツール ===

1. ローカルデータベースからエクスポート中...
エクスポート完了: 114件のデータを aircon_export_20250628_210003.json に保存しました
ファイルサイズ: 48596 bytes

=== データ概要 ===
最初のレコードID: 1
最後のレコードID: 116

メーカー別台数:
  ダイキン: 35台
  ナショナル: 5台
  シャープ: 9台
  パナ: 1台
  パナソニック: 21台
  三菱: 4台
  ミツビシ: 4台
  東芝: 11台
  日立: 9台
  富士通: 8台
  CORONA: 2台
  三菱重工: 2台
  ハイセンス: 1台
  長府: 1台
  サンヨー: 1台
```

---

**注意**: このインポート作業は本番データベースに影響を与えます。必ず事前にバックアップを取得し、テスト環境での動作確認を行ってから実行してください。 