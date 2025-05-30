from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    g,
)
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db
from datetime import datetime
import functools

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """ログイン必須デコレータ"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    """管理者権限必須デコレータ"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        user = User.query.get(session["user_id"])
        if not user or user.role != "admin":
            flash("この操作には管理者権限が必要です。", "danger")
            return redirect(url_for("main.index"))

        return view(**kwargs)

    return wrapped_view


@bp.route("/login", methods=("GET", "POST"))
def login():
    """ログイン処理"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        user = User.query.filter_by(username=username).first()

        if user is None:
            error = "ユーザー名が正しくありません。"
        elif not user.check_password(password):
            error = "パスワードが正しくありません。"
        elif not user.active:
            error = "このアカウントは現在無効になっています。"

        if error is None:
            # セッションをクリアし、ユーザーIDを保存
            session.clear()
            session["user_id"] = user.id

            # 最終ログイン日時を更新
            user.last_login = datetime.utcnow()
            db.session.commit()

            return redirect(url_for("main.index"))

        flash(error, "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """ログアウト処理"""
    session.clear()
    flash("ログアウトしました。", "success")
    return redirect(url_for("auth.login"))


@bp.route("/admin/settings", methods=("GET", "POST"))
@admin_required
def admin_settings():
    """管理者設定変更"""
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        current_password = request.form.get("current_password", "").strip()
        new_username = request.form.get("new_username", "").strip()
        new_name = request.form.get("new_name", "").strip()
        new_email = request.form.get("new_email", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        error = None

        # 現在のパスワード確認
        if not current_password:
            error = "現在のパスワードを入力してください。"
        elif not user.check_password(current_password):
            error = "現在のパスワードが正しくありません。"

        # 新しいユーザー名の検証
        if not error and new_username:
            if len(new_username) < 3:
                error = "ユーザー名は3文字以上で入力してください。"
            elif User.query.filter(
                User.username == new_username, User.id != user.id
            ).first():
                error = "そのユーザー名は既に使用されています。"

        # 新しいメールアドレスの検証
        if not error and new_email:
            if "@" not in new_email:
                error = "有効なメールアドレスを入力してください。"
            elif User.query.filter(User.email == new_email, User.id != user.id).first():
                error = "そのメールアドレスは既に使用されています。"

        # 新しいパスワードの検証
        if not error and new_password:
            if len(new_password) < 6:
                error = "パスワードは6文字以上で入力してください。"
            elif new_password != confirm_password:
                error = "パスワードと確認用パスワードが一致しません。"

        if error is None:
            # 情報を更新
            updated_fields = []

            if new_username and new_username != user.username:
                user.username = new_username
                updated_fields.append("ユーザー名")

            if new_name and new_name != user.name:
                user.name = new_name
                updated_fields.append("表示名")

            if new_email and new_email != user.email:
                user.email = new_email
                updated_fields.append("メールアドレス")

            if new_password:
                user.set_password(new_password)
                updated_fields.append("パスワード")

            if updated_fields:
                user.updated_at = datetime.utcnow()
                db.session.commit()
                flash(f'{", ".join(updated_fields)}を更新しました。', "success")
            else:
                flash("変更する項目がありません。", "info")

            return redirect(url_for("auth.admin_settings"))

        flash(error, "danger")

    return render_template("auth/admin_settings.html", user=user)


@bp.before_app_request
def load_logged_in_user():
    """リクエスト前にログイン中のユーザー情報をロード"""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)
