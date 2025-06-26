from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
    g,
    current_app,
)
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db
from datetime import datetime
import functools
import os

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


def permission_required(permission):
    """権限必須デコレータ"""

    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))

            user = User.query.get(session["user_id"])
            if not user or not user.active:
                flash("アカウントが無効化されています。", "danger")
                return redirect(url_for("auth.login"))

            # 権限チェック
            if permission == "view" and not user.can_view():
                flash("閲覧権限がありません。", "danger")
                return redirect(url_for("main.index"))
            elif permission == "edit" and not user.can_edit():
                flash("編集権限がありません。", "danger")
                return redirect(url_for("main.index"))
            elif permission == "create" and not user.can_create():
                flash("作成権限がありません。", "danger")
                return redirect(url_for("main.index"))
            elif permission == "delete" and not user.can_delete():
                flash("削除権限がありません。", "danger")
                return redirect(url_for("main.index"))

            return view(**kwargs)

        return wrapped_view

    return decorator


def view_permission_required(view):
    """閲覧権限必須デコレータ"""
    return permission_required("view")(view)


def edit_permission_required(view):
    """編集権限必須デコレータ"""
    return permission_required("edit")(view)


def create_permission_required(view):
    """作成権限必須デコレータ"""
    return permission_required("create")(view)


def delete_permission_required(view):
    """削除権限必須デコレータ"""
    return permission_required("delete")(view)


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


@bp.route("/admin/users")
@admin_required
def user_list():
    """ユーザー一覧表示"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/user_list.html", users=users)


@bp.route("/admin/users/create", methods=("GET", "POST"))
@admin_required
def create_user():
    """ユーザー作成"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        error = None

        # バリデーション
        if not username:
            error = "ユーザー名は必須です。"
        elif len(username) < 3:
            error = "ユーザー名は3文字以上で入力してください。"
        elif User.query.filter_by(username=username).first():
            error = "そのユーザー名は既に使用されています。"
        elif not email:
            error = "メールアドレスは必須です。"
        elif "@" not in email:
            error = "有効なメールアドレスを入力してください。"
        elif User.query.filter_by(email=email).first():
            error = "そのメールアドレスは既に使用されています。"
        elif not role or role not in User.ROLES:
            error = "有効な権限を選択してください。"
        elif not password:
            error = "パスワードは必須です。"
        elif len(password) < 6:
            error = "パスワードは6文字以上で入力してください。"
        elif password != confirm_password:
            error = "パスワードと確認用パスワードが一致しません。"

        if error is None:
            # ユーザー作成
            user = User(
                username=username,
                email=email,
                name=name if name else username,
                role=role,
            )
            user.set_password(password)

            try:
                db.session.add(user)
                db.session.commit()
                flash(f"ユーザー「{username}」を作成しました。", "success")
                return redirect(url_for("auth.user_list"))
            except Exception as e:
                db.session.rollback()
                error = "ユーザーの作成に失敗しました。"

        flash(error, "danger")

    return render_template("auth/create_user.html", roles=User.ROLES)


@bp.route("/admin/users/<int:user_id>/toggle")
@admin_required
def toggle_user_status(user_id):
    """ユーザーの有効/無効を切り替え"""
    user = User.query.get_or_404(user_id)

    # 自分自身は無効化できない
    if user.id == session["user_id"]:
        flash("自分自身のアカウントは無効化できません。", "danger")
        return redirect(url_for("auth.user_list"))

    # 管理者は無効化できない（最低1人は必要）
    if user.role == User.ROLE_ADMIN:
        admin_count = User.query.filter_by(role=User.ROLE_ADMIN, active=True).count()
        if admin_count <= 1:
            flash("管理者アカウントは最低1つ必要です。", "danger")
            return redirect(url_for("auth.user_list"))

    user.active = not user.active
    user.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        status = "有効" if user.active else "無効"
        flash(f"ユーザー「{user.username}」を{status}にしました。", "success")
    except Exception as e:
        db.session.rollback()
        flash("ユーザーステータスの変更に失敗しました。", "danger")

    return redirect(url_for("auth.user_list"))


@bp.route("/admin/users/<int:user_id>/edit", methods=("GET", "POST"))
@admin_required
def edit_user(user_id):
    """ユーザー編集"""
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        error = None

        # バリデーション
        if not username:
            error = "ユーザー名は必須です。"
        elif len(username) < 3:
            error = "ユーザー名は3文字以上で入力してください。"
        elif User.query.filter(User.username == username, User.id != user.id).first():
            error = "そのユーザー名は既に使用されています。"
        elif not email:
            error = "メールアドレスは必須です。"
        elif "@" not in email:
            error = "有効なメールアドレスを入力してください。"
        elif User.query.filter(User.email == email, User.id != user.id).first():
            error = "そのメールアドレスは既に使用されています。"
        elif not role or role not in User.ROLES:
            error = "有効な権限を選択してください。"
        elif new_password and len(new_password) < 6:
            error = "パスワードは6文字以上で入力してください。"
        elif new_password and new_password != confirm_password:
            error = "パスワードと確認用パスワードが一致しません。"

        # 管理者権限の変更制限
        if user.role == User.ROLE_ADMIN and role != User.ROLE_ADMIN:
            admin_count = User.query.filter_by(
                role=User.ROLE_ADMIN, active=True
            ).count()
            if admin_count <= 1:
                error = "管理者アカウントは最低1つ必要です。"

        if error is None:
            # ユーザー情報更新
            user.username = username
            user.email = email
            user.name = name if name else username
            user.role = role
            user.updated_at = datetime.utcnow()

            if new_password:
                user.set_password(new_password)

            try:
                db.session.commit()
                flash(f"ユーザー「{username}」を更新しました。", "success")
                return redirect(url_for("auth.user_list"))
            except Exception as e:
                db.session.rollback()
                error = "ユーザーの更新に失敗しました。"

        flash(error, "danger")

    return render_template("auth/edit_user.html", user=user, roles=User.ROLES)


@bp.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():
    """初回セットアップ用の管理者作成エンドポイント"""

    # 既に管理者が存在する場合はアクセス拒否
    admin_user = User.query.filter_by(role="admin").first()
    if admin_user is not None:
        flash("管理者は既に設定済みです。", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()

        # バリデーション
        if not all([username, password, confirm_password, email, name]):
            flash("すべての項目を入力してください。", "error")
            return render_template("auth/setup_admin.html")

        if password != confirm_password:
            flash("パスワードが一致しません。", "error")
            return render_template("auth/setup_admin.html")

        if len(password) < 6:
            flash("パスワードは6文字以上で設定してください。", "error")
            return render_template("auth/setup_admin.html")

        # ユーザー名の重複チェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("このユーザー名は既に使用されています。", "error")
            return render_template("auth/setup_admin.html")

        try:
            # 管理者ユーザーを作成
            admin = User(
                username=username,
                email=email,
                name=name,
                role="admin",
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            admin.set_password(password)

            # データベースに保存
            db.session.add(admin)
            db.session.commit()

            flash(
                "管理者アカウントが正常に作成されました。ログインしてください。",
                "success",
            )
            return redirect(url_for("auth.login"))

        except Exception as e:
            db.session.rollback()
            flash(f"管理者アカウントの作成に失敗しました: {str(e)}", "error")
            return render_template("auth/setup_admin.html")

    return render_template("auth/setup_admin.html")
