"""
スケジューラーサービス

APSchedulerを使用してバックグラウンドで定期的に通知チェックを実行
"""

import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz

from app.services.email_service import email_service


class SchedulerService:
    """スケジューラーサービス"""

    def __init__(self):
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.check_interval = int(os.getenv("NOTIFICATION_CHECK_INTERVAL", 60))  # 秒
        self.enabled = os.getenv("NOTIFICATION_ENABLED", "True").lower() == "true"
        self.jst = pytz.timezone("Asia/Tokyo")

    def init_scheduler(self):
        """スケジューラーを初期化"""
        if not self.enabled:
            self.logger.info("通知機能が無効のためスケジューラーを開始しません")
            return

        if self.scheduler is not None:
            self.logger.warning("スケジューラーは既に初期化されています")
            return

        try:
            # エクゼキューターの設定
            executors = {"default": ThreadPoolExecutor(max_workers=2)}

            # ジョブの設定
            job_defaults = {
                "coalesce": True,  # 同じジョブが複数実行待ちの場合は統合
                "max_instances": 1,  # 同時実行インスタンス数
                "misfire_grace_time": 30,  # ミスファイア時の猶予時間（秒）
            }

            # スケジューラー作成
            self.scheduler = BackgroundScheduler(
                executors=executors, job_defaults=job_defaults, timezone="Asia/Tokyo"
            )

            # 通知チェックジョブを追加
            self.scheduler.add_job(
                func=self._check_notifications_job,
                trigger=IntervalTrigger(seconds=self.check_interval),
                id="notification_check",
                name="スケジュール通知チェック",
                replace_existing=True,
            )

            self.logger.info(
                f"スケジューラーを初期化しました（チェック間隔: {self.check_interval}秒）"
            )

        except Exception as e:
            self.logger.error(f"スケジューラー初期化エラー: {e}")
            self.scheduler = None

    def start(self):
        """スケジューラーを開始"""
        if not self.enabled:
            self.logger.info("通知機能が無効のためスケジューラーを開始しません")
            return False

        if self.scheduler is None:
            self.init_scheduler()

        if self.scheduler is None:
            self.logger.error("スケジューラーが初期化されていません")
            return False

        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("スケジューラーを開始しました")
                return True
            else:
                self.logger.warning("スケジューラーは既に実行中です")
                return True

        except Exception as e:
            self.logger.error(f"スケジューラー開始エラー: {e}")
            return False

    def stop(self):
        """スケジューラーを停止"""
        if self.scheduler is not None and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=True)
                self.logger.info("スケジューラーを停止しました")
            except Exception as e:
                self.logger.error(f"スケジューラー停止エラー: {e}")

    def is_running(self) -> bool:
        """スケジューラーが実行中かチェック"""
        return self.scheduler is not None and self.scheduler.running

    def get_status(self) -> dict:
        """スケジューラーの状態を取得"""
        if self.scheduler is None:
            return {
                "status": "not_initialized",
                "running": False,
                "jobs": 0,
                "next_run": None,
            }

        jobs = self.scheduler.get_jobs()
        next_run = None

        if jobs:
            notification_job = self.scheduler.get_job("notification_check")
            if notification_job:
                next_run = (
                    notification_job.next_run_time.isoformat()
                    if notification_job.next_run_time
                    else None
                )

        return {
            "status": "running" if self.scheduler.running else "stopped",
            "running": self.scheduler.running,
            "jobs": len(jobs),
            "next_run": next_run,
            "check_interval": self.check_interval,
            "enabled": self.enabled,
        }

    def _check_notifications_job(self):
        """通知チェックジョブ（バックグラウンド実行）"""
        try:
            # アプリケーションコンテキストが必要な場合の対応
            from app import create_app

            app = create_app()
            with app.app_context():
                # メール設定チェック
                if not email_service.is_configured():
                    self.logger.debug("メール設定が不完全のため通知チェックをスキップ")
                    return

                # 通知チェック実行（日本時間）
                start_time = datetime.now(self.jst)
                sent_count = email_service.check_and_send_notifications()
                end_time = datetime.now(self.jst)

                processing_time = (end_time - start_time).total_seconds()

                if sent_count > 0:
                    self.logger.info(
                        f"通知チェック完了: {sent_count} 件送信 "
                        f"(処理時間: {processing_time:.2f}秒)"
                    )
                else:
                    self.logger.debug(
                        f"通知チェック完了: 送信対象なし "
                        f"(処理時間: {processing_time:.2f}秒)"
                    )

        except Exception as e:
            self.logger.error(f"通知チェックジョブエラー: {e}")

    def trigger_manual_check(self) -> dict:
        """手動で通知チェックを実行"""
        try:
            start_time = datetime.now(self.jst)
            sent_count = email_service.check_and_send_notifications()
            end_time = datetime.now(self.jst)

            processing_time = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "sent_count": sent_count,
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
            }

            self.logger.info(f"手動通知チェック完了: {sent_count} 件送信")
            return result

        except Exception as e:
            self.logger.error(f"手動通知チェックエラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(self.jst).isoformat(),
            }


# サービスインスタンス
scheduler_service = SchedulerService()
