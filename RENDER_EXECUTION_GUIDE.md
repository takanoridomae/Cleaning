# 📋 Render上での写真移行実行ガイド

## 🎯 現在の状況
- ✅ 写真データが4つのチャンクに分割完了
- ✅ GitHubにプッシュ完了
- ✅ Persistent Disk設定準備完了

## 📦 プッシュされたファイル
```
photo_migration/
├── photo_migration_20250630_210456.part01 (90.0MB)
├── photo_migration_20250630_210456.part02 (90.0MB)  
├── photo_migration_20250630_210456.part03 (90.0MB)
├── photo_migration_20250630_210456.part04 (65.5MB)
├── merge_on_render.py (結合スクリプト)
├── extract_photos_on_render.py (展開スクリプト)
└── migration_metadata.json (メタデータ)
```

## 🚀 Render上での実行手順

### 1️⃣ Persistent Disk設定（最優先）

#### Renderダッシュボードで設定
1. **サービス選択**
   - https://dashboard.render.com/
   - エアコン報告書システムのWebサービスを選択

2. **Persistent Disk追加**
   - サイドメニュー「Disks」をクリック
   - 「Add Disk」ボタンをクリック
   
3. **設定値入力**
   ```
   Name: photo-storage
   Mount Path: /opt/render/project/src/uploads
   Size: 2 GB (推奨: 既存データ336MB + 成長分)
   ```

4. **保存と再デプロイ**
   - 「Add Disk」で保存
   - 自動的に再デプロイが開始されます

### 2️⃣ 最新コードのデプロイ確認

#### デプロイ状況の確認
1. **「Logs」タブで確認**
   ```
   ✅ Persistent Diskが検出されました: /opt/render/project/src/uploads
   📂 新規Persistent Diskです
   施工前写真: 0件
   施工後写真: 0件
   ```

2. **デプロイ完了まで待機**（通常2-5分）

### 3️⃣ Render Shellでの実行

#### Shell接続
1. **「Shell」タブをクリック**
2. **接続待機**（数秒）
3. **コマンドプロンプト表示確認**

#### 事前確認コマンド
```bash
# 現在の場所確認
pwd
# → /opt/render/project/src

# Persistent Disk確認
ls -la /opt/render/project/src/uploads
# → uploads ディレクトリの存在確認

# 分割ファイル確認
ls -la photo_migration/
# → part01〜part04ファイルの存在確認
```

#### 実行コマンド（順番に実行）

**ステップ1: ファイル結合**
```bash
cd photo_migration
python merge_on_render.py
```

**期待される出力:**
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
```

**ステップ2: 写真展開**
```bash
python extract_photos_on_render.py
```

**期待される出力:**
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

### 4️⃣ 動作確認

#### アプリケーションでの確認
1. **アプリケーションにアクセス**
   - Render URL（https://your-service.onrender.com）を開く

2. **既存報告書の確認**
   - 報告書一覧から任意の報告書を選択
   - 写真が正常に表示されることを確認

3. **新規写真アップロードテスト**
   - 新しい報告書を作成
   - 写真をアップロード
   - Persistent Diskに保存されることを確認

### 5️⃣ 再デプロイテスト

#### 永続性の確認
```bash
# アプリケーション動作を停止させずにテスト
# Renderダッシュボードで「Manual Deploy」実行
```

1. **Renderダッシュボード**
   - 「Manual Deploy」をクリック
   - デプロイ完了まで待機

2. **写真の確認**
   - デプロイ後にアプリケーションにアクセス
   - 写真が残っていることを確認

## 🔧 トラブルシューティング

### 問題1: Persistent Diskが見つからない
**エラー表示:**
```
❌ Persistent Diskが見つかりません
   Mount Path: /opt/render/project/src/uploads が設定されているか確認してください
```

**解決方法:**
1. Renderダッシュボードでディスク設定を再確認
2. Mount Pathが正確か確認: `/opt/render/project/src/uploads`
3. サービスの再デプロイを実行

### 問題2: 分割ファイルが見つからない
**エラー表示:**
```
❌ 分割ファイルが見つかりません
   photo_migration_*.part* ファイルを確認してください
```

**解決方法:**
```bash
# ファイル確認
ls -la photo_migration/photo_migration_*.part*

# Git pullが必要な場合
git pull origin feature/monthly-summary-updates
```

### 問題3: 権限エラー
**エラー表示:**
```
Permission denied
```

**解決方法:**
```bash
# 権限確認
ls -la /opt/render/project/src/uploads

# 権限修正
chmod -R 755 /opt/render/project/src/uploads
```

### 問題4: 容量不足
**エラー表示:**
```
No space left on device
```

**解決方法:**
1. Persistent Diskサイズを拡張（2GB推奨）
2. 一時ファイル削除: `rm /tmp/*`

## ⏱️ 実行時間の目安

| 処理 | 所要時間 | 説明 |
|------|----------|------|
| Persistent Disk設定 | 3-5分 | 再デプロイ含む |
| ファイル結合 | 30秒-1分 | 335MBファイルの結合 |
| 写真展開 | 1-2分 | ZIPファイルの展開 |
| **総所要時間** | **5-8分** | 全工程完了まで |

## ✅ 実行チェックリスト

### 事前準備
- [ ] Renderの有料プラン確認
- [ ] Persistent Disk設定完了
- [ ] 最新コードのデプロイ完了

### 実行工程
- [ ] Render Shell接続完了
- [ ] 事前確認コマンド実行
- [ ] ファイル結合完了（merge_on_render.py）
- [ ] 写真展開完了（extract_photos_on_render.py）

### 動作確認
- [ ] アプリケーション写真表示確認
- [ ] 新規写真アップロードテスト
- [ ] 再デプロイテスト完了

## 🎉 成功後の効果

✅ **177件の既存写真データが永続化**
✅ **再デプロイ後も写真データが保持**
✅ **自動バックアップ機能（日次スナップショット）**
✅ **高性能SSDによる高速アクセス**

## 📞 サポート

実行中に問題が発生した場合は、以下の情報をお教えください：

1. **エラーメッセージの全文**
2. **実行中のコマンド**
3. **Render Logsの内容**
4. **Persistent Disk設定の確認**

---

**重要:** この手順により、写真データが永続的に保護され、再デプロイ時の消失問題が解決されます！ 