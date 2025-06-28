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
    """エアコンデータアップロード（管理者用）- 認証なし版"""
    print("🔍 エアコンデータアップロード画面にアクセスしました")

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
                from datetime import datetime

                content = file.read().decode("utf-8")
                data = json.loads(content)

                imported_count = 0
                updated_count = 0
                errors = []

                for i, item in enumerate(data):
                    try:
                        # IDを除いてデータを準備
                        item_data = {k: v for k, v in item.items() if k != "id"}

                        # 日付フィールドの変換（デプロイ環境対応）
                        for date_field in ["created_at", "updated_at"]:
                            if date_field in item_data and item_data[date_field]:
                                try:
                                    if isinstance(item_data[date_field], str):
                                        # 文字列から日付オブジェクトに変換
                                        item_data[date_field] = datetime.fromisoformat(
                                            item_data[date_field].replace("Z", "+00:00")
                                        )
                                except (ValueError, AttributeError) as e:
                                    print(f"⚠️ 日付変換エラー {date_field}: {e}")
                                    # 現在の日時を設定
                                    item_data[date_field] = datetime.now()

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
                    print(
                        f"✅ データベース保存完了: 新規{imported_count}件, 更新{updated_count}件"
                    )
                    flash(
                        f"🎉 インポート完了: 新規追加 {imported_count}件, 更新 {updated_count}件",
                        "success",
                    )
                else:
                    print("⚠️ インポート対象データなし")
                    flash("⚠️ インポートできるデータがありませんでした", "warning")

                if errors:
                    print(f"⚠️ エラー発生: {len(errors)}件")
                    for error in errors[:5]:  # 最初の5件のエラーを表示
                        print(f"  - {error}")
                    flash(f"⚠️ エラー {len(errors)}件が発生しました", "warning")

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
                from datetime import datetime

                content = file.read().decode("utf-8")
                data = json.loads(content)

                imported_count = 0
                updated_count = 0
                errors = []

                for i, item in enumerate(data):
                    try:
                        # IDを除いてデータを準備
                        item_data = {k: v for k, v in item.items() if k != "id"}

                        # 日付フィールドの変換（デプロイ環境対応）
                        for date_field in ["created_at", "updated_at"]:
                            if date_field in item_data and item_data[date_field]:
                                try:
                                    if isinstance(item_data[date_field], str):
                                        # 文字列から日付オブジェクトに変換
                                        item_data[date_field] = datetime.fromisoformat(
                                            item_data[date_field].replace("Z", "+00:00")
                                        )
                                except (ValueError, AttributeError) as e:
                                    print(f"⚠️ テスト版日付変換エラー {date_field}: {e}")
                                    # 現在の日時を設定
                                    item_data[date_field] = datetime.now()

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
                    print(
                        f"✅ テスト版データベース保存完了: 新規{imported_count}件, 更新{updated_count}件"
                    )
                    flash(
                        f"🎉 インポート完了: 新規追加 {imported_count}件, 更新 {updated_count}件",
                        "success",
                    )
                else:
                    print("⚠️ テスト版インポート対象データなし")
                    flash("⚠️ インポートできるデータがありませんでした", "warning")

                if errors:
                    print(f"⚠️ テスト版エラー発生: {len(errors)}件")
                    for error in errors[:3]:  # 最初の3件のエラーを表示
                        print(f"  - {error}")
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


@bp.route("/admin/upload-all-data", methods=["GET", "POST"])
def upload_all_data():
    """全テーブルデータアップロード（管理者用）"""
    print("🔍 全データアップロード画面にアクセスしました")

    if request.method == "POST":
        try:
            # JSONファイルのアップロード処理
            if "all_data_file" not in request.files:
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            file = request.files["all_data_file"]
            if file.filename == "":
                flash("ファイルが選択されていません", "error")
                return redirect(request.url)

            if file and file.filename.endswith(".json"):
                # JSONファイルを読み込み
                import json
                from datetime import datetime
                from app.models.user import User
                from app.models.customer import Customer
                from app.models.property import Property
                from app.models.report import Report
                from app.models.photo import Photo
                from app.models.air_conditioner import AirConditioner
                from app.models.work_time import WorkTime
                from app.models.work_detail import WorkDetail
                from app.models.work_item import WorkItem
                from app.models.schedule import Schedule

                content = file.read().decode("utf-8")
                all_data = json.loads(content)

                # インポート順序（依存関係を考慮）
                import_config = [
                    ("users", User),
                    ("customers", Customer),
                    ("properties", Property),
                    ("reports", Report),
                    ("photos", Photo),
                    ("air_conditioners", AirConditioner),
                    ("work_times", WorkTime),
                    ("work_details", WorkDetail),
                    ("work_items", WorkItem),
                    (
                        "schedules",
                        Schedule,
                    ),  # 追加：他テーブルへの外部キー参照があるため最後に配置
                ]

                total_imported = 0
                total_updated = 0
                total_errors = 0
                results = {}

                for table_name, model_class in import_config:
                    if table_name not in all_data:
                        print(f"⚠️ {table_name}テーブルのデータが見つかりません")
                        continue

                    print(f"📋 {table_name}テーブルをインポート中...")
                    table_data = all_data[table_name]

                    imported_count = 0
                    updated_count = 0
                    errors = []

                    for i, item in enumerate(table_data):
                        try:
                            # IDを除いてデータを準備
                            item_data = {k: v for k, v in item.items() if k != "id"}

                            # 日付フィールドの変換（デプロイ環境対応）
                            for field_name, field_value in item_data.items():
                                if field_value and isinstance(field_value, str):
                                    # 日付っぽい文字列を変換（より広範囲なフィールドに対応）
                                    if any(
                                        keyword in field_name.lower()
                                        for keyword in [
                                            "created_at",
                                            "updated_at",
                                            "last_login",  # 追加
                                            "start_datetime",  # schedules用
                                            "end_datetime",  # schedules用
                                            "recurrence_end",  # schedules用
                                            "date",
                                            "time",
                                        ]
                                    ):
                                        try:
                                            # ISO形式の文字列をdatetimeオブジェクトに変換
                                            item_data[field_name] = (
                                                datetime.fromisoformat(
                                                    field_value.replace("Z", "+00:00")
                                                )
                                            )
                                        except (ValueError, AttributeError):
                                            # 変換できない場合はそのまま
                                            pass

                            # 既存レコードの確認（IDベース）
                            original_id = item.get("id")
                            existing = None
                            if original_id:
                                existing = model_class.query.filter_by(
                                    id=original_id
                                ).first()

                            if existing:
                                # 既存レコードを更新
                                for key, value in item_data.items():
                                    if hasattr(existing, key):
                                        setattr(existing, key, value)
                                updated_count += 1
                            else:
                                # 新規レコードを作成（IDも含める）
                                if original_id:
                                    item_data["id"] = original_id
                                new_record = model_class(**item_data)
                                db.session.add(new_record)
                                imported_count += 1

                        except Exception as e:
                            errors.append(f"Item {i}: {str(e)}")
                            print(f"❌ {table_name}テーブル Item {i} エラー: {e}")
                            # エラー発生時はセッションをロールバック
                            db.session.rollback()
                            continue

                    # テーブル毎の結果を記録
                    results[table_name] = {
                        "imported": imported_count,
                        "updated": updated_count,
                        "errors": len(errors),
                    }

                    total_imported += imported_count
                    total_updated += updated_count
                    total_errors += len(errors)

                    print(
                        f"  ✅ {table_name}: 新規{imported_count}件, 更新{updated_count}件, エラー{len(errors)}件"
                    )

                # データベースに保存
                if total_imported > 0 or total_updated > 0:
                    db.session.commit()
                    print(
                        f"✅ 全データベース保存完了: 新規{total_imported}件, 更新{total_updated}件"
                    )

                    # 詳細結果をフラッシュメッセージに
                    result_msg = f"🎉 全データインポート完了!<br>"
                    result_msg += (
                        f"📊 総計: 新規{total_imported}件, 更新{total_updated}件<br>"
                    )
                    for table_name, result in results.items():
                        result_msg += f"• {table_name}: 新規{result['imported']}件, 更新{result['updated']}件<br>"

                    flash(result_msg, "success")
                else:
                    print("⚠️ インポート対象データなし")
                    flash("⚠️ インポートできるデータがありませんでした", "warning")

                if total_errors > 0:
                    flash(f"⚠️ 合計{total_errors}件のエラーが発生しました", "warning")

                return redirect(url_for("main.upload_all_data"))
            else:
                flash("❌ JSONファイルを選択してください", "error")
                return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            print(f"❌ 全データアップロードエラー: {e}")
            flash(f"❌ アップロードエラー: {str(e)}", "error")
            return redirect(request.url)

    # 現在の各テーブルのレコード数を表示
    try:
        from app.models.user import User
        from app.models.customer import Customer
        from app.models.property import Property
        from app.models.report import Report
        from app.models.photo import Photo
        from app.models.air_conditioner import AirConditioner
        from app.models.work_time import WorkTime
        from app.models.work_detail import WorkDetail
        from app.models.work_item import WorkItem
        from app.models.schedule import Schedule

        table_counts = {
            "users": User.query.count(),
            "customers": Customer.query.count(),
            "properties": Property.query.count(),
            "reports": Report.query.count(),
            "photos": Photo.query.count(),
            "air_conditioners": AirConditioner.query.count(),
            "work_times": WorkTime.query.count(),
            "work_details": WorkDetail.query.count(),
            "work_items": WorkItem.query.count(),
            "schedules": Schedule.query.count(),  # 追加
        }
    except Exception as e:
        print(f"⚠️ テーブルカウント取得エラー: {e}")
        table_counts = {}

    return render_template("admin/upload_all_data.html", table_counts=table_counts)
