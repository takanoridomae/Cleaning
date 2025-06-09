"""
Email通知サービス

Gmailを使用してスケジュール通知メールを送信するサービス
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app import db
from app.models.schedule import Schedule
from app.models.user import User


class EmailService:
    """メール送信サービス"""

    def __init__(self):
        self.smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("MAIL_PORT", 587))
        self.use_tls = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
        self.username = os.getenv("MAIL_USERNAME")
        self.password = os.getenv("MAIL_PASSWORD")
        self.default_sender = os.getenv("MAIL_DEFAULT_SENDER")
        self.enabled = os.getenv("NOTIFICATION_ENABLED", "True").lower() == "true"

        # ログ設定
        self.logger = logging.getLogger(__name__)

    def is_configured(self) -> bool:
        """メール設定が正しく行われているかチェック"""
        return all([self.username, self.password, self.default_sender, self.enabled])

    def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        メール送信

        Args:
            to_addresses: 送信先メールアドレスリスト
            subject: 件名
            html_body: HTML本文
            text_body: テキスト本文（オプション）

        Returns:
            bool: 送信成功の場合True
        """
        if not self.is_configured():
            self.logger.error("メール設定が不完全です")
            return False

        if not to_addresses:
            self.logger.warning("送信先アドレスが指定されていません")
            return False

        try:
            # メッセージ作成
            message = MIMEMultipart("alternative")
            message["From"] = self.default_sender
            message["To"] = ", ".join(to_addresses)
            message["Subject"] = subject

            # テキスト部分
            if text_body:
                text_part = MIMEText(text_body, "plain", "utf-8")
                message.attach(text_part)

            # HTML部分
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)

            # SMTP接続とメール送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(message)

            self.logger.info(f"メール送信成功: {', '.join(to_addresses)}")
            return True

        except Exception as e:
            self.logger.error(f"メール送信エラー: {e}")
            return False

    def send_schedule_notification(
        self, schedule: Schedule, notification_type: str = "reminder"
    ) -> bool:
        """
        スケジュール通知メール送信

        Args:
            schedule: スケジュールオブジェクト
            notification_type: 通知タイプ（reminder, start, complete）

        Returns:
            bool: 送信成功の場合True
        """
        try:
            # 送信先メールアドレスを取得
            to_addresses = self._get_notification_recipients(schedule)
            if not to_addresses:
                self.logger.warning(
                    f"スケジュール {schedule.id} の送信先が見つかりません"
                )
                return False

            # メール内容生成
            subject, html_body, text_body = self._generate_notification_content(
                schedule, notification_type
            )

            # メール送信
            return self.send_email(to_addresses, subject, html_body, text_body)

        except Exception as e:
            self.logger.error(f"スケジュール通知エラー: {e}")
            return False

    def _get_notification_recipients(self, schedule: Schedule) -> List[str]:
        """
        通知送信先メールアドレスリストを取得

        Args:
            schedule: スケジュールオブジェクト

        Returns:
            List[str]: メールアドレスリスト
        """
        recipients = []

        try:
            # スケジュール作成者
            if schedule.creator and schedule.creator.email:
                recipients.append(schedule.creator.email)

            # 関連する顧客のメールアドレス
            if schedule.customer and schedule.customer.email:
                recipients.append(schedule.customer.email)

            # 重複削除
            recipients = list(set(recipients))

            # 有効なメールアドレスのみフィルタ
            valid_recipients = [email for email in recipients if "@" in email]

            return valid_recipients

        except Exception as e:
            self.logger.error(f"受信者取得エラー: {e}")
            return []

    def _generate_notification_content(
        self, schedule: Schedule, notification_type: str
    ) -> tuple:
        """
        通知メール内容生成

        Args:
            schedule: スケジュールオブジェクト
            notification_type: 通知タイプ

        Returns:
            tuple: (件名, HTML本文, テキスト本文)
        """
        # 基本情報
        title = schedule.title
        start_time = schedule.start_datetime.strftime("%Y年%m月%d日 %H:%M")
        end_time = schedule.end_datetime.strftime("%Y年%m月%d日 %H:%M")

        # 顧客・物件情報
        customer_info = ""
        if schedule.customer:
            customer_info = f"お客様: {schedule.customer.name}"
            if schedule.schedule_property:
                customer_info += f"\n物件: {schedule.schedule_property.name}"

        # 通知タイプ別の件名とメッセージ
        if notification_type == "reminder":
            subject = f"【リマインダー】{title} - {start_time}"
            message_title = "スケジュールリマインダー"
            message_body = f"以下のスケジュールが {schedule.notification_minutes} 分後に開始予定です。"
        elif notification_type == "start":
            subject = f"【開始通知】{title} - {start_time}"
            message_title = "スケジュール開始通知"
            message_body = "以下のスケジュールが開始時刻になりました。"
        elif notification_type == "complete":
            subject = f"【完了通知】{title} - 完了"
            message_title = "スケジュール完了通知"
            message_body = "以下のスケジュールが完了しました。"
        else:
            subject = f"【通知】{title}"
            message_title = "スケジュール通知"
            message_body = "スケジュールの通知です。"

        # HTML本文
        description_html = (
            f"<p><strong>説明:</strong> {schedule.description}</p>"
            if schedule.description
            else ""
        )
        customer_html = f"<p>{customer_info}</p>" if customer_info else ""

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; }}
                .schedule-info {{ background: white; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{message_title}</h1>
                </div>
                <div class="content">
                    <p>{message_body}</p>
                    <div class="schedule-info">
                        <h3>{title}</h3>
                        <p><strong>開始:</strong> {start_time}</p>
                        <p><strong>終了:</strong> {end_time}</p>
                        {description_html}
                        {customer_html}
                    </div>
                </div>
                <div class="footer">
                    <p>エアコンクリーニング完了報告書システム</p>
                    <p>このメールは自動送信されています。</p>
                </div>
            </div>
        </body>
        </html>
        """

        # テキスト本文
        text_body = f"""
{message_title}

{message_body}

スケジュール詳細:
- タイトル: {title}
- 開始: {start_time}
- 終了: {end_time}
{f"- 説明: {schedule.description}" if schedule.description else ""}
{f"- {customer_info}" if customer_info else ""}

---
エアコンクリーニング完了報告書システム
このメールは自動送信されています。
        """

        return subject, html_body, text_body

    def check_and_send_notifications(self) -> int:
        """
        通知が必要なスケジュールをチェックして通知送信

        Returns:
            int: 送信した通知数
        """
        if not self.is_configured():
            self.logger.warning("メール設定が不完全のため通知をスキップ")
            return 0

        sent_count = 0
        now = datetime.now()

        try:
            # 通知が有効なスケジュールを取得
            schedules = Schedule.query.filter(
                Schedule.notification_enabled == True, Schedule.status == "pending"
            ).all()

            for schedule in schedules:
                try:
                    # 通知タイミングの計算
                    notification_time = schedule.start_datetime - timedelta(
                        minutes=schedule.notification_minutes
                    )

                    # 通知時刻到来チェック（1分の誤差を許容）
                    time_diff = abs((now - notification_time).total_seconds())

                    if time_diff <= 60:  # 1分以内
                        if self.send_schedule_notification(schedule, "reminder"):
                            sent_count += 1
                            self.logger.info(
                                f"通知送信完了: スケジュール {schedule.id}"
                            )

                    # 開始時刻通知（開始時刻から5分以内）
                    start_time_diff = abs(
                        (now - schedule.start_datetime).total_seconds()
                    )
                    if start_time_diff <= 300:  # 5分以内
                        if self.send_schedule_notification(schedule, "start"):
                            sent_count += 1
                            self.logger.info(
                                f"開始通知送信完了: スケジュール {schedule.id}"
                            )

                except Exception as e:
                    self.logger.error(
                        f"スケジュール {schedule.id} の通知処理エラー: {e}"
                    )
                    continue

            if sent_count > 0:
                self.logger.info(f"通知送信完了: {sent_count} 件")

            return sent_count

        except Exception as e:
            self.logger.error(f"通知チェック処理エラー: {e}")
            return 0


# サービスインスタンス
email_service = EmailService()
