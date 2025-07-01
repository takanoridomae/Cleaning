"""
通知機能ルート

スケジュール通知の手動実行、設定管理、ステータス確認など
"""

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    g,
    session,
)
from datetime import datetime, timedelta
import pytz

from app import db
from app.models.schedule import Schedule
from app.models.user import User
from app.services.email_service import email_service
from app.routes.auth import login_required, admin_required, view_permission_required


bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@bp.route("/")
@login_required
@view_permission_required
def dashboard():
    """通知ダッシュボード"""
    try:
        # 今後24時間以内の通知対象スケジュール（日本時間）
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).replace(tzinfo=None)
        tomorrow = now + timedelta(days=1)

        upcoming_schedules = (
            Schedule.query.filter(
                Schedule.notification_enabled == True,
                Schedule.status == "pending",
                Schedule.start_datetime >= now,
                Schedule.start_datetime <= tomorrow,
            )
            .order_by(Schedule.start_datetime.asc())
            .all()
        )

        # メール設定状況
        mail_configured = email_service.is_configured()

        # 統計情報
        total_schedules = Schedule.query.filter(Schedule.status == "pending").count()
        notification_enabled_count = Schedule.query.filter(
            Schedule.notification_enabled == True, Schedule.status == "pending"
        ).count()

        stats = {
            "total_schedules": total_schedules,
            "notification_enabled": notification_enabled_count,
            "notification_disabled": total_schedules - notification_enabled_count,
            "upcoming_24h": len(upcoming_schedules),
        }

        return render_template(
            "notifications/dashboard.html",
            upcoming_schedules=upcoming_schedules,
            mail_configured=mail_configured,
            stats=stats,
        )

    except Exception as e:
        flash(f"ダッシュボード表示エラー: {e}", "danger")
        return redirect(url_for("schedules.list"))


@bp.route("/send-test", methods=["POST"])
@login_required
@admin_required
def send_test_email():
    """テストメール送信"""
    try:
        # デバッグ情報出力
        print(f"=== テストメール送信デバッグ ===")
        print(f"is_configured: {email_service.is_configured()}")
        print(f"smtp_server: {email_service.smtp_server}")
        print(f"smtp_port: {email_service.smtp_port}")
        print(f"username: {email_service.username}")
        print(f"password set: {bool(email_service.password)}")
        print(f"default_sender: {email_service.default_sender}")

        if not email_service.is_configured():
            flash("メール設定が不完全です。環境変数を確認してください。", "danger")
            return redirect(url_for("notifications.dashboard"))

            # 全ユーザーのメールアドレスを取得
        all_users = User.query.filter(User.email.isnot(None)).all()
        test_recipients = [
            user.email for user in all_users if user.email and "@" in user.email
        ]

        print(f"全ユーザー数: {len(all_users)}")
        print(f"有効なメールアドレスを持つユーザー: {len(test_recipients)}")
        print(f"test_recipients: {test_recipients}")

        if not test_recipients:
            flash("メールアドレスが設定されているユーザーが見つかりません。", "warning")
            return redirect(url_for("notifications.dashboard"))

        subject = "【テスト】通知機能動作確認（全ユーザー宛）"
        jst = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f8f9fa; padding: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>テスト通知（全ユーザー宛）</h1>
                </div>
                <div class="content">
                    <p>エアコンクリーニング完了報告書システムの通知機能が正常に動作しています。</p>
                    <p><strong>送信日時:</strong> {current_time}</p>
                    <p><strong>送信先:</strong> 登録されている全ユーザー（{len(test_recipients)}名）</p>
                    <p>この機能により、スケジュールの開始前リマインダーや開始通知が自動送信されます。</p>
                </div>
                <div class="footer">
                    <p>エアコンクリーニング完了報告書システム</p>
                    <p>このメールは自動送信されています。</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
テスト通知（全ユーザー宛）

エアコンクリーニング完了報告書システムの通知機能が正常に動作しています。

送信日時: {current_time}
送信先: 登録されている全ユーザー（{len(test_recipients)}名）

この機能により、スケジュールの開始前リマインダーや開始通知が自動送信されます。

---
エアコンクリーニング完了報告書システム
このメールは自動送信されています。
        """

        success = email_service.send_email(
            test_recipients, subject, html_body, text_body
        )

        if success:
            flash(
                f"テストメールを全ユーザー（{len(test_recipients)}名）に送信しました。",
                "success",
            )
        else:
            flash(
                "テストメールの送信に失敗しました。ログを確認してください。", "danger"
            )

    except Exception as e:
        flash(f"テストメール送信エラー: {e}", "danger")

    return redirect(url_for("notifications.dashboard"))


@bp.route("/check-notifications", methods=["POST"])
@login_required
@admin_required
def check_notifications():
    """手動通知チェック実行"""
    try:
        sent_count = email_service.check_and_send_notifications()

        if sent_count > 0:
            flash(f"通知を {sent_count} 件送信しました。", "success")
        else:
            flash("送信対象の通知はありませんでした。", "info")

    except Exception as e:
        flash(f"通知チェックエラー: {e}", "danger")

    return redirect(url_for("notifications.dashboard"))


@bp.route("/api/status")
@login_required
@view_permission_required
def api_status():
    """通知機能ステータスAPI"""
    try:
        status = {
            "mail_configured": email_service.is_configured(),
            "notification_enabled": email_service.enabled,
            "smtp_server": email_service.smtp_server,
            "smtp_port": email_service.smtp_port,
            "username": (
                email_service.username[:5] + "*****" if email_service.username else None
            ),
            "check_time": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
        }

        return jsonify(status)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/schedule/<int:schedule_id>/send", methods=["POST"])
@login_required
@admin_required
def send_schedule_notification(schedule_id):
    """特定スケジュールの通知を全ユーザーに手動送信"""
    try:
        schedule = Schedule.query.get_or_404(schedule_id)

        notification_type = request.form.get("type", "reminder")

        if not notification_type in ["reminder", "start", "complete"]:
            flash("無効な通知タイプです。", "danger")
            return redirect(url_for("schedules.view", id=schedule_id))

        # 全ユーザーに送信
        success = email_service.send_schedule_notification_to_all(
            schedule, notification_type
        )

        if success:
            type_names = {
                "reminder": "リマインダー",
                "start": "開始通知",
                "complete": "完了通知",
            }

            # 送信先ユーザー数を取得
            all_users = User.query.filter(User.email.isnot(None)).all()
            recipient_count = len(
                [user for user in all_users if user.email and "@" in user.email]
            )

            flash(
                f"「{schedule.title}」の{type_names[notification_type]}を全ユーザー（{recipient_count}名）に送信しました。",
                "success",
            )
        else:
            flash("通知の送信に失敗しました。", "danger")

    except Exception as e:
        flash(f"通知送信エラー: {e}", "danger")

    # 通知管理ダッシュボードにリダイレクト
    return redirect(url_for("notifications.dashboard"))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    """通知設定画面"""
    if request.method == "POST":
        # 現在は環境変数での設定のみサポート
        flash("通知設定は環境変数(.env)ファイルで管理されています。", "info")
        return redirect(url_for("notifications.settings"))

    # 現在の設定を表示
    current_settings = {
        "mail_server": email_service.smtp_server,
        "mail_port": email_service.smtp_port,
        "use_tls": email_service.use_tls,
        "username": email_service.username,
        "sender": email_service.default_sender,
        "enabled": email_service.enabled,
        "configured": email_service.is_configured(),
    }

    return render_template("notifications/settings.html", settings=current_settings)


@bp.route("/send-all-reminder", methods=["POST"])
@login_required
@admin_required
def send_all_reminder():
    """全ユーザーにリマインダー送信"""
    try:
        if not email_service.is_configured():
            flash("メール設定が不完全です。環境変数を確認してください。", "danger")
            return redirect(url_for("notifications.dashboard"))

        # 全ユーザーのメールアドレスを取得
        all_users = User.query.filter(User.email.isnot(None)).all()
        recipients = [
            user.email for user in all_users if user.email and "@" in user.email
        ]

        if not recipients:
            flash("メールアドレスが設定されているユーザーが見つかりません。", "warning")
            return redirect(url_for("notifications.dashboard"))

        # 今後24時間以内の通知対象スケジュール数を取得（日本時間）
        jst = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst).replace(tzinfo=None)
        tomorrow = now + timedelta(days=1)
        upcoming_count = Schedule.query.filter(
            Schedule.notification_enabled == True,
            Schedule.status == "pending",
            Schedule.start_datetime >= now,
            Schedule.start_datetime <= tomorrow,
        ).count()

        subject = (
            "【一括リマインダー】スケジュール通知 - エアコンクリーニング報告書システム"
        )
        current_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
                .schedule-info {{ background: white; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 20px; color: #6c757d; font-size: 14px; border-radius: 0 0 8px 8px; background: #e9ecef; }}
                .alert {{ padding: 12px; margin: 10px 0; border-radius: 4px; background: #d1ecf1; border: 1px solid #bee5eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 スケジュール一括リマインダー</h1>
                </div>
                <div class="content">
                    <p>エアコンクリーニング完了報告書システムからの一括リマインダーです。</p>
                    
                    <div class="schedule-info">
                        <h3>📊 現在の状況</h3>
                        <p><strong>送信日時:</strong> {current_time}</p>
                        <p><strong>送信先:</strong> 登録されている全ユーザー（{len(recipients)}名）</p>
                        <p><strong>今後24時間以内の通知対象:</strong> {upcoming_count} 件のスケジュール</p>
                    </div>
                    
                    <div class="alert">
                        <p><strong>💡 お知らせ:</strong></p>
                        <p>スケジュールの詳細確認や個別通知は、通知管理画面からご利用いただけます。</p>
                        <p>自動通知機能により、各スケジュールの開始前にも個別リマインダーが送信されます。</p>
                    </div>
                </div>
                <div class="footer">
                    <p>エアコンクリーニング完了報告書システム</p>
                    <p>このメールは管理者により送信されました。</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
📅 スケジュール一括リマインダー

エアコンクリーニング完了報告書システムからの一括リマインダーです。

📊 現在の状況:
- 送信日時: {current_time}
- 送信先: 登録されている全ユーザー（{len(recipients)}名）
- 今後24時間以内の通知対象: {upcoming_count} 件のスケジュール

💡 お知らせ:
スケジュールの詳細確認や個別通知は、通知管理画面からご利用いただけます。
自動通知機能により、各スケジュールの開始前にも個別リマインダーが送信されます。

---
エアコンクリーニング完了報告書システム
このメールは管理者により送信されました。
        """

        success = email_service.send_email(recipients, subject, html_body, text_body)

        if success:
            flash(
                f"全ユーザー（{len(recipients)}名）にリマインダーを送信しました。",
                "success",
            )
        else:
            flash(
                "リマインダーの送信に失敗しました。ログを確認してください。", "danger"
            )

    except Exception as e:
        flash(f"リマインダー送信エラー: {e}", "danger")

    return redirect(url_for("notifications.dashboard"))
