from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from app.models.customer import Customer
from app.models.property import Property
from app.models.report import Report
from app import db
from flask_login import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """ダッシュボード画面を表示"""
    # 統計情報の取得
    stats = {
        "customer_count": Customer.query.count(),
        "property_count": Property.query.count(),
        "report_count": Report.query.count(),
        "pending_count": Report.query.filter_by(status="pending").count(),
    }

    # 最近の報告書を取得（最新5件）
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()

    # 最近のお客様を取得（最新5件）
    recent_customers = (
        Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
    )

    # 最近の物件を取得（最新5件）
    recent_properties = (
        Property.query.order_by(Property.created_at.desc()).limit(5).all()
    )

    return render_template(
        "index.html",
        stats=stats,
        recent_reports=recent_reports,
        recent_customers=recent_customers,
        recent_properties=recent_properties,
    )


@bp.route("/admin/upload-aircon-data", methods=["GET", "POST"])
def upload_aircon_data():
    """エアコンデータアップロード（管理者用）"""
    # 手動でログイン状態をチェック
    from flask_login import current_user

    if not current_user.is_authenticated:
        flash("ログインが必要です", "error")
        return redirect(url_for("auth.login"))

    print(f"ユーザー情報: {current_user.username}, 権限: {current_user.role}")

    if request.method == "POST":
        try:
            # JSONファイルのアップロード処理
            if "aircon_file" not in request.files:
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            file = request.files["aircon_file"]
            if file.filename == "":
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            if file and file.filename.endswith(".json"):
                # JSONファイルを読み込み
                import json
                from app.models.air_conditioner import AirConditioner

                content = file.read().decode("utf-8")
                data = json.loads(content)

                imported_count = 0
                updated_count = 0
                errors = []

                for i, item in enumerate(data):
                    try:
                        # IDを除いてデータを準備
                        item_data = {k: v for k, v in item.items() if k != "id"}

                        # 必須フィールドの確認
                        if not item_data.get("property_id"):
                            errors.append(f"Item {i}: property_id is required")
                            continue

                        # 既存レコードを確認
                        existing = AirConditioner.query.filter_by(
                            property_id=item_data.get("property_id"),
                            manufacturer=item_data.get("manufacturer"),
                            model_number=item_data.get("model_number"),
                        ).first()

                        if existing:
                            # 既存レコードを更新
                            for key, value in item_data.items():
                                if hasattr(existing, key):
                                    setattr(existing, key, value)
                            updated_count += 1
                        else:
                            # 新規レコードを作成
                            new_aircon = AirConditioner(**item_data)
                            db.session.add(new_aircon)
                            imported_count += 1

                    except Exception as e:
                        errors.append(f"Item {i}: {str(e)}")
                        continue

                # データベースに保存
                if imported_count > 0 or updated_count > 0:
                    db.session.commit()
                    flash(
                        f"インポート完了: 新規追加 {imported_count}件, 更新 {updated_count}件",
                        "success",
                    )
                else:
                    flash("インポートできるデータがありませんでした", "warning")

                if errors:
                    flash(f"エラー {len(errors)}件が発生しました", "warning")

                return redirect(url_for("main.upload_aircon_data"))
            else:
                flash("JSONファイルを選択してください", "error")
                return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash(f"アップロードエラー: {str(e)}", "error")
            return redirect(request.url)

    # 現在のエアコン数を表示
    from app.models.air_conditioner import AirConditioner

    current_count = AirConditioner.query.count()

    return render_template("admin/upload_aircon_data.html", current_count=current_count)


@bp.route("/test-upload", methods=["GET", "POST"])
def test_upload():
    """認証なしのテスト用アップロード画面"""
    if request.method == "POST":
        try:
            # JSONファイルのアップロード処理
            if "aircon_file" not in request.files:
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            file = request.files["aircon_file"]
            if file.filename == "":
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            if file and file.filename.endswith(".json"):
                # JSONファイルを読み込み
                import json
                from app.models.air_conditioner import AirConditioner

                content = file.read().decode("utf-8")
                data = json.loads(content)

                imported_count = 0
                updated_count = 0
                errors = []

                for i, item in enumerate(data):
                    try:
                        # IDを除いてデータを準備
                        item_data = {k: v for k, v in item.items() if k != "id"}

                        # 必須フィールドの確認
                        if not item_data.get("property_id"):
                            errors.append(f"Item {i}: property_id is required")
                            continue

                        # 既存レコードを確認
                        existing = AirConditioner.query.filter_by(
                            property_id=item_data.get("property_id"),
                            manufacturer=item_data.get("manufacturer"),
                            model_number=item_data.get("model_number"),
                        ).first()

                        if existing:
                            # 既存レコードを更新
                            for key, value in item_data.items():
                                if hasattr(existing, key):
                                    setattr(existing, key, value)
                            updated_count += 1
                        else:
                            # 新規レコードを作成
                            new_aircon = AirConditioner(**item_data)
                            db.session.add(new_aircon)
                            imported_count += 1

                    except Exception as e:
                        errors.append(f"Item {i}: {str(e)}")
                        continue

                # データベースに保存
                if imported_count > 0 or updated_count > 0:
                    db.session.commit()
                    flash(
                        f"✅ インポート完了: 新規追加 {imported_count}件, 更新 {updated_count}件",
                        "success",
                    )
                else:
                    flash("⚠️ インポートできるデータがありませんでした", "warning")

                if errors:
                    flash(f"⚠️ エラー {len(errors)}件が発生しました", "warning")

                return redirect(url_for("main.test_upload"))
            else:
                flash("❌ JSONファイルを選択してください", "error")
                return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash(f"❌ アップロードエラー: {str(e)}", "error")
            return redirect(request.url)

    # 現在のエアコン数を表示
    from app.models.air_conditioner import AirConditioner

    current_count = AirConditioner.query.count()

    return render_template("admin/upload_aircon_data.html", current_count=current_count)
