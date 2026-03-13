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
    # PILがインストールされていない場合
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
        file: アップロードされたファイル
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
        current_app.logger.error(f"サムネイル作成エラー: {str(e)}")
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