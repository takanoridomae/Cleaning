"""
NAS WebDAV接続ユーティリティ

UGREEN NASへWebDAV経由で写真を保存・取得するためのユーティリティ関数
"""

import os
import io
import time
import logging
import socket
from urllib.parse import urlparse
from typing import Optional, Tuple
from flask import current_app
from webdav3.client import Client
from webdav3.exceptions import WebDavException

logger = logging.getLogger(__name__)

# 接続チェックのキャッシュ設定
_AVAILABILITY_CACHE_TTL_SUCCESS = 60    # 成功時: 60秒キャッシュ
_AVAILABILITY_CACHE_TTL_FAILURE = 15    # 失敗時: 15秒キャッシュ（すぐに再試行しない）
_SOCKET_CONNECT_TIMEOUT = 3            # ソケットレベル接続チェック: 3秒


class NASWebDAVClient:
    """NAS WebDAVクライアント"""

    def __init__(self):
        """WebDAVクライアントの初期化"""
        self.enabled = os.environ.get('NAS_ENABLED', 'False').lower() == 'true'
        self._availability_cache = None       # True/False/None
        self._availability_cache_time = 0     # キャッシュ更新時刻
        self._known_directories = set()       # 作成済みディレクトリのキャッシュ
        
        if not self.enabled:
            logger.info("NAS機能は無効です")
            return
            
        # NAS設定の取得
        self.webdav_url = os.environ.get('NAS_WEBDAV_URL', '')
        self.username = os.environ.get('NAS_USERNAME', '')
        self.password = os.environ.get('NAS_PASSWORD', '')
        self.base_path = os.environ.get('NAS_BASE_PATH', '/home/eacon_keep_pict')
        
        # WebDAVクライアントの設定（タイムアウト短縮: 30→10秒）
        self.options = {
            'webdav_hostname': self.webdav_url,
            'webdav_login': self.username,
            'webdav_password': self.password,
            'webdav_timeout': 10,
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

    def _quick_socket_check(self) -> bool:
        """ソケットレベルでNASへの接続を素早くチェック（3秒タイムアウト）"""
        try:
            parsed = urlparse(self.webdav_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_SOCKET_CONNECT_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"ソケット接続チェック失敗: {e}")
            return False

    def is_available(self) -> bool:
        """NASが利用可能かチェック（キャッシュ付き）"""
        if not self.enabled or not self.client:
            return False
        
        # キャッシュチェック
        now = time.time()
        if self._availability_cache is not None:
            ttl = _AVAILABILITY_CACHE_TTL_SUCCESS if self._availability_cache else _AVAILABILITY_CACHE_TTL_FAILURE
            if now - self._availability_cache_time < ttl:
                if not self._availability_cache:
                    logger.debug("NAS接続: キャッシュにより不可（前回失敗から15秒以内）")
                return self._availability_cache
        
        # まずソケットレベルで素早くチェック（3秒）
        if not self._quick_socket_check():
            logger.warning(f"NAS接続チェック失敗: {self.webdav_url} に到達できません")
            self._availability_cache = False
            self._availability_cache_time = now
            return False
        
        try:
            # WebDAVレベルでベースパスの存在確認
            result = self.client.check(self.base_path)
            self._availability_cache = result
            self._availability_cache_time = now
            if result:
                logger.debug("NAS接続チェック成功（キャッシュ更新）")
            return result
        except WebDavException as e:
            logger.warning(f"NAS接続チェック失敗: {e}")
            self._availability_cache = False
            self._availability_cache_time = now
            return False
        except Exception as e:
            logger.error(f"NAS接続チェックエラー: {e}")
            self._availability_cache = False
            self._availability_cache_time = now
            return False

    def _invalidate_cache(self):
        """接続キャッシュを無効化"""
        self._availability_cache = None
        self._availability_cache_time = 0
        self._known_directories.clear()

    def _ensure_directory(self, remote_path: str) -> bool:
        """ディレクトリが存在することを確認し、必要に応じて作成（キャッシュ付き）"""
        # 既に確認済みのディレクトリはスキップ
        if remote_path in self._known_directories:
            return True
        
        try:
            if not self.client.check(remote_path):
                logger.info(f"ディレクトリを作成: {remote_path}")
                self.client.mkdir(remote_path)
            self._known_directories.add(remote_path)
            return True
        except WebDavException as e:
            logger.error(f"ディレクトリ作成エラー: {remote_path} - {e}")
            return False

    def upload_file(self, file_data: bytes, remote_path: str, skip_availability_check: bool = False) -> Tuple[bool, Optional[str]]:
        """
        ファイルをNASにアップロード
        
        Args:
            file_data: アップロードするファイルのバイナリデータ
            remote_path: NAS上のファイルパス（ベースパスからの相対パス）
            skip_availability_check: Trueの場合、is_available()チェックをスキップ（呼び出し元で既にチェック済みの場合）
            
        Returns:
            Tuple[成功フラグ, エラーメッセージ]
        """
        if not skip_availability_check and not self.is_available():
            return False, "NASが利用できません"
        
        try:
            # フルパスの作成
            full_remote_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            
            # ディレクトリ部分を取得して作成（キャッシュ付き）
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
            self._invalidate_cache()
            return False, error_msg
        except Exception as e:
            error_msg = f"NASアップロードエラー: {e}"
            logger.error(error_msg)
            self._invalidate_cache()
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
            self._invalidate_cache()
            return None, error_msg
        except Exception as e:
            error_msg = f"NASダウンロードエラー: {e}"
            logger.error(error_msg)
            self._invalidate_cache()
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
            self._invalidate_cache()
            return False, error_msg
        except Exception as e:
            error_msg = f"NAS削除エラー: {e}"
            logger.error(error_msg)
            self._invalidate_cache()
            return False, error_msg

    def test_connection(self) -> Tuple[bool, str]:
        """
        NAS接続テスト（キャッシュをクリアして再チェック）
        
        Returns:
            Tuple[成功フラグ, メッセージ]
        """
        if not self.enabled:
            return False, "NAS機能が無効です"
        
        if not self.client:
            return False, "WebDAVクライアントが初期化されていません"
        
        # テスト時はキャッシュをクリア
        self._invalidate_cache()
        
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


def reset_nas_client():
    """NASクライアントをリセット（設定変更後に使用）"""
    global _nas_client
    _nas_client = None

