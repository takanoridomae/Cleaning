from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_file,
    make_response,
)
from datetime import datetime, date, time
from app.models.customer import Customer
from app.models.property import Property
from app.models.report import Report
from app.models.user import User
from app.models.photo import Photo
from app.models.air_conditioner import AirConditioner
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from app.models.work_item import WorkItem
from app.models.schedule import Schedule
from app import db
from flask_login import login_required
import json
import os
import tempfile

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
                                    # datetime型フィールドの変換
                                    if any(
                                        keyword in field_name.lower()
                                        for keyword in [
                                            "created_at",
                                            "updated_at",
                                            "last_login",  # 追加
                                            "start_datetime",  # schedules用
                                            "end_datetime",  # schedules用
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

                                    # date型フィールドの変換（work_dateなど）
                                    elif any(
                                        keyword in field_name.lower()
                                        for keyword in [
                                            "work_date",
                                            "recurrence_end",
                                            "date",
                                        ]
                                    ):
                                        try:
                                            from datetime import date

                                            # ISO形式の日付文字列をdateオブジェクトに変換
                                            item_data[field_name] = (
                                                datetime.fromisoformat(
                                                    field_value
                                                ).date()
                                            )
                                        except (ValueError, AttributeError):
                                            pass

                                    # time型フィールドの変換（start_time, end_timeなど）
                                    elif any(
                                        keyword in field_name.lower()
                                        for keyword in ["start_time", "end_time"]
                                    ):
                                        try:
                                            from datetime import time

                                            # HH:MM:SS形式の時間文字列をtimeオブジェクトに変換
                                            time_parts = field_value.split(":")
                                            if len(time_parts) >= 2:
                                                hour = int(time_parts[0])
                                                minute = int(time_parts[1])
                                                second = (
                                                    int(time_parts[2])
                                                    if len(time_parts) > 2
                                                    else 0
                                                )
                                                item_data[field_name] = time(
                                                    hour, minute, second
                                                )
                                        except (ValueError, AttributeError, IndexError):
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
                            # エラー発生時は個別ロールバックではなく、エラーログのみ記録
                            # db.session.rollback() を削除（これが原因でテーブル全体がロールバックされていた）
                            continue

                    # テーブル毎にコミットを実行（エラーがあっても成功分は保存）
                    try:
                        if imported_count > 0 or updated_count > 0:
                            db.session.commit()
                            print(
                                f"  💾 {table_name}テーブル保存完了: 新規{imported_count}件, 更新{updated_count}件"
                            )
                    except Exception as commit_error:
                        db.session.rollback()
                        print(f"  ❌ {table_name}テーブル保存エラー: {commit_error}")
                        # コミットエラーの場合は該当テーブルの成功カウントをリセット
                        imported_count = 0
                        updated_count = 0

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

                # 最終結果の表示（テーブル毎にコミット済みなので、ここでの追加コミットは不要）
                print(
                    f"✅ 全データインポート処理完了: 新規{total_imported}件, 更新{total_updated}件"
                )

                # 詳細結果をフラッシュメッセージに
                if total_imported > 0 or total_updated > 0:
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


@bp.route("/admin/export-database", methods=["GET", "POST"])
def export_database():
    """データベース全体をJSONファイルとしてエクスポート（管理者用）"""
    print("🔍 データベースエクスポート画面にアクセスしました")

    if request.method == "POST":
        try:
            # モデルのインポート（関数内で明示的にインポート）
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

            def serialize_datetime(obj):
                """日付・時刻オブジェクトを文字列に変換"""
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif isinstance(obj, time):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            def export_table_data(model_class, table_name):
                """指定されたテーブルのデータをエクスポート"""
                try:
                    print(f"📋 {table_name}テーブルをエクスポート中...")

                    # 全データを取得
                    records = model_class.query.all()
                    data = []

                    for record in records:
                        # モデルインスタンスを辞書に変換
                        record_dict = {}
                        for column in record.__table__.columns:
                            value = getattr(record, column.name)
                            record_dict[column.name] = value
                        data.append(record_dict)

                    print(f"  ✅ {len(data)}件のデータを取得")
                    return data

                except Exception as e:
                    print(f"  ❌ エラー: {e}")
                    import traceback

                    traceback.print_exc()
                    return []

            print("🚀 全テーブルデータエクスポート開始...")

            # エクスポート対象テーブル（依存関係順）
            export_config = [
                (User, "users"),
                (Customer, "customers"),
                (Property, "properties"),
                (Report, "reports"),
                (Photo, "photos"),
                (AirConditioner, "air_conditioners"),
                (WorkTime, "work_times"),
                (WorkDetail, "work_details"),
                (WorkItem, "work_items"),
                (Schedule, "schedules"),
            ]

            all_data = {}
            total_records = 0

            for model_class, table_name in export_config:
                table_data = export_table_data(model_class, table_name)
                all_data[table_name] = table_data
                total_records += len(table_data)

            # ファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"all_data_export_{timestamp}.json"

            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".json", encoding="utf-8"
            ) as tmp_file:
                json.dump(
                    all_data,
                    tmp_file,
                    ensure_ascii=False,
                    indent=2,
                    default=serialize_datetime,
                )
                temp_file_path = tmp_file.name

            # ファイルサイズ取得
            file_size = os.path.getsize(temp_file_path)
            file_size_mb = file_size / (1024 * 1024)

            print(f"\n🎉 エクスポート完了!")
            print(f"📁 ファイル名: {filename}")
            print(f"📊 総レコード数: {total_records}件")
            print(f"💾 ファイルサイズ: {file_size_mb:.2f}MB")

            # テーブル別サマリー
            print(f"\n📋 テーブル別データ数:")
            for table_name, table_data in all_data.items():
                print(f"  • {table_name}: {len(table_data)}件")

            flash(
                f"✅ データベースエクスポート完了: {total_records}件 ({file_size_mb:.2f}MB)",
                "success",
            )

            # ファイルをダウンロードとして送信
            def remove_file(response):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                return response

            response = make_response(
                send_file(
                    temp_file_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/json",
                )
            )
            response.call_on_close(remove_file)
            return response

        except Exception as e:
            print(f"❌ エクスポートエラー: {e}")
            import traceback

            traceback.print_exc()
            flash(f"❌ エクスポートエラー: {str(e)}", "error")
            return redirect(request.url)

    # 現在の各テーブルのレコード数を表示
    try:
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
            "schedules": Schedule.query.count(),
        }

        total_records = sum(table_counts.values())

    except Exception as e:
        print(f"⚠️ テーブルカウント取得エラー: {e}")
        table_counts = {}
        total_records = 0

    return render_template(
        "admin/export_database.html",
        table_counts=table_counts,
        total_records=total_records,
    )
