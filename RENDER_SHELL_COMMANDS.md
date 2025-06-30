# 🖥️ Render Shell 実行コマンド集

## 📋 事前確認コマンド

### 環境確認
```bash
# 現在の作業ディレクトリ確認
pwd
# 期待される出力: /opt/render/project/src

# Pythonバージョン確認
python --version
# 期待される出力: Python 3.x.x

# Persistent Disk確認
ls -la /opt/render/project/src/uploads
# 期待される出力: uploadsディレクトリの存在確認
```

### ファイル存在確認
```bash
# 分割ファイルの存在確認
ls -la photo_migration/photo_migration_*.part*
# 期待される出力:
# photo_migration_20250630_210456.part01
# photo_migration_20250630_210456.part02  
# photo_migration_20250630_210456.part03
# photo_migration_20250630_210456.part04

# スクリプトファイル確認
ls -la photo_migration/*.py
# 期待される出力:
# extract_photos_on_render.py
# merge_on_render.py
# split_for_github.py
```

## 🔧 実行コマンド

### ステップ1: ファイル結合
```bash
cd photo_migration
python merge_on_render.py
```

#### 期待される出力:
```
📦 ファイル結合情報:
   - 分割ファイル数: 4個
   - 出力ファイル: photo_migration_20250630_210456.zip
   📁 結合中: photo_migration_20250630_210456.part01
   📁 結合中: photo_migration_20250630_210456.part02
   📁 結合中: photo_migration_20250630_210456.part03
   📁 結合中: photo_migration_20250630_210456.part04

✅ ファイル結合完了:
   - 結合ファイル: photo_migration_20250630_210456.zip
   - 総サイズ: 335.45MB
🎉 ファイル結合が正常に完了しました！

次のステップ:
python extract_photos_on_render.py
```

#### 結合後の確認:
```bash
# 結合されたZIPファイルの確認
ls -la *.zip
# 期待される出力: photo_migration_20250630_210456.zip (約335MB)

# ファイルサイズの詳細確認
du -h photo_migration_20250630_210456.zip
# 期待される出力: 336M photo_migration_20250630_210456.zip
```

### ステップ2: 写真展開
```bash
python extract_photos_on_render.py
```

#### 期待される出力:
```
📦 移行ファイル: photo_migration_20250630_210456.zip
📊 移行データ情報:
   - 総ファイル数: 177件
   - 総サイズ: 335.45MB
   - 施工前: 90件
   - 施工後: 87件
📂 Persistent Diskに写真を展開中...
✅ 写真データの移行が完了しました:
   - 施工前写真: 90件
   - 施工後写真: 87件
   - 配置先: /opt/render/project/src/uploads
🎉 写真データの移行が正常に完了しました！
```

## 🔍 展開後の確認コマンド

### Persistent Disk内容確認
```bash
# Persistent Diskのディレクトリ構造確認
ls -la /opt/render/project/src/uploads/
# 期待される出力:
# drwxr-xr-x before/
# drwxr-xr-x after/
# drwxr-xr-x thumbnails/
# drwxr-xr-x PDF/

# 施工前写真の確認
find /opt/render/project/src/uploads/before -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l
# 期待される出力: 90

# 施工後写真の確認  
find /opt/render/project/src/uploads/after -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l
# 期待される出力: 87

# 総容量確認
du -sh /opt/render/project/src/uploads/
# 期待される出力: 約340M /opt/render/project/src/uploads/
```

### サンプル写真の確認
```bash
# beforeフォルダの内容サンプル
ls -la /opt/render/project/src/uploads/before/ | head -10
# 顧客フォルダの構造が表示される

# afterフォルダの内容サンプル  
ls -la /opt/render/project/src/uploads/after/ | head -10
# 顧客フォルダの構造が表示される
```

## ⚠️ エラーハンドリング

### エラー1: Persistent Diskが見つからない
```bash
# エラー表示例:
❌ Persistent Diskが見つかりません
   Mount Path: /opt/render/project/src/uploads が設定されているか確認してください

# 確認コマンド:
ls -la /opt/render/project/src/
mount | grep uploads
```

### エラー2: 分割ファイルが見つからない
```bash
# エラー表示例:
❌ 分割ファイルが見つかりません
   photo_migration_*.part* ファイルを確認してください

# 確認コマンド:
pwd
ls -la photo_migration/
git status
git pull origin feature/monthly-summary-updates
```

### エラー3: 権限エラー
```bash
# エラー表示例:
Permission denied

# 解決コマンド:
chmod -R 755 /opt/render/project/src/uploads/
whoami
ls -la /opt/render/project/src/uploads/
```

### エラー4: 容量不足
```bash
# エラー表示例:
No space left on device

# 確認コマンド:
df -h
du -sh /opt/render/project/src/uploads/
# Persistent Diskのサイズ拡張が必要
```

## 🧹 クリーンアップ（オプション）

### 一時ファイルの削除
```bash
# 移行完了後の不要ファイル削除
cd photo_migration

# 分割ファイルの削除
rm photo_migration_20250630_210456.part*

# 結合済みZIPファイルの削除
rm photo_migration_20250630_210456.zip

# 確認
ls -la
# 残るファイル: extract_photos_on_render.py, merge_on_render.py, migration_metadata.json, split_for_github.py
```

## ⏱️ 実行時間の目安

| 処理 | 時間 | 詳細 |
|------|------|------|
| ファイル結合 | 30秒-1分 | 4つのチャンクを結合 |
| 写真展開 | 1-2分 | ZIPから177ファイルを展開 |
| 権限設定 | 数秒 | 自動実行 |
| **合計** | **2-3分** | 全工程完了 |

## ✅ 成功確認のポイント

### 1. コマンド実行成功
- [ ] `merge_on_render.py` が正常終了
- [ ] `extract_photos_on_render.py` が正常終了
- [ ] エラーメッセージなし

### 2. ファイル数確認
- [ ] 施工前写真: 90件
- [ ] 施工後写真: 87件
- [ ] 総ファイル数: 177件

### 3. 容量確認
- [ ] 総容量: 約340MB
- [ ] Persistent Disk使用量確認

---

これらのコマンドを順番に実行することで、写真データの移行が完了します！ 

## 写真データ移行の実行手順（詳細版）

### ステップ1: 環境とファイルの確認

```bash
# 現在のディレクトリ確認
pwd
# 期待される出力: /opt/render/project/src

# Persistent Disk確認
ls -la /opt/render/project/src/uploads
# 期待される出力: Persistent Diskがマウントされている場合はディレクトリが存在

# 分割ファイルの確認
cd photo_migration
ls -la *.part*
# 期待される出力:
# photo_migration_20250630_210456.part01 (90MB)
# photo_migration_20250630_210456.part02 (90MB)  
# photo_migration_20250630_210456.part03 (90MB)
# photo_migration_20250630_210456.part04 (65.5MB)

# 分割ファイルサイズの確認
du -h *.part*
# 期待される出力:
# 90M photo_migration_20250630_210456.part01
# 90M photo_migration_20250630_210456.part02
# 90M photo_migration_20250630_210456.part03
# 66M photo_migration_20250630_210456.part04
```

### ステップ2: ファイル結合の実行

```bash
# 結合スクリプトの実行
python merge_on_render.py

# 期待される出力:
# 📦 ファイル結合情報:
#    - 分割ファイル数: 4個
#    - 出力ファイル: photo_migration_20250630_210456.zip
# 
#    📁 結合中: photo_migration_20250630_210456.part01
#    📁 結合中: photo_migration_20250630_210456.part02
#    📁 結合中: photo_migration_20250630_210456.part03
#    📁 結合中: photo_migration_20250630_210456.part04
# 
# ✅ ファイル結合完了:
#    - 結合ファイル: photo_migration_20250630_210456.zip
#    - 総サイズ: 336.51MB
# 
# 🗑️ 分割ファイルを削除しますか？ (y/N)
# 🎉 ファイル結合が正常に完了しました！
# 
# 次のステップ:
# python extract_photos_on_render.py

# 結合結果の確認
ls -la *.zip
# 期待される出力:
# photo_migration_20250630_210456.zip (約336MB)
```

### ステップ3: 写真データの展開

```bash
# 展開スクリプトの実行
python extract_photos_on_render.py

# 期待される出力:
# 📦 移行ファイル: photo_migration_20250630_210456.zip
# 📊 移行データ情報:
#    - 総ファイル数: 177件
#    - 総サイズ: 336.51MB
#    - 施工前: 90件
#    - 施工後: 87件
# 📂 Persistent Diskに写真を展開中...
# ✅ 写真データの移行が完了しました:
#    - 施工前写真: 90件
#    - 施工後写真: 87件
#    - 配置先: /opt/render/project/src/uploads
# 🎉 写真データの移行が正常に完了しました！
```

### ステップ4: 展開結果の確認

```bash
# Persistent Diskの写真ファイル確認
ls -la /opt/render/project/src/uploads/

# 期待される出力:
# drwxr-xr-x 2 render render 4096 date time before/
# drwxr-xr-x 2 render render 4096 date time after/
# -rw-r--r-- 1 render render xxxx date time migration_metadata.json

# 施工前写真の確認
find /opt/render/project/src/uploads/before -name "*.jpeg" -o -name "*.jpg" -o -name "*.png" | wc -l
# 期待される出力: 90

# 施工後写真の確認  
find /opt/render/project/src/uploads/after -name "*.jpeg" -o -name "*.jpg" -o -name "*.png" | wc -l
# 期待される出力: 87

# ディスク使用量確認
du -sh /opt/render/project/src/uploads/
# 期待される出力: 約340M /opt/render/project/src/uploads/

# 権限確認
ls -ld /opt/render/project/src/uploads/
# 期待される出力: drwxr-xr-x ... /opt/render/project/src/uploads/
```

### ステップ5: アプリケーション再起動（オプション）

```bash
# プロセス確認
ps aux | grep gunicorn

# 必要に応じてアプリケーション再起動
# (通常は自動的に再起動されます)
```

## トラブルシューティング

### 🚨 エラーパターンと対処法

#### 1. 分割ファイルが見つからない場合
```bash
❌ 分割ファイルが見つかりません
   photo_migration_*.part* ファイルを確認してください
```

**対処法:**
```bash
# ファイルの存在確認
ls -la photo_migration/
git status
git pull origin main  # 最新版を取得
```

#### 2. Persistent Diskが見つからない場合
```bash
❌ Persistent Diskが見つかりません
   Mount Path: /opt/render/project/src/uploads が設定されているか確認してください
```

**対処法:**
1. Renderダッシュボードでサービス設定を確認
2. "Storage" セクションで Persistent Disk が設定されているか確認
3. Mount Path が `/opt/render/project/src/uploads` に設定されているか確認

#### 3. 権限エラーが発生した場合
```bash
# 権限修正
chmod -R 755 /opt/render/project/src/uploads/
sudo chown -R render:render /opt/render/project/src/uploads/
```

#### 4. ディスク容量不足の場合
```bash
# ディスク使用量確認
df -h
# Persistent Diskの使用量確認
du -sh /opt/render/project/src/uploads/
```

### 📊 成功時の最終確認

移行が成功した場合、以下の状態になります：

- **ファイル構造:**
  ```
  /opt/render/project/src/uploads/
  ├── before/
  │   ├── [report_id]/
  │   │   ├── [model]/
  │   │   │   └── [date]/
  │   │   │       └── *.jpeg
  │   │   └── ...
  ├── after/
  │   ├── [report_id]/
  │   │   ├── [model]/
  │   │   │   └── [date]/
  │   │   │       └── *.jpeg
  │   │   └── ...
  └── migration_metadata.json
  ```

- **ファイル数:** 施工前90件 + 施工後87件 = 合計177件
- **総サイズ:** 約336.51MB
- **権限:** 755 (読み取り・実行可能)

### 🧹 クリーンアップ（移行完了後）

```bash
# 一時ファイルの削除（オプション）
cd photo_migration
rm -f *.part*  # 分割ファイル削除
rm -f *.zip    # ZIPファイル削除（バックアップとして残してもOK）

# Gitから一時ファイルを削除
cd ..
git rm photo_migration/*.part*
git commit -m "Remove temporary migration files after successful deployment"
git push origin main
```

## 📝 実行ログの保存

トラブルシューティングのため、実行ログを保存することをお勧めします：

```bash
# ログファイルに出力を保存
python merge_on_render.py 2>&1 | tee merge_log.txt
python extract_photos_on_render.py 2>&1 | tee extract_log.txt
```

## 📞 サポート

移行に問題が発生した場合は、以下の情報と共にサポートに連絡してください：

1. エラーメッセージの全文
2. 実行したコマンドとその出力
3. `ls -la photo_migration/` の結果
4. `df -h` の結果（ディスク容量）
5. Render サービス設定のスクリーンショット（Persistent Disk設定）

---

**注意:** 所要時間は約5-8分です。Renderのネットワーク状況により多少前後する場合があります。 