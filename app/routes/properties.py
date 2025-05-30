from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.property import Property
from app.models.customer import Customer
from app.models.air_conditioner import AirConditioner
from app.models.report import Report
from app.models.photo import Photo
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from app import db
from app.routes.auth import login_required
from sqlalchemy import or_
import os
from flask import current_app

bp = Blueprint("properties", __name__, url_prefix="/properties")


@bp.route("/")
@login_required
def list():
    """物件一覧画面表示"""
    # パラメータの取得
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 20  # 1ページあたりの表示件数

    # ベースクエリの作成
    query = Property.query.join(Customer)

    # 検索フィルタ（物件名、顧客名、住所、備考）
    if search:
        search_filter = or_(
            Property.name.contains(search),
            Customer.name.contains(search),
            Property.address.contains(search),
            Property.note.contains(search),
            Property.reception_type.contains(search),
            Property.reception_detail.contains(search),
        )
        query = query.filter(search_filter)

    # ソート処理
    sort_column = None
    if sort_by == "id":
        sort_column = Property.id
    elif sort_by == "name":
        sort_column = Property.name
    elif sort_by == "customer":
        sort_column = Customer.name
    elif sort_by == "address":
        sort_column = Property.address
    elif sort_by == "reception_type":
        sort_column = Property.reception_type
    elif sort_by == "created_at":
        sort_column = Property.created_at
    elif sort_by == "updated_at":
        sort_column = Property.updated_at
    else:
        sort_column = Property.created_at

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # ページネーション
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    properties = pagination.items

    return render_template(
        "properties/list.html",
        properties=properties,
        pagination=pagination,
        current_search=search,
        current_sort=sort_by,
        current_order=order,
    )


@bp.route("/<int:id>")
@login_required
def view(id):
    """物件詳細画面表示"""
    property = Property.query.get_or_404(id)
    return render_template("properties/view.html", property=property)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """新規物件登録"""
    customers = Customer.query.order_by(Customer.name).all()

    if request.method == "POST":
        name = request.form["name"]
        customer_id = request.form["customer_id"]
        address = request.form.get("address", "")
        postal_code = request.form.get("postal_code", "")
        note = request.form.get("note", "")
        reception_type = request.form.get("reception_type", "")
        reception_detail = request.form.get("reception_detail", "")

        error = None

        # 入力検証
        if not name:
            error = "物件名は必須です"

        if not customer_id:
            error = "お客様の選択は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            # 新規物件登録
            property = Property(
                name=name,
                customer_id=customer_id,
                address=address,
                postal_code=postal_code,
                note=note,
                reception_type=reception_type,
                reception_detail=reception_detail,
            )
            db.session.add(property)
            db.session.commit()

            # エアコン情報の登録
            # フォームから配列で送信されたエアコン情報を処理
            ac_types = request.form.getlist("ac_types[]")
            cleaning_types = request.form.getlist("cleaning_types[]")
            manufacturers = request.form.getlist("manufacturers[]")
            model_numbers = request.form.getlist("model_numbers[]")
            locations = request.form.getlist("locations[]")
            quantities = request.form.getlist("quantities[]")
            unit_prices = request.form.getlist("unit_prices[]")
            total_amounts = request.form.getlist("total_amounts[]")
            ac_notes = request.form.getlist("ac_notes[]")

            for i in range(len(ac_types)):
                # 空のフォームは無視
                if not ac_types[i] and not manufacturers[i] and not model_numbers[i]:
                    continue

                try:
                    quantity = int(quantities[i]) if quantities[i] else 1
                    unit_price = int(unit_prices[i]) if unit_prices[i] else None
                    total_amount = int(total_amounts[i]) if total_amounts[i] else None
                    location = locations[i] if i < len(locations) else ""

                    # エアコンデータの作成
                    air_conditioner = AirConditioner(
                        property_id=property.id,
                        ac_type=ac_types[i],
                        cleaning_type=cleaning_types[i],
                        manufacturer=manufacturers[i],
                        model_number=model_numbers[i].upper(),  # 品番を大文字に変換
                        location=location,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_amount=total_amount,
                        note=ac_notes[i],
                    )
                    db.session.add(air_conditioner)
                except Exception as e:
                    flash(
                        f"エアコン情報の登録中にエラーが発生しました: {str(e)}",
                        "warning",
                    )

            db.session.commit()
            flash("物件が正常に登録されました", "success")
            return redirect(url_for("properties.view", id=property.id))

    return render_template("properties/create.html", customers=customers)


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
def edit(id):
    """物件情報編集"""
    property = Property.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()

    if request.method == "POST":
        name = request.form["name"]
        customer_id = request.form["customer_id"]
        address = request.form.get("address", "")
        postal_code = request.form.get("postal_code", "")
        note = request.form.get("note", "")
        reception_type = request.form.get("reception_type", "")
        reception_detail = request.form.get("reception_detail", "")

        error = None

        # 入力検証
        if not name:
            error = "物件名は必須です"

        if not customer_id:
            error = "お客様の選択は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            # 物件情報更新
            property.name = name
            property.customer_id = customer_id
            property.address = address
            property.postal_code = postal_code
            property.note = note
            property.reception_type = reception_type
            property.reception_detail = reception_detail

            db.session.commit()
            flash("物件情報が正常に更新されました", "success")
            return redirect(url_for("properties.view", id=property.id))

    return render_template(
        "properties/edit.html", property=property, customers=customers
    )


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_property(id):
    """物件と関連データの削除"""
    property = Property.query.get_or_404(id)

    try:
        # 報告書が存在するかチェック
        reports = Report.query.filter_by(property_id=id).all()
        if reports:
            flash(
                f"物件「{property.name}」には{len(reports)}件の報告書が作成されているため削除できません。",
                "warning",
            )
            return redirect(url_for("properties.list"))

        # 関連する写真ファイルの削除
        air_conditioners = AirConditioner.query.filter_by(property_id=id).all()
        for ac in air_conditioners:
            # エアコンに関連する写真を取得
            photos = Photo.query.filter_by(air_conditioner_id=ac.id).all()
            for photo in photos:
                try:
                    # ファイルパスを取得
                    if hasattr(photo, "filepath") and photo.filepath:
                        photo_path = os.path.join(
                            current_app.config["UPLOAD_FOLDER"], photo.filepath
                        )
                    else:
                        # 従来のパス構造
                        photo_path = os.path.join(
                            current_app.config["UPLOAD_FOLDER"],
                            "before" if photo.photo_type == "before" else "after",
                            photo.filename,
                        )

                    # ファイルが存在する場合は削除
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        print(f"写真ファイル削除: {photo_path}")
                except Exception as e:
                    print(f"写真ファイル削除エラー: {e}")

        # 関連データの削除（外部キー制約により、物件を削除する前に関連データを削除する必要がある）
        # 写真データの削除
        Photo.query.filter(
            Photo.air_conditioner_id.in_([ac.id for ac in air_conditioners])
        ).delete(synchronize_session=False)

        # 作業時間データの削除
        WorkTime.query.filter_by(property_id=id).delete()

        # 作業内容データの削除
        WorkDetail.query.filter_by(property_id=id).delete()

        # エアコン情報の削除
        AirConditioner.query.filter_by(property_id=id).delete()

        # 物件自体の削除
        property_name = property.name
        db.session.delete(property)

        # 変更をコミット
        db.session.commit()

        flash(f"物件「{property_name}」とすべての関連データが削除されました", "success")
    except Exception as e:
        db.session.rollback()
        print(f"削除エラー: {e}")
        flash(f"物件の削除中にエラーが発生しました: {e}", "danger")

    return redirect(url_for("properties.list"))
