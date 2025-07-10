from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    session,
)
from app.models.property import Property
from app.models.customer import Customer
from app.models.air_conditioner import AirConditioner
from app.models.report import Report
from app.models.photo import Photo
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
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
import os
import re
from flask import current_app

bp = Blueprint("properties", __name__, url_prefix="/properties")


def extract_customer_name_from_property(property_name):
    """物件名から顧客名部分（「様」までの文字）を抽出する"""
    if not property_name:
        return ""

    # 「様」の位置を見つける
    sama_index = property_name.find("様")
    if sama_index != -1:
        # 「様」が見つかった場合は、「様」を含む部分まで抽出
        return property_name[: sama_index + 1]
    else:
        # 「様」が見つからない場合は、全体を返す
        return property_name


def check_property_name_duplicate(property_name, exclude_property_id=None):
    """物件名の重複チェック（「様」までの文字で判定）"""
    customer_part = extract_customer_name_from_property(property_name)

    if not customer_part:
        return False

    # データベースから全ての物件を取得して重複チェック
    properties = Property.query.all()

    for prop in properties:
        # 編集時は自分自身を除外
        if exclude_property_id and prop.id == exclude_property_id:
            continue

        # 既存の物件名から顧客名部分を抽出
        existing_customer_part = extract_customer_name_from_property(prop.name)

        # 顧客名部分が一致する場合は重複
        if customer_part == existing_customer_part:
            return True

    return False


@bp.route("/")
@login_required
@view_permission_required
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

    current_user = User.query.get(session["user_id"])
    return render_template(
        "properties/list.html",
        properties=properties,
        pagination=pagination,
        current_search=search,
        current_sort=sort_by,
        current_order=order,
        current_user=current_user,
    )


@bp.route("/<int:id>")
@login_required
@view_permission_required
def view(id):
    """物件詳細画面表示"""
    property = Property.query.get_or_404(id)
    current_user = User.query.get(session["user_id"])
    return render_template(
        "properties/view.html", property=property, current_user=current_user
    )


@bp.route("/create", methods=("GET", "POST"))
@login_required
@create_permission_required
def create():
    """新規物件登録"""
    customers = Customer.query.order_by(Customer.name).all()
    current_user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form["name"]
        customer_id = request.form["customer_id"]

        # 機密情報は権限のあるユーザーのみ取得
        if current_user.can_view_sensitive_info():
            address = request.form.get("address", "")
            postal_code = request.form.get("postal_code", "")
            note = request.form.get("note", "")
        else:
            address = ""
            postal_code = ""
            note = ""
        reception_type = request.form.get("reception_type", "")
        reception_detail = request.form.get("reception_detail", "")

        error = None

        # 入力検証
        if not name:
            error = "物件名は必須です"

        if not customer_id:
            error = "お客様の選択は必須です"

        # 物件名重複チェック
        if not error and check_property_name_duplicate(name):
            customer_part = extract_customer_name_from_property(name)
            error = f"物件名「{customer_part}」は既に登録されています。同一のお客様名での物件登録はできません。"

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

    return render_template(
        "properties/create.html", customers=customers, current_user=current_user
    )


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
@edit_permission_required
def edit(id):
    """物件情報編集"""
    property = Property.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    current_user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form["name"]
        customer_id = request.form["customer_id"]

        # 機密情報は権限のあるユーザーのみ取得・更新
        if current_user.can_view_sensitive_info():
            address = request.form.get("address", "")
            postal_code = request.form.get("postal_code", "")
            note = request.form.get("note", "")
        else:
            # 権限がない場合は既存の値を保持
            address = property.address
            postal_code = property.postal_code
            note = property.note
        reception_type = request.form.get("reception_type", "")
        reception_detail = request.form.get("reception_detail", "")

        error = None

        # 入力検証
        if not name:
            error = "物件名は必須です"

        if not customer_id:
            error = "お客様の選択は必須です"

        # 物件名重複チェック（編集時は自分自身を除外）
        if not error and check_property_name_duplicate(name, exclude_property_id=id):
            customer_part = extract_customer_name_from_property(name)
            error = f"物件名「{customer_part}」は既に登録されています。同一のお客様名での物件登録はできません。"

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
        "properties/edit.html",
        property=property,
        customers=customers,
        current_user=current_user,
    )


@bp.route("/check_duplicate", methods=["POST"])
@login_required
def check_duplicate():
    """AJAX用の物件名重複チェックエンドポイント"""
    try:
        data = request.get_json()
        property_name = data.get("property_name", "")
        exclude_property_id = data.get("exclude_property_id")

        if not property_name:
            return jsonify({"is_duplicate": False, "message": ""})

        is_duplicate = check_property_name_duplicate(property_name, exclude_property_id)

        if is_duplicate:
            customer_part = extract_customer_name_from_property(property_name)
            message = f"物件名「{customer_part}」は既に登録されています。"
            return jsonify({"is_duplicate": True, "message": message})
        else:
            return jsonify({"is_duplicate": False, "message": ""})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@delete_permission_required
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
