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

    def send_schedule_notification_to_all(
        self, schedule: Schedule, notification_type: str = "reminder"
    ) -> bool:
        """
        スケジュール通知メールを全ユーザーに送信

        Args:
            schedule: スケジュールオブジェクト
            notification_type: 通知タイプ（reminder, start, complete）

        Returns:
            bool: 送信成功の場合True
        """
        try:
            # 全ユーザーのメールアドレスを取得
            all_users = User.query.filter(User.email.isnot(None)).all()
            to_addresses = [
                user.email for user in all_users if user.email and "@" in user.email
            ]

            if not to_addresses:
                self.logger.warning("送信先となる有効なメールアドレスが見つかりません")
                return False

            # メール内容生成（全ユーザー向け）
            subject, html_body, text_body = (
                self._generate_all_user_notification_content(
                    schedule, notification_type, len(to_addresses)
                )
            )

            # メール送信
            success = self.send_email(to_addresses, subject, html_body, text_body)

            if success:
                self.logger.info(
                    f"スケジュール {schedule.id} の{notification_type}通知を全ユーザー（{len(to_addresses)}名）に送信完了"
                )

            return success

        except Exception as e:
            self.logger.error(f"全ユーザースケジュール通知エラー: {e}")
            return False

    def _generate_all_user_notification_content(
        self, schedule: Schedule, notification_type: str, recipient_count: int
    ) -> tuple:
        """
        全ユーザー向けスケジュール通知メール内容生成

        Args:
            schedule: スケジュールオブジェクト
            notification_type: 通知タイプ
            recipient_count: 送信先ユーザー数

        Returns:
            tuple: (件名, HTML本文, テキスト本文)
        """
        # 基本情報
        title = schedule.title
        start_time = schedule.start_datetime.strftime("%Y年%m月%d日 %H:%M")
        end_time = schedule.end_datetime.strftime("%Y年%m月%d日 %H:%M")
        current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # 詳細情報の組み立て
        schedule_details = []

        if schedule.description:
            schedule_details.append(f"説明: {schedule.description}")

        if schedule.customer:
            customer_detail = f"お客様: {schedule.customer.name}"
            if hasattr(schedule.customer, "phone") and schedule.customer.phone:
                customer_detail += f" (Tel: {schedule.customer.phone})"
            schedule_details.append(customer_detail)

        if schedule.schedule_property:
            property_detail = f"物件: {schedule.schedule_property.name}"
            if (
                hasattr(schedule.schedule_property, "address")
                and schedule.schedule_property.address
            ):
                property_detail += f"\n住所: {schedule.schedule_property.address}"
            schedule_details.append(property_detail)

        if schedule.creator:
            schedule_details.append(f"担当者: {schedule.creator.username}")

        # 優先度の表示
        priority_names = {"low": "低", "normal": "通常", "high": "高", "urgent": "緊急"}
        priority_display = priority_names.get(schedule.priority, "通常")

        # 通知タイプ別の件名とメッセージ
        if notification_type == "reminder":
            subject = f"【全社通知】スケジュールリマインダー: {title}"
            message_title = "📅 スケジュールリマインダー（全社通知）"
            message_body = f"以下のスケジュールが {schedule.notification_minutes} 分後に開始予定です。関係者の皆様はご確認ください。"
            icon = "⏰"
        elif notification_type == "start":
            subject = f"【全社通知】スケジュール開始: {title}"
            message_title = "🚀 スケジュール開始通知（全社通知）"
            message_body = "以下のスケジュールが開始時刻になりました。関係者の皆様はご確認ください。"
            icon = "▶️"
        elif notification_type == "complete":
            subject = f"【全社通知】スケジュール完了: {title}"
            message_title = "✅ スケジュール完了通知（全社通知）"
            message_body = "以下のスケジュールが完了しました。"
            icon = "✅"
        else:
            subject = f"【全社通知】スケジュール通知: {title}"
            message_title = "📢 スケジュール通知（全社通知）"
            message_body = "重要なスケジュール情報をお知らせします。"
            icon = "📢"

        # HTML本文
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', 'Hiragino Sans', 'Yu Gothic UI', Arial, sans-serif; 
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                }}
                .container {{ 
                    max-width: 650px; 
                    margin: 0 auto; 
                    padding: 20px; 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                    color: white; 
                    padding: 25px; 
                    text-align: center; 
                    border-radius: 8px 8px 0 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .content {{ 
                    background: #f8f9fa; 
                    padding: 25px; 
                    border: 1px solid #dee2e6;
                }}
                .schedule-card {{ 
                    background: white; 
                    padding: 20px; 
                    border-left: 5px solid #007bff; 
                    margin: 15px 0; 
                    border-radius: 0 8px 8px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .priority-high {{ border-left-color: #dc3545; }}
                .priority-urgent {{ border-left-color: #dc3545; background: #fff5f5; }}
                .info-row {{ 
                    display: flex; 
                    padding: 8px 0; 
                    border-bottom: 1px solid #eee;
                }}
                .info-row:last-child {{ border-bottom: none; }}
                .info-label {{ 
                    font-weight: bold; 
                    min-width: 100px; 
                    color: #495057;
                }}
                .info-value {{ 
                    flex: 1; 
                    color: #212529;
                }}
                .footer {{ 
                    text-align: center; 
                    padding: 20px; 
                    color: #6c757d; 
                    font-size: 14px; 
                    border-radius: 0 0 8px 8px; 
                    background: #e9ecef;
                }}
                .alert {{ 
                    padding: 15px; 
                    margin: 15px 0; 
                    border-radius: 6px; 
                    background: #d1ecf1; 
                    border: 1px solid #bee5eb; 
                    color: #0c5460;
                }}
                .priority-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .priority-low {{ background: #d4edda; color: #155724; }}
                .priority-normal {{ background: #cce7ff; color: #004085; }}
                .priority-high {{ background: #fff3cd; color: #856404; }}
                .priority-urgent {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{icon} {message_title}</h1>
                    <p style="margin: 0; opacity: 0.9;">エアコンクリーニング完了報告書システム</p>
                </div>
                <div class="content">
                    <p style="font-size: 16px; margin-bottom: 20px;">{message_body}</p>
                    
                    <div class="schedule-card {'priority-' + schedule.priority if schedule.priority in ['high', 'urgent'] else ''}">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h2 style="margin: 0; color: #007bff;">{title}</h2>
                            <span class="priority-badge priority-{schedule.priority}">優先度: {priority_display}</span>
                        </div>
                        
                        <div class="info-row">
                            <div class="info-label">📅 開始日時:</div>
                            <div class="info-value">{start_time}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">🕐 終了日時:</div>
                            <div class="info-value">{end_time}</div>
                        </div>
                        
                        {chr(10).join([f'<div class="info-row"><div class="info-label">📋</div><div class="info-value">{detail}</div></div>' for detail in schedule_details]) if schedule_details else ''}
                        
                        <div class="info-row">
                            <div class="info-label">⏰ 通知設定:</div>
                            <div class="info-value">{schedule.notification_minutes}分前に通知</div>
                        </div>
                    </div>
                    
                    <div class="alert">
                        <p><strong>💡 お知らせ:</strong></p>
                        <p>この通知は全登録ユーザー（{recipient_count}名）に送信されています。</p>
                        <p>スケジュールの詳細確認や変更は、システムの通知管理画面からご利用ください。</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #6c757d; margin-top: 20px;">
                        <strong>送信日時:</strong> {current_time}<br>
                        <strong>送信先:</strong> 全登録ユーザー（{recipient_count}名）
                    </p>
                </div>
                <div class="footer">
                    <p><strong>エアコンクリーニング完了報告書システム</strong></p>
                    <p>このメールは管理者により全社に送信されました。</p>
                </div>
            </div>
        </body>
        </html>
        """

        # テキスト本文
        text_body = f"""
{icon} {message_title}

{message_body}

📋 スケジュール詳細:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
タイトル: {title}
優先度: {priority_display}
開始日時: {start_time}
終了日時: {end_time}
通知設定: {schedule.notification_minutes}分前に通知

{chr(10).join([f"- {detail}" for detail in schedule_details]) if schedule_details else ""}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 お知らせ:
この通知は全登録ユーザー（{recipient_count}名）に送信されています。
スケジュールの詳細確認や変更は、システムの通知管理画面からご利用ください。

送信日時: {current_time}
送信先: 全登録ユーザー（{recipient_count}名）

---
エアコンクリーニング完了報告書システム
このメールは管理者により全社に送信されました。
        """

        return subject, html_body, text_body


# サービスインスタンス
email_service = EmailService()
