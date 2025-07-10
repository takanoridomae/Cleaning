from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.models.customer import Customer
from app.models.property import Property
from app.models.user import User
from app import db
from app.routes.auth import (
    login_required,
    view_permission_required,
    edit_permission_required,
    create_permission_required,
    delete_permission_required,
)
from sqlalchemy import or_

bp = Blueprint("customers", __name__, url_prefix="/customers")


@bp.route("/")
@login_required
@view_permission_required
def list():
    """顧客一覧画面表示"""
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    current_user = User.query.get(session["user_id"])
    return render_template(
        "customers/list.html", customers=customers, current_user=current_user
    )


@bp.route("/<int:id>")
@login_required
@view_permission_required
def view(id):
    """顧客詳細画面表示"""
    customer = Customer.query.get_or_404(id)
    current_user = User.query.get(session["user_id"])
    return render_template(
        "customers/view.html", customer=customer, current_user=current_user
    )


@bp.route("/create", methods=("GET", "POST"))
@login_required
@create_permission_required
def create():
    """新規顧客登録"""
    current_user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form["name"]
        company_name = request.form.get("company_name", "")
        email = request.form.get("email", "")

        # 機密情報は権限のあるユーザーのみ取得
        if current_user.can_view_sensitive_info():
            phone = request.form.get("phone", "")
            postal_code = request.form.get("postal_code", "")
            address = request.form.get("address", "")
        else:
            phone = ""
            postal_code = ""
            address = ""

        note = request.form.get("note", "")

        error = None

        # 入力検証
        if not name:
            error = "顧客名は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            # 新規顧客登録
            customer = Customer(
                name=name,
                company_name=company_name,
                email=email,
                phone=phone,
                postal_code=postal_code,
                address=address,
                note=note,
            )
            db.session.add(customer)
            db.session.commit()
            flash("顧客が正常に登録されました", "success")
            return redirect(url_for("customers.list"))

    return render_template("customers/create.html", current_user=current_user)


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
@edit_permission_required
def edit(id):
    """顧客情報編集"""
    customer = Customer.query.get_or_404(id)
    current_user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form["name"]
        company_name = request.form.get("company_name", "")
        email = request.form.get("email", "")

        # 機密情報は権限のあるユーザーのみ取得
        if current_user.can_view_sensitive_info():
            phone = request.form.get("phone", "")
            postal_code = request.form.get("postal_code", "")
            address = request.form.get("address", "")
        else:
            phone = ""
            postal_code = ""
            address = ""

        note = request.form.get("note", "")

        error = None

        # 入力検証
        if not name:
            error = "顧客名は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            # 顧客情報更新
            customer.name = name
            customer.company_name = company_name
            customer.email = email
            customer.phone = phone
            customer.postal_code = postal_code
            customer.address = address
            customer.note = note

            db.session.commit()
            flash("顧客情報が正常に更新されました", "success")
            return redirect(url_for("customers.list"))

    return render_template(
        "customers/edit.html", customer=customer, current_user=current_user
    )


@bp.route("/<int:id>/delete")
@login_required
@delete_permission_required
def delete(id):
    """顧客情報削除"""
    customer = Customer.query.get_or_404(id)

    # 関連する物件があるか確認
    if customer.properties and len(customer.properties) > 0:
        flash(
            f"削除できません。お客様「{customer.name}」には{len(customer.properties)}件の物件が関連付けられています。"
            "お客様情報を削除するには、まず関連する物件をすべて削除してください。",
            "danger",
        )
        return redirect(url_for("customers.view", id=customer.id))

    try:
        db.session.delete(customer)
        db.session.commit()
        flash("顧客情報が正常に削除されました", "success")
    except Exception as e:
        db.session.rollback()
        flash(
            "顧客情報の削除に失敗しました。",
            "danger",
        )

    return redirect(url_for("customers.list"))
