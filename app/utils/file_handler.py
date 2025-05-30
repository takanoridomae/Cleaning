import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
try:
    from PIL import Image
except ImportError:
    # PILがインストールされていない場合
    Image = None
    print("WARNING: PIL is not installed. Thumbnail creation will be disabled.")

def allowed_file(filename, allowed_extensions=None):
    """アップロードされたファイルが許可された拡張子かチェック"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_photo(file, photo_type):
    """写真ファイルを保存し、ファイル名を返す"""
    if file and allowed_file(file.filename):
        # 拡張子の取得
        ext = file.filename.rsplit('.', 1)[1].lower()
        
        # 安全なファイル名の作成 (UUID + タイムスタンプ + 拡張子)
        new_filename = f"{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}.{ext}"
        
        # 保存先フォルダの決定
        folder = 'before' if photo_type == 'before' else 'after'
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        
        # フォルダが存在しない場合は作成
        os.makedirs(upload_folder, exist_ok=True)
        
        # フルパスの作成
        file_path = os.path.join(upload_folder, new_filename)
        
        # ファイルの保存
        file.save(file_path)
        
        # サムネイル作成
        create_thumbnail(file_path, folder)
        
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
    """写真ファイルとそのサムネイルを削除"""
    try:
        # 保存先フォルダの決定
        folder = 'before' if photo_type == 'before' else 'after'
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        
        # サムネイルパスの作成
        thumb_filename = f"thumb_{filename}"
        thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)
        
        # ファイルが存在する場合は削除
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # サムネイルが存在する場合は削除
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        return True
    except Exception as e:
        current_app.logger.error(f"ファイル削除エラー: {str(e)}")
        return False 