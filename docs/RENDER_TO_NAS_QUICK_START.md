# Render写真のNAS移行 - クイックスタートガイド

## 🚀 最速で移行を完了する手順

このガイドは、Renderに保存されている写真を最速でNASに移行するための簡潔な手順です。

## ⚡ 方法の選択

### 方法A: Render Shell経由（理想的だが条件が厳しい）

**条件:**
- Render環境からTailscale VPNにアクセス可能
- NAS環境変数が設定済み

**所要時間:** 約10-20分

### 方法B: ローカルPC経由（推奨・確実）

**条件:**
- ローカルPCでTailscale VPNが利用可能
- ローカルPCにプロジェクトの環境がある

**所要時間:** 約30-60分（写真の量による）

---

## 📋 方法A: Render Shell経由（直接移行）

### 手順

1. **Render環境変数を設定**
   ```
   NAS_ENABLED=True
   NAS_WEBDAV_URL=http://100.69.218.15:5005
   NAS_USERNAME=Takanori
   NAS_PASSWORD=（パスワード）
   NAS_BASE_PATH=/home/eacon_keep_pict
   ```

2. **Render Shellに接続**
   - Renderダッシュボード > Shell

3. **移行スクリプトを実行**
   ```bash
   python scripts/utilities/migrate_render_photos_to_nas.py
   ```

4. **完了を確認**
   - ✅ が表示されれば成功
   - NAS上で写真を確認

### トラブルシューティング

❌ **「NASに接続できません」が表示された場合**
→ 方法B（ローカルPC経由）を使用してください

---

## 📋 方法B: ローカルPC経由（推奨）

### ステップ1: Render上で写真URLリストを生成

1. **Render環境変数を追加**
   ```
   RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
   ```
   （実際のRenderアプリURLに置き換え）

2. **Render Shellに接続**

3. **URLリスト生成スクリプトを実行**
   ```bash
   python scripts/utilities/generate_photo_urls.py
   ```

4. **URLリストをコピー**
   ```bash
   cat photo_urls.txt
   ```
   
   出力をすべてコピー

### ステップ2: ローカルPCで写真をダウンロード

1. **photo_urls.txt を作成**
   - コピーした内容をローカルPCに `photo_urls.txt` として保存

2. **ダウンロードスクリプトを実行**
   ```bash
   python scripts/utilities/download_photos_from_render.py photo_urls.txt
   ```

3. **ダウンロード完了を確認**
   - `downloads_from_render/before/` に施工前写真
   - `downloads_from_render/after/` に施工後写真

### ステップ3: ローカルからNASに移行

1. **写真をuploadsフォルダに移動**
   
   **Windows PowerShell:**
   ```powershell
   Copy-Item -Path downloads_from_render\before\* -Destination uploads\before\
   Copy-Item -Path downloads_from_render\after\* -Destination uploads\after\
   ```
   
   **Linux/Mac:**
   ```bash
   cp downloads_from_render/before/* uploads/before/
   cp downloads_from_render/after/* uploads/after/
   ```

2. **Tailscale VPNを起動**
   ```bash
   tailscale status
   ```

3. **NAS移行スクリプトを実行**
   ```bash
   python migrate_existing_photos_to_nas.py
   ```

4. **完了を確認**
   - ✅ が表示されれば成功
   - NAS上で写真を確認

---

## ✅ 移行完了後の確認

### 1. NAS上の写真確認

NAS管理画面で以下を確認:
- `/home/eacon_keep_pict/aircon_reports/before/`
- `/home/eacon_keep_pict/aircon_reports/after/`

### 2. アプリケーションでの動作確認

ローカル環境でアプリケーションを起動し、報告書詳細画面で写真が表示されることを確認。

### 3. Renderバックアップの確認

Render上の写真は削除されずに残っているため、バックアップとして保持されます。

---

## 🔧 よくある問題

### Q: Render Shellで「NASに接続できません」と表示される

**A:** Render環境からTailscale VPNにアクセスできないため、方法B（ローカルPC経由）を使用してください。

### Q: ダウンロードが途中で止まる

**A:** スクリプトを再実行してください。既にダウンロード済みの写真はスキップされます。

### Q: NAS移行時に「NASが利用できません」と表示される

**A:** 以下を確認してください:
1. Tailscale VPNが起動しているか
2. `.env` ファイルのNAS設定が正しいか
3. NAS WebDAVサービスが起動しているか

---

## 📞 さらに詳しい情報

- **詳細な手順:** `docs/RENDER_PHOTO_MIGRATION_GUIDE.md`
- **代替方法の詳細:** `docs/RENDER_TO_NAS_MIGRATION_ALTERNATIVE.md`
- **NASセットアップ:** `docs/NAS_SETUP_GUIDE.md`

---

**所要時間の目安:**
- 写真100枚の場合: 約30分
- 写真500枚の場合: 約1時間
- 写真1000枚以上の場合: 約2-3時間

**推奨環境:**
- 安定したインターネット接続
- Tailscale VPNが正常に動作していること
- 十分なディスク容量（ローカルPCとNAS）

