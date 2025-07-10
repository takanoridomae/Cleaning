# Renderへのファイルアップロード & Shell実行ガイド

## 🎯 目的
既存の写真データをRenderのPersistent Diskに移行するためのファイルアップロード手順

## 📁 対象ファイル
- `photo_migration_20250630_210456.zip` (336.51MB)
- `extract_photos_on_render.py` (展開スクリプト)

## 🚀 実行方法

### 方法1: SCP（推奨）- 最も確実

#### ステップ1: RenderでSSHセットアップ
1. **Renderダッシュボードにアクセス**
   - https://dashboard.render.com/
   - 対象のWebサービスを選択

2. **SSH設定の確認**
   - サイドメニュー「Settings」→「SSH Public Keys」
   - 公開鍵が登録されていない場合は追加が必要

3. **SSH接続情報の取得**
   - 「Shell」タブに移動
   - 上部に表示されるSSH接続コマンドをメモ
   ```bash
   ssh YOUR_SERVICE@ssh.YOUR_REGION.render.com
   ```

#### ステップ2: ローカルからSCPでアップロード
Windows PowerShellまたはWSLで実行：

```powershell
# 写真アーカイブのアップロード
scp -s "C:\new_prog\eacon_report\photo_migration\photo_migration_20250630_210456.zip" YOUR_SERVICE@ssh.YOUR_REGION.render.com:/tmp/

# 展開スクリプトのアップロード  
scp -s "C:\new_prog\eacon_report\photo_migration\extract_photos_on_render.py" YOUR_SERVICE@ssh.YOUR_REGION.render.com:/tmp/
```

**注意事項：**
- `YOUR_SERVICE`と`YOUR_REGION`は実際の値に置き換える
- `-s`フラグでSFTPプロトコルを使用（推奨）
- ファイルは`/tmp/`にアップロード

#### ステップ3: Render Shellで実行
1. **Renderダッシュボードの「Shell」タブを開く**

2. **アップロードしたファイルを確認**
   ```bash
   ls -la /tmp/photo_migration_*
   ls -la /tmp/extract_photos_on_render.py
   ```

3. **作業ディレクトリに移動してスクリプト実行**
   ```bash
   # ファイルを作業ディレクトリにコピー
   cp /tmp/photo_migration_*.zip .
   cp /tmp/extract_photos_on_render.py .
   
   # 実行権限を付与
   chmod +x extract_photos_on_render.py
   
   # スクリプト実行
   python extract_photos_on_render.py
   ```

### 方法2: Magic-Wormhole（簡単だが制限あり）

#### ステップ1: ローカルでWormhole送信
Windows PowerShellで：
```powershell
# Python環境でmagic-wormholeをインストール
pip install magic-wormhole

# ファイル送信
wormhole send "C:\new_prog\eacon_report\photo_migration\photo_migration_20250630_210456.zip"
```

#### ステップ2: Renderで受信
Render Shellで：
```bash
# Wormholeで受信（コードを入力）
wormhole receive

# スクリプトも同様に送信・受信
```

**制限事項：**
- 大きなファイル（336MB）の転送に時間がかかる
- 接続が不安定な場合は失敗する可能性

### 方法3: GitHub経由（開発用）

#### ステップ1: GitHubにファイル追加
```bash
# .gitignoreを一時的に変更してアップロード
git add photo_migration/
git commit -m "Add photo migration files"
git push origin main
```

#### ステップ2: Render側でPull
```bash
# Renderで最新コードを取得
git pull origin main
```

**注意事項：**
- 大きなファイルはGitHubの制限に注意（100MB制限）
- プライベートリポジトリ推奨
- 完了後はファイルを削除してhistoryをクリーンアップ

## 🔍 実行時の確認ポイント

### 事前確認
```bash
# Persistent Diskの存在確認
ls -la /opt/render/project/src/uploads

# 現在の権限確認
whoami
pwd
```

### 実行中の出力例
```
📦 移行ファイル: photo_migration_20250630_210456.zip
📊 移行データ情報:
   - 総ファイル数: 177件
   - 総サイズ: 336.51MB
   - 施工前: 90件
   - 施工後: 87件
📂 Persistent Diskに写真を展開中...
✅ 写真データの移行が完了しました:
   - 施工前写真: 90件
   - 施工後写真: 87件
   - 配置先: /opt/render/project/src/uploads
🎉 写真データの移行が正常に完了しました！
```

## ⚠️ トラブルシューティング

### 問題1: SCPでPermission Denied
**解決策：**
```bash
# SSH鍵の確認
ssh-add -l

# 鍵の再登録
ssh-add ~/.ssh/id_rsa
```

### 問題2: Persistent Diskが見つからない
**エラー：** "❌ Persistent Diskが見つかりません"

**解決策：**
1. Renderダッシュボードでディスク設定を確認
2. Mount Path: `/opt/render/project/src/uploads`
3. サービスの再デプロイを実行

### 問題3: 容量不足
**エラー：** "No space left on device"

**解決策：**
1. Persistent Diskのサイズを拡張（2GB推奨）
2. 一時ファイルの削除：`rm /tmp/*`

### 問題4: 権限エラー
**エラー：** "Permission denied"

**解決策：**
```bash
# ディレクトリ権限の修正
chmod -R 755 /opt/render/project/src/uploads

# ファイル所有者の確認
ls -la /opt/render/project/src/uploads
```

## 🎯 成功後の確認作業

### 1. 写真表示テスト
1. アプリケーションにアクセス
2. 既存の報告書を開く
3. 写真が正常に表示されることを確認

### 2. 新規写真アップロードテスト
1. 新しい写真をアップロード
2. Persistent Diskに保存されることを確認

### 3. 再デプロイテスト
1. Renderダッシュボードで「Manual Deploy」実行
2. デプロイ後も写真が残っていることを確認

## ⏱️ 実行時間の目安

| 処理 | 時間 | 説明 |
|------|------|------|
| SCPアップロード | 2-5分 | 336MBファイルの転送時間 |
| 写真展開処理 | 1-2分 | ZIPファイルの展開とファイル配置 |
| **総所要時間** | **5-10分** | 全工程完了まで |

## 📝 実行チェックリスト

- [ ] Persistent Disk設定完了（1GB以上）
- [ ] SSH接続設定完了
- [ ] SCPでzipファイルアップロード完了
- [ ] SCPでPythonスクリプトアップロード完了
- [ ] Render Shellでスクリプト実行完了
- [ ] 写真表示確認完了
- [ ] 再デプロイテスト完了

---

この方法で安全に既存の写真データをPersistent Diskに移行できます！ 