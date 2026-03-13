# NAS写真保存ロジック 完全ガイド

このドキュメントは、UGREEN NASへの写真保存システムの完全な実装ロジックをまとめたものです。
他のシステムでの実装時のプロンプト資料として使用できます。

---

## 📋 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [環境変数設定](#環境変数設定)
4. [コア実装](#コア実装)
5. [使用例](#使用例)
6. [エラーハンドリング](#エラーハンドリング)
7. [セキュリティ](#セキュリティ)

---

## システム概要

### 保存戦略
3段階のハイブリッドストレージシステム：

1. **優先**: UGREEN NAS (Tailscale経由WebDAV、容量無制限)
2. **フォールバック**: ローカルストレージ (開発環境)
3. **本番環境**: NAS保存成功時はローカル保存をスキップ

### 主要機能

- ✅ WebDAV経由でのNAS自動保存
- ✅ 画像の自動圧縮 (最大700x500px, JPEG品質70%)
- ✅ NAS接続失敗時の自動フォールバック
- ✅ NASとローカルの両方からの画像取得
- ✅ 削除時の両ストレージ同期

---

## アーキテクチャ

### フォルダ構造

```
NAS: /home/eacon_keep_pict/
└── aircon_reports/
    ├── before/
    │   └── {uuid}_{timestamp}.jpg
    └── after/
        └── {uuid}_{timestamp}.jpg

ローカル: uploads/
├── before/
│   └── {uuid}_{timestamp}.jpg
├── after/
│   └── {uuid}_{timestamp}.jpg
└── thumbnails/
    └── thumb_{uuid}_{timestamp}.jpg
```

### 依存パッケージ

```txt
webdavclient3>=3.14.6  # WebDAVクライアント
Pillow>=10.0.0         # 画像処理
Flask>=2.3.0           # Webフレームワーク
```

---

## 環境変数設定

### .env ファイル

```bash
# NAS機能の有効化
NAS_ENABLED=True

# NAS WebDAV URL（TailscaleのIPアドレス:ポート）
NAS_WEBDAV_URL=http://100.69.218.15:5005

# NASログイン情報
NAS_USERNAME=Takanori
NAS_PASSWORD=your-password-here

# NAS保存先ベースパス
NAS_BASE_PATH=/home/eacon_keep_pict

# ローカルアップロードフォルダ
UPLOAD_FOLDER=uploads

# 本番環境フラグ（Render等）
RENDER=False
```

### 環境別の動作

| 環境 | NAS保存 | ローカル保存 |
|------|---------|--------------|
| 開発 (NAS有効) | ✅ | ✅ (常時) |
| 開発 (NAS無効) | ❌ | ✅ (常時) |
| 本番 (NAS成功) | ✅ | ❌ (スキップ) |
| 本番 (NAS失敗) | ❌ | ✅ (フォールバック) |

---

## コア実装

### 1. NAS WebDAVクライアント (`app/utils/nas_webdav.py`)

```python
"""
NAS WebDAV接続ユーティリティ

UGREEN NASへWebDAV経由で写真を保存・取得するためのユーティリティ関数
"""

import os
import io
import logging
from typing import Optional, Tuple
from webdav3.client import Client
from webdav3.exceptions import WebDavException

logger = logging.getLogger(__name__)


class NASWebDAVClient:
    """NAS WebDAVクライアント"""

    def __init__(self):
        """WebDAVクライアントの初期化"""
        self.enabled = os.environ.get('NAS_ENABLED', 'False').lower() == 'true'
        
        if not self.enabled:
            logger.info("NAS機能は無効です")
            return
            
        # NAS設定の取得
        self.webdav_url = os.environ.get('NAS_WEBDAV_URL', '')
        self.username = os.environ.get('NAS_USERNAME', '')
        self.password = os.environ.get('NAS_PASSWORD', '')
        self.base_path = os.environ.get('NAS_BASE_PATH', '/home/eacon_keep_pict')
        
        # WebDAVクライアントの設定
        self.options = {
            'webdav_hostname': self.webdav_url,
            'webdav_login': self.username,
            'webdav_password': self.password,
            'webdav_timeout': 30,
        }
        
        self.client = None
        if self._validate_config():
            try:
                self.client = Client(self.options)
                logger.info(f"NAS WebDAVクライアント初期化完了: {self.webdav_url}")
            except Exception as e:
                logger.error(f"NAS WebDAVクライアント初期化エラー: {e}")
                self.client = None

    def _validate_config(self) -> bool:
        """NAS設定の検証"""
        if not all([self.webdav_url, self.username, self.password]):
            logger.warning("NAS設定が不完全です。必要な環境変数: NAS_WEBDAV_URL, NAS_USERNAME, NAS_PASSWORD")
            return False
        return True

    def is_available(self) -> bool:
        """NASが利用可能かチェック"""
        if not self.enabled or not self.client:
            return False
        
        try:
            # ベースパスの存在確認
            return self.client.check(self.base_path)
        except WebDavException as e:
            logger.warning(f"NAS接続チェック失敗: {e}")
            return False
        except Exception as e:
            logger.error(f"NAS接続チェックエラー: {e}")
            return False

    def _ensure_directory(self, remote_path: str) -> bool:
        """ディレクトリが存在することを確認し、必要に応じて作成"""
        try:
            if not self.client.check(remote_path):
                logger.info(f"ディレクトリを作成: {remote_path}")
                self.client.mkdir(remote_path)
            return True
        except WebDavException as e:
            logger.error(f"ディレクトリ作成エラー: {remote_path} - {e}")
            return False

    def upload_file(self, file_data: bytes, remote_path: str) -> Tuple[bool, Optional[str]]:
        """
        ファイルをNASにアップロード
        
        Args:
            file_data: アップロードするファイルのバイナリデータ
            remote_path: NAS上のファイルパス（ベースパスからの相対パス）
            
        Returns:
            Tuple[成功フラグ, エラーメッセージ]
        """
        if not self.is_available():
            return False, "NASが利用できません"
        
        try:
            # フルパスの作成
            full_remote_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            
            # ディレクトリ部分を取得して作成
            directory = os.path.dirname(full_remote_path)
            if not self._ensure_directory(directory):
                return False, f"ディレクトリ作成失敗: {directory}"
            
            # ファイルアップロード
            logger.info(f"NASへアップロード開始: {full_remote_path}")
            
            # バイトデータからアップロード
            buffer = io.BytesIO(file_data)
            self.client.upload_to(buffer, full_remote_path)
            
            logger.info(f"NASアップロード完了: {full_remote_path}")
            return True, None
            
        except WebDavException as e:
            error_msg = f"WebDAVアップロードエラー: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"NASアップロードエラー: {e}"
            logger.error(error_msg)
            return False, error_msg

    def download_file(self, remote_path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        NASからファイルをダウンロード
        
        Args:
            remote_path: NAS上のファイルパス（ベースパスからの相対パス）
            
        Returns:
            Tuple[ファイルデータ, エラーメッセージ]
        """
        if not self.is_available():
            return None, "NASが利用できません"
        
        try:
            # フルパスの作成
            full_remote_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            
            # ファイルの存在確認
            if not self.client.check(full_remote_path):
                return None, f"ファイルが存在しません: {full_remote_path}"
            
            # ファイルダウンロード
            logger.info(f"NASからダウンロード: {full_remote_path}")
            buffer = io.BytesIO()
            self.client.download_from(buffer, full_remote_path)
            
            return buffer.getvalue(), None
            
        except WebDavException as e:
            error_msg = f"WebDAVダウンロードエラー: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"NASダウンロードエラー: {e}"
            logger.error(error_msg)
            return None, error_msg

    def delete_file(self, remote_path: str) -> Tuple[bool, Optional[str]]:
        """
        NASからファイルを削除
        
        Args:
            remote_path: NAS上のファイルパス（ベースパスからの相対パス）
            
        Returns:
            Tuple[成功フラグ, エラーメッセージ]
        """
        if not self.is_available():
            return False, "NASが利用できません"
        
        try:
            # フルパスの作成
            full_remote_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            
            # ファイルの存在確認
            if not self.client.check(full_remote_path):
                logger.warning(f"削除対象ファイルが存在しません: {full_remote_path}")
                return True, None  # 既に存在しないので成功とする
            
            # ファイル削除
            logger.info(f"NASから削除: {full_remote_path}")
            self.client.clean(full_remote_path)
            
            return True, None
            
        except WebDavException as e:
            error_msg = f"WebDAV削除エラー: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"NAS削除エラー: {e}"
            logger.error(error_msg)
            return False, error_msg

    def test_connection(self) -> Tuple[bool, str]:
        """
        NAS接続テスト
        
        Returns:
            Tuple[成功フラグ, メッセージ]
        """
        if not self.enabled:
            return False, "NAS機能が無効です"
        
        if not self.client:
            return False, "WebDAVクライアントが初期化されていません"
        
        if self.is_available():
            return True, f"NAS接続成功: {self.webdav_url}{self.base_path}"
        else:
            return False, f"NAS接続失敗: {self.webdav_url}{self.base_path}"


# グローバルクライアントインスタンス（シングルトンパターン）
_nas_client = None


def get_nas_client() -> NASWebDAVClient:
    """NAS WebDAVクライアントのシングルトンインスタンスを取得"""
    global _nas_client
    if _nas_client is None:
        _nas_client = NASWebDAVClient()
    return _nas_client
```

### 2. ファイルハンドラー (`app/utils/file_handler.py`)

```python
import os
import uuid
import io
import logging
from datetime import datetime
from typing import Tuple, Optional
from flask import current_app
from werkzeug.utils import secure_filename
try:
    from PIL import Image
except ImportError:
    Image = None
    print("WARNING: PIL is not installed. Thumbnail creation will be disabled.")

logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions=None):
    """アップロードされたファイルが許可された拡張子かチェック"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def compress_image(image_data: bytes, max_width: int = 700, max_height: int = 500, quality: int = 70) -> bytes:
    """
    画像を圧縮
    
    Args:
        image_data: 元画像のバイナリデータ
        max_width: 最大幅
        max_height: 最大高さ
        quality: JPEG品質 (0-100)
    
    Returns:
        圧縮された画像のバイナリデータ
    """
    try:
        if Image is None:
            logger.warning("PILが利用できないため、画像圧縮をスキップします")
            return image_data
        
        # 画像を開く
        img = Image.open(io.BytesIO(image_data))
        
        # RGBA画像の場合はRGBに変換
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # サイズ調整
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # JPEG形式で保存
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        compressed_data = output.getvalue()
        logger.info(f"画像圧縮: {len(image_data)} bytes → {len(compressed_data)} bytes "
                   f"({int((1 - len(compressed_data)/len(image_data)) * 100)}% 削減)")
        
        return compressed_data
        
    except Exception as e:
        logger.error(f"画像圧縮エラー: {e}")
        return image_data


def save_photo(file, photo_type):
    """
    写真ファイルを保存（NAS優先、フォールバック付き）
    
    Args:
        file: アップロードされたファイル（Werkzeug FileStorage）
        photo_type: 写真タイプ ('before' または 'after')
    
    Returns:
        ファイル名（保存成功時）または None（保存失敗時）
    """
    if file and allowed_file(file.filename):
        # 拡張子の取得
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        # 安全なファイル名の作成 (UUID + タイムスタンプ + 拡張子)
        timestamp = int(datetime.utcnow().timestamp())
        new_filename = f"{uuid.uuid4().hex}_{timestamp}.{ext}"
        
        # ファイルデータを読み込む
        file.seek(0)
        file_data = file.read()
        
        # 画像圧縮
        compressed_data = compress_image(file_data, max_width=700, max_height=500, quality=70)
        
        # NASへの保存を試行
        nas_saved = False
        try:
            from app.utils.nas_webdav import get_nas_client
            
            nas_client = get_nas_client()
            if nas_client.is_available():
                # NASパス: aircon_reports/{photo_type}/{filename}
                remote_path = f"aircon_reports/{photo_type}/{new_filename}"
                success, error = nas_client.upload_file(compressed_data, remote_path)
                
                if success:
                    logger.info(f"✅ NAS保存成功: {remote_path}")
                    nas_saved = True
                else:
                    logger.warning(f"⚠️ NAS保存失敗: {error}")
            else:
                logger.info("💾 NASが利用できないため、ローカルストレージに保存します")
        except Exception as e:
            logger.error(f"❌ NAS保存エラー: {e}")
        
        # ローカルストレージへの保存（NAS失敗時のフォールバックまたは併用）
        # Render環境では、NAS保存が成功した場合はローカル保存をスキップ
        is_render = os.environ.get('RENDER', 'False').lower() == 'true'
        
        if not is_render or not nas_saved:
            folder = 'before' if photo_type == 'before' else 'after'
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            
            # フォルダが存在しない場合は作成
            os.makedirs(upload_folder, exist_ok=True)
            
            # フルパスの作成
            file_path = os.path.join(upload_folder, new_filename)
            
            # ローカルに圧縮済み画像を保存
            try:
                with open(file_path, 'wb') as f:
                    f.write(compressed_data)
                logger.info(f"💾 ローカル保存成功: {file_path}")
                
                # サムネイル作成
                create_thumbnail(file_path, folder)
            except Exception as e:
                logger.error(f"❌ ローカル保存エラー: {e}")
                if not nas_saved:
                    return None
        else:
            logger.info(f"🚀 Render環境: NAS保存成功のためローカル保存スキップ")
        
        return new_filename
    
    return None


def create_thumbnail(file_path, folder, size=(150, 150)):
    """サムネイル画像を作成"""
    try:
        if Image is None:
            return None
            
        thumb_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumb_folder, exist_ok=True)
        
        # 元のファイル名からサムネイル名を作成
        filename = os.path.basename(file_path)
        thumb_filename = f"thumb_{filename}"
        thumb_path = os.path.join(thumb_folder, thumb_filename)
        
        # PILで画像を開いてリサイズ
        img = Image.open(file_path)
        img.thumbnail(size)
        img.save(thumb_path)
        
        return thumb_filename
    except Exception as e:
        logger.error(f"サムネイル作成エラー: {str(e)}")
        return None


def delete_photo(filename, photo_type):
    """
    写真ファイルとそのサムネイルを削除（NASとローカルの両方）
    
    Args:
        filename: ファイル名
        photo_type: 写真タイプ ('before' または 'after')
    
    Returns:
        成功フラグ
    """
    try:
        # NASから削除を試行
        try:
            from app.utils.nas_webdav import get_nas_client
            
            nas_client = get_nas_client()
            if nas_client.is_available():
                remote_path = f"aircon_reports/{photo_type}/{filename}"
                success, error = nas_client.delete_file(remote_path)
                if success:
                    logger.info(f"✅ NAS削除成功: {remote_path}")
                else:
                    logger.warning(f"⚠️ NAS削除失敗: {error}")
        except Exception as e:
            logger.error(f"❌ NAS削除エラー: {e}")
        
        # ローカルストレージから削除
        folder = 'before' if photo_type == 'before' else 'after'
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        
        # サムネイルパスの作成
        thumb_filename = f"thumb_{filename}"
        thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)
        
        # ファイルが存在する場合は削除
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"💾 ローカル削除成功: {file_path}")
        
        # サムネイルが存在する場合は削除
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        return True
    except Exception as e:
        logger.error(f"ファイル削除エラー: {str(e)}")
        return False


def get_photo_from_nas(filename: str, photo_type: str) -> Optional[bytes]:
    """
    NASから写真を取得
    
    Args:
        filename: ファイル名
        photo_type: 写真タイプ ('before' または 'after')
    
    Returns:
        画像データ（取得成功時）または None（取得失敗時）
    """
    try:
        from app.utils.nas_webdav import get_nas_client
        
        nas_client = get_nas_client()
        if not nas_client.is_available():
            logger.debug("NASが利用できません")
            return None
        
        remote_path = f"aircon_reports/{photo_type}/{filename}"
        file_data, error = nas_client.download_file(remote_path)
        
        if file_data:
            logger.info(f"✅ NASから取得成功: {remote_path}")
            return file_data
        else:
            logger.warning(f"⚠️ NASから取得失敗: {error}")
            return None
            
    except Exception as e:
        logger.error(f"❌ NAS取得エラー: {e}")
        return None
```

---

## 使用例

### 1. Flaskアプリケーションでの写真アップロード

```python
from flask import Flask, request, flash, redirect, url_for
from app.utils.file_handler import save_photo

@app.route('/upload', methods=['POST'])
def upload_photo():
    """写真アップロードエンドポイント"""
    
    # アップロードされた写真を取得
    before_photo = request.files.get('before_photo')
    after_photo = request.files.get('after_photo')
    
    # 写真を保存（NAS優先、自動フォールバック）
    before_filename = None
    after_filename = None
    
    if before_photo:
        before_filename = save_photo(before_photo, 'before')
        if before_filename:
            flash(f'施工前写真を保存しました: {before_filename}', 'success')
        else:
            flash('施工前写真の保存に失敗しました', 'error')
    
    if after_photo:
        after_filename = save_photo(after_photo, 'after')
        if after_filename:
            flash(f'施工後写真を保存しました: {after_filename}', 'success')
        else:
            flash('施工後写真の保存に失敗しました', 'error')
    
    # データベースにファイル名を保存
    # ...
    
    return redirect(url_for('reports.view', id=report_id))
```

### 2. 写真の配信

```python
from flask import send_file, abort
from app.utils.file_handler import get_photo_from_nas
import os

@app.route('/uploads/<photo_type>/<filename>')
def serve_photo(photo_type, filename):
    """写真配信エンドポイント（NASとローカルの両対応）"""
    
    # まずローカルストレージを確認
    folder = 'before' if photo_type == 'before' else 'after'
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    
    if os.path.exists(local_path):
        # ローカルにある場合は直接配信
        return send_file(local_path)
    
    # ローカルにない場合はNASから取得
    photo_data = get_photo_from_nas(filename, photo_type)
    
    if photo_data:
        # NASから取得した画像を配信
        return send_file(
            io.BytesIO(photo_data),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=filename
        )
    
    # どちらにもない場合は404
    abort(404)
```

### 3. 写真の削除

```python
from app.utils.file_handler import delete_photo

@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo_endpoint(photo_id):
    """写真削除エンドポイント"""
    
    # データベースから写真情報を取得
    photo = Photo.query.get_or_404(photo_id)
    
    # ファイルを削除（NASとローカルの両方）
    if delete_photo(photo.filename, photo.photo_type):
        # データベースから削除
        db.session.delete(photo)
        db.session.commit()
        flash('写真を削除しました', 'success')
    else:
        flash('写真の削除に失敗しました', 'error')
    
    return redirect(url_for('reports.view', id=photo.report_id))
```

### 4. 接続テスト

```python
from app.utils.nas_webdav import get_nas_client

def test_nas_connection():
    """NAS接続テスト"""
    nas_client = get_nas_client()
    success, message = nas_client.test_connection()
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
```

---

## エラーハンドリング

### ログメッセージ

システムは以下のログメッセージを出力します：

#### 成功時
```
✅ NAS保存成功: aircon_reports/before/abc123_1234567890.jpg
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

#### NAS利用不可時
```
💾 NASが利用できないため、ローカルストレージに保存します
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

#### エラー時
```
❌ NAS保存エラー: WebDAVアップロードエラー: 401 Unauthorized
💾 ローカル保存成功: uploads/before/abc123_1234567890.jpg
```

#### Render環境
```
🚀 Render環境: NAS保存成功のためローカル保存スキップ
```

### エラーハンドリングの実装パターン

```python
def robust_photo_save(file, photo_type):
    """堅牢な写真保存（エラー時も処理を継続）"""
    
    nas_saved = False
    local_saved = False
    errors = []
    
    # NAS保存を試行
    try:
        nas_client = get_nas_client()
        if nas_client.is_available():
            success, error = nas_client.upload_file(file_data, remote_path)
            if success:
                nas_saved = True
                logger.info("NAS保存成功")
            else:
                errors.append(f"NAS保存失敗: {error}")
    except Exception as e:
        errors.append(f"NAS保存例外: {e}")
    
    # ローカル保存を試行
    try:
        with open(local_path, 'wb') as f:
            f.write(file_data)
        local_saved = True
        logger.info("ローカル保存成功")
    except Exception as e:
        errors.append(f"ローカル保存例外: {e}")
    
    # 両方失敗した場合のみエラー
    if not nas_saved and not local_saved:
        logger.error(f"写真保存完全失敗: {errors}")
        return None
    
    return filename
```

---

## セキュリティ

### Tailscale VPN

- **暗号化**: すべての通信はTailscale VPNトンネル内で暗号化
- **Basic認証**: WebDAVのユーザー名/パスワードもVPNトンネル内で送信
- **アクセス制御**: Tailscaleネットワーク内のデバイスのみアクセス可能

### ベストプラクティス

1. **.env ファイルの管理**
   - 絶対にGitにコミットしない
   - `.gitignore`に`.env`を追加
   - 本番環境は環境変数で管理

2. **パスワードセキュリティ**
   - 強力なパスワードを使用
   - 定期的にパスワードを変更
   - パスワードを平文で保存しない

3. **ファイル名の安全性**
   ```python
   # UUIDとタイムスタンプで一意かつ安全なファイル名を生成
   new_filename = f"{uuid.uuid4().hex}_{timestamp}.{ext}"
   ```

4. **アクセス権限**
   - NASユーザーに必要最小限の権限のみ付与
   - Tailscaleのアクセス制御リスト(ACL)を適切に設定

5. **バックアップ**
   - NASのデータを定期的にバックアップ
   - バックアップの整合性を定期的に確認

---

## トラブルシューティング

### 問題: NAS接続エラー

**症状**: `NAS接続チェック失敗`

**対処法**:
1. Tailscale VPNが起動しているか確認
   ```bash
   tailscale status
   ```

2. NASのIPアドレスにpingが通るか確認
   ```bash
   ping 100.69.218.15
   ```

3. 環境変数が正しく設定されているか確認
   ```python
   import os
   print(os.environ.get('NAS_WEBDAV_URL'))
   print(os.environ.get('NAS_USERNAME'))
   ```

### 問題: 認証エラー

**症状**: `WebDAVアップロードエラー: 401 Unauthorized`

**対処法**:
1. ユーザー名とパスワードが正しいか確認
2. NASの管理画面でユーザーアカウントを確認
3. WebDAVサービスが有効になっているか確認

### 問題: ディレクトリ作成失敗

**症状**: `ディレクトリ作成エラー`

**対処法**:
1. NAS_BASE_PATHが存在するか確認
2. ユーザーに書き込み権限があるか確認
3. NASの容量が十分にあるか確認

### 問題: 画像圧縮エラー

**症状**: `画像圧縮エラー`

**対処法**:
1. Pillowパッケージがインストールされているか確認
   ```bash
   pip install Pillow>=10.0.0
   ```

2. 画像ファイルが破損していないか確認
3. サポートされている画像形式か確認（PNG, JPG, JPEG, GIF）

---

## パフォーマンス指標

### 画像圧縮

| 項目 | 値 |
|------|------|
| 元のサイズ | 2-5MB (スマートフォン撮影) |
| 圧縮後 | 100-500KB |
| 削減率 | 約80-90% |
| 品質 | JPEG 70% (実用上問題なし) |
| 最大解像度 | 700x500px |

### アップロード時間

| 接続 | 時間 |
|------|------|
| NAS (Tailscale経由) | 1-3秒/枚 |
| ローカルストレージ | 0.1-0.5秒/枚 |

### 画像取得時間

| ソース | 時間 |
|--------|------|
| ローカル | 0.01-0.05秒 |
| NAS | 0.5-2秒 |

---

## システム要件

### 必須

- Python 3.8以上
- Tailscale VPN（NAS接続時）
- UGREEN NAS（またはWebDAV対応NAS）

### 推奨

- 高速インターネット接続
- NASの定期バックアップ設定
- ログ監視システム

---

## まとめ

このNAS写真保存システムは以下の特徴を持ちます：

✅ **信頼性**: 3段階のフォールバック機構
✅ **効率性**: 自動画像圧縮で帯域と容量を節約
✅ **セキュリティ**: Tailscale VPNによる暗号化通信
✅ **柔軟性**: 環境に応じた動作モードの自動切り替え
✅ **保守性**: 詳細なログとエラーハンドリング

このドキュメントを参考に、他のシステムでも同様のNAS連携機能を実装できます。

