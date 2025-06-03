from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models.air_conditioner import AirConditioner
from app.models.property import Property
from app.models.photo import Photo
from app import db
from app.routes.auth import login_required, view_permission_required, edit_permission_required, create_permission_required, delete_permission_required
import os
from flask import current_app

bp = Blueprint("air_conditioners", __name__, url_prefix="/air_conditioners")


@bp.route("/property/<int:property_id>")
@login_required
@view_permission_required
def list_by_property(property_id):
    """物件に関連するエアコン一覧表示"""
    property = Property.query.get_or_404(property_id)
    air_conditioners = AirConditioner.query.filter_by(property_id=property_id).all()
    return render_template(
        "air_conditioners/list.html",
        property=property,
        air_conditioners=air_conditioners,
    )


@bp.route("/api/property/<int:property_id>")
@login_required
@view_permission_required
def api_list_by_property(property_id):
    """物件に関連するエアコン一覧をJSON形式で返す（API）"""
    air_conditioners = AirConditioner.query.filter_by(property_id=property_id).all()
    return jsonify(
        {
            "property_id": property_id,
            "air_conditioners": [ac.to_dict() for ac in air_conditioners],
        }
    )


@bp.route("/create/<int:property_id>", methods=("GET", "POST"))
@login_required
@create_permission_required
def create(property_id):
    """エアコン情報新規登録"""
    property = Property.query.get_or_404(property_id)

    if request.method == "POST":
        # フォームからデータを取得
        ac_type = request.form.get("ac_type", "")
        manufacturer = request.form.get("manufacturer", "")
        model_number = request.form.get(
            "model_number", ""
        ).upper()  # 品番を大文字に変換
        quantity = request.form.get("quantity", 1)
        unit_price = request.form.get("unit_price", 0)
        total_amount = request.form.get("total_amount", 0)
        cleaning_type = request.form.get("cleaning_type", "")
        note = request.form.get("note", "")
        location = request.form.get("location", "")

        # デバッグ情報
        print("フォームデータ:", request.form)
        print("location:", location)

        # データ検証
        if not location and "location" in request.form:
            location = request.form["location"]
            print("location (再取得):", location)

        # エアコン情報登録
        air_conditioner = AirConditioner(
            property_id=property_id,
            ac_type=ac_type,
            manufacturer=manufacturer,
            model_number=model_number,
            quantity=int(quantity),
            unit_price=int(unit_price) if unit_price else None,
            total_amount=int(total_amount) if total_amount else None,
            cleaning_type=cleaning_type,
            note=note,
            location=location,
        )

        db.session.add(air_conditioner)
        db.session.commit()
        flash("エアコン情報が正常に登録されました", "success")
        return redirect(
            url_for("air_conditioners.list_by_property", property_id=property_id)
        )

    return render_template("air_conditioners/create.html", property=property)


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
@edit_permission_required
def edit(id):
    """エアコン情報編集"""
    air_conditioner = AirConditioner.query.get_or_404(id)
    property = Property.query.get_or_404(air_conditioner.property_id)

    if request.method == "POST":
        # フォームからデータを取得
        ac_type = request.form.get("ac_type", "")
        manufacturer = request.form.get("manufacturer", "")
        model_number = request.form.get(
            "model_number", ""
        ).upper()  # 品番を大文字に変換
        quantity = request.form.get("quantity", 1)
        unit_price = request.form.get("unit_price", 0)
        total_amount = request.form.get("total_amount", 0)
        cleaning_type = request.form.get("cleaning_type", "")
        note = request.form.get("note", "")
        location = request.form.get("location", "")

        # デバッグ情報
        print("フォームデータ (編集):", request.form)
        print("location (編集):", location)

        # データ検証
        if not location and "location" in request.form:
            location = request.form["location"]
            print("location (編集・再取得):", location)

        # エアコン情報更新
        air_conditioner.ac_type = ac_type
        air_conditioner.manufacturer = manufacturer
        air_conditioner.model_number = model_number
        air_conditioner.quantity = int(quantity)
        air_conditioner.unit_price = int(unit_price) if unit_price else None
        air_conditioner.total_amount = int(total_amount) if total_amount else None
        air_conditioner.cleaning_type = cleaning_type
        air_conditioner.note = note
        air_conditioner.location = location

        db.session.commit()
        flash("エアコン情報が正常に更新されました", "success")
        return redirect(
            url_for(
                "air_conditioners.list_by_property",
                property_id=air_conditioner.property_id,
            )
        )

    return render_template(
        "air_conditioners/edit.html", air_conditioner=air_conditioner, property=property
    )


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
@delete_permission_required
def delete(id):
    """エアコン情報削除"""
    air_conditioner = AirConditioner.query.get_or_404(id)
    property_id = air_conditioner.property_id

    db.session.delete(air_conditioner)
    db.session.commit()

    flash("エアコン情報が削除されました", "success")
    return redirect(
        url_for("air_conditioners.list_by_property", property_id=property_id)
    )
