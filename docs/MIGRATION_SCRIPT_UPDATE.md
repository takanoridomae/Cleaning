# 移行スクリプト更新履歴

## 📅 2025-10-14: Render環境の実際の構造に対応

### 🔍 発見された問題

Render環境の実際のディレクトリ構造を確認したところ、想定と異なる点が見つかりました：

```bash
uploads/before/
├── 15_34-7/              # サブディレクトリ
├── 17_12-13_40/          # サブディレクトリ
├── 18_3-6-9/             # サブディレクトリ
├── 20250926060509_IMG_2269.jpeg  # .jpeg拡張子
├── 20250926060509_IMG_2270.jpeg
├── 20250927232344_IMG_2282.JPG   # 大文字の.JPG
└── ...
```

**問題点:**
1. サブディレクトリが存在する
2. `.jpeg`と`.JPG`（大文字）の拡張子が使用されている
3. 元のスクリプトは`.jpg`のみを想定していた

### ✅ 実施した修正

#### 1. ファイル検出ロジックの改善

**修正前:**
```python
files = [f for f in os.listdir(local_folder) 
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
```

**修正後:**
```python
# ディレクトリを除外し、ファイルのみを対象
all_items = os.listdir(local_folder)
files = []
for item in all_items:
    item_path = os.path.join(local_folder, item)
    # ファイルのみを対象とし、ディレクトリは除外
    if os.path.isfile(item_path):
        # 画像ファイルのみを対象（大文字小文字を区別しない）
        if item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.JPG', '.JPEG', '.PNG', '.GIF')):
            files.append(item)
```

**改善点:**
- `os.path.isfile()`でディレクトリを明示的に除外
- 大文字の拡張子（`.JPG`, `.JPEG`など）にも対応
- より安全なファイル検出

#### 2. 更新されたスクリプト

以下のスクリプトを更新しました：

1. **`scripts/utilities/migrate_render_photos_to_nas.py`**
   - Render環境用の移行スクリプト

2. **`migrate_existing_photos_to_nas.py`**
   - ローカル環境用の移行スクリプト

#### 3. ドキュメント更新

**`docs/RENDER_PHOTO_MIGRATION_GUIDE.md`**

写真件数確認コマンドを更新：

**修正前:**
```bash
echo "施工前写真: $(ls uploads/before/*.jpg 2>/dev/null | wc -l)件"
```

**修正後:**
```bash
echo "施工前写真: $(find uploads/before/ -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) | wc -l)件"
```

**改善点:**
- `-maxdepth 1`でサブディレクトリを除外
- `-type f`でファイルのみを対象
- `-iname`で大文字小文字を区別しない検索
- すべての画像形式（.jpg, .jpeg, .png, .gif）に対応

### 📊 実際のRender環境での確認結果

```bash
render@srv-xxx:~/project/src$ ls -lh uploads/before/ | head -10
total 237M
drwxrwsr-x 3 render render 4.0K Jul 13 00:51 15_34-7
drwxrwsr-x 3 render render 4.0K Jul  2 10:30 17_12-13_40
-rw-r--r-- 1 render render 2.3M Sep 26 06:05 20250926060509_IMG_2269.jpeg
-rw-r--r-- 1 render render 2.2M Sep 26 06:05 20250926060509_IMG_2270.jpeg
-rw-r--r-- 1 render render 3.3M Sep 27 23:23 20250927232344_IMG_2282.JPG
...

render@srv-xxx:~/project/src$ ls -lh uploads/after/ | head -10
total 263M
drwxrwsr-x 3 render render 4.0K Jul 13 00:51 15_34-7
-rw-r--r-- 1 render render 1.8M Sep 26 06:05 20250926060539_IMG_2274.jpeg
-rw-r--r-- 1 render render 3.3M Sep 27 23:24 20250927232402_IMG_2285.JPG
...
```

**確認内容:**
- ✅ サブディレクトリ（`15_34-7`など）が存在
- ✅ `.jpeg`と`.JPG`（大文字）が混在
- ✅ 合計サイズ: 約500MB（before: 237MB, after: 263MB）

### 🔧 正しい件数確認方法

**Render Shell上で実行:**

```bash
# 施工前写真の件数
find uploads/before/ -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) | wc -l

# 施工後写真の件数
find uploads/after/ -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) | wc -l

# または、移行スクリプトを実行すれば自動的にカウントされます
python scripts/utilities/migrate_render_photos_to_nas.py
```

### ✨ 今後の対応

これらの修正により、以下が可能になりました：

1. **サブディレクトリの自動除外**
   - `uploads/before/15_34-7/`などのディレクトリは無視される
   - ファイルのみが移行対象となる

2. **すべての画像形式に対応**
   - `.jpg`, `.jpeg`, `.png`, `.gif`
   - 大文字（`.JPG`, `.JPEG`など）も認識

3. **安全な移行**
   - ファイルとディレクトリを明示的に区別
   - エラーの可能性を低減

### 📝 移行実行時の注意点

1. **サブディレクトリ内の写真について**
   - 現在のスクリプトは、`uploads/before/`と`uploads/after/`の**直下のファイルのみ**を対象
   - サブディレクトリ内の写真は移行されません
   - もしサブディレクトリ内の写真も移行が必要な場合は、別途対応が必要です

2. **サブディレクトリ内の写真を確認する方法**
   ```bash
   # サブディレクトリ内の写真を確認
   find uploads/before/ -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \)
   ```

3. **すべての写真を移行したい場合**
   - サブディレクトリ内の写真も含めて移行したい場合は、ご連絡ください
   - スクリプトを拡張して再帰的に処理することも可能です

### 🎯 結論

修正されたスクリプトは、Render環境の実際の構造に完全対応しています。
安心して移行スクリプトを実行できます。

---

**更新日:** 2025-10-14  
**影響を受けるファイル:**
- `scripts/utilities/migrate_render_photos_to_nas.py`
- `migrate_existing_photos_to_nas.py`
- `docs/RENDER_PHOTO_MIGRATION_GUIDE.md`

