"""
NAS WebDAV接続ユーティリティ

UGREEN NASへWebDAV経由で写真を保存・取得するためのユーティリティ関数
"""

import os
import io
import logging
from typing import Optional, Tuple
from flask import current_app
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


# グローバルクライアントインスタンス
_nas_client = None


def get_nas_client() -> NASWebDAVClient:
    """NAS WebDAVクライアントのシングルトンインスタンスを取得"""
    global _nas_client
    if _nas_client is None:
        _nas_client = NASWebDAVClient()
    return _nas_client

