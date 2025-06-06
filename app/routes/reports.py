from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
    send_file,
    Response,
    make_response,
)
from app.models.report import Report
from app.models.property import Property
from app.models.photo import Photo
from app.models.work_time import WorkTime
from app.models.work_detail import WorkDetail
from app.models.work_item import WorkItem
from app.models.customer import Customer
from app.models.air_conditioner import AirConditioner
from app.models.schedule import Schedule
from app import db
from sqlalchemy import or_
import os
from datetime import datetime, time, date
from werkzeug.utils import secure_filename
from app.routes.auth import (
    login_required,
    view_permission_required,
    edit_permission_required,
    create_permission_required,
    delete_permission_required,
)
from app.services.pdf_service import PDFService
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from io import BytesIO

bp = Blueprint("reports", __name__, url_prefix="/reports")


def create_schedule_from_work_times(
    report, work_dates, start_times, end_times, property_id
):
    """作業時間からスケジュールを自動作成する関数"""
    try:
        # 作業日が複数ある場合は、最初の作業日をベースにスケジュールを作成
        if work_dates and work_dates[0]:
            work_date = datetime.strptime(work_dates[0], "%Y-%m-%d")

            # 開始時間と終了時間を取得（デフォルト値も設定）
            start_time = None
            end_time = None

            if start_times and start_times[0]:
                try:
                    start_time = datetime.strptime(start_times[0], "%H:%M").time()
                except ValueError:
                    start_time = time(9, 0)  # デフォルト 09:00
            else:
                start_time = time(9, 0)

            if end_times and end_times[0]:
                try:
                    end_time = datetime.strptime(end_times[0], "%H:%M").time()
                except ValueError:
                    end_time = time(17, 0)  # デフォルト 17:00
            else:
                end_time = time(17, 0)

            # スケジュールのタイトルを生成
            property_obj = Property.query.get(property_id)
            customer_name = (
                property_obj.customer.name
                if property_obj and property_obj.customer
                else "不明"
            )
            property_name = property_obj.name if property_obj else "不明"
            title = f"作業: {customer_name} - {property_name}"

            # 説明文を生成
            description = f"報告書 #{report.id} の作業\n"
            if report.work_address:
                description += f"作業場所: {report.work_address}\n"
            if report.note:
                description += f"備考: {report.note}"

            # スケジュールを作成（ステータスは後で報告書と同期する）
            schedule = Schedule(
                title=title,
                description=description,
                start_datetime=datetime.combine(work_date.date(), start_time),
                end_datetime=datetime.combine(work_date.date(), end_time),
                all_day=False,
                status="pending",  # 初期ステータス（後で報告書ステータスと同期）
                priority="normal",
                customer_id=property_obj.customer_id if property_obj else None,
                property_id=property_id,
                report_id=report.id,  # 報告書との関連付け
            )

            db.session.add(schedule)

            # 複数の作業日がある場合は追加のスケジュールも作成
            for i in range(1, len(work_dates)):
                if work_dates[i]:
                    try:
                        additional_work_date = datetime.strptime(
                            work_dates[i], "%Y-%m-%d"
                        )
                        additional_start_time = time(9, 0)
                        additional_end_time = time(17, 0)

                        if i < len(start_times) and start_times[i]:
                            try:
                                additional_start_time = datetime.strptime(
                                    start_times[i], "%H:%M"
                                ).time()
                            except ValueError:
                                pass

                        if i < len(end_times) and end_times[i]:
                            try:
                                additional_end_time = datetime.strptime(
                                    end_times[i], "%H:%M"
                                ).time()
                            except ValueError:
                                pass

                        additional_schedule = Schedule(
                            title=f"作業: {customer_name} - {property_name} (Day {i+1})",
                            description=f"報告書 #{report.id} の作業 (作業日 {i+1})",
                            start_datetime=datetime.combine(
                                additional_work_date.date(), additional_start_time
                            ),
                            end_datetime=datetime.combine(
                                additional_work_date.date(), additional_end_time
                            ),
                            all_day=False,
                            status="pending",  # 初期ステータス（後で報告書ステータスと同期）
                            priority="normal",
                            customer_id=(
                                property_obj.customer_id if property_obj else None
                            ),
                            property_id=property_id,
                            report_id=report.id,
                        )

                        db.session.add(additional_schedule)
                    except ValueError:
                        # 日付形式が不正な場合はスキップ
                        continue

    except Exception as e:
        # エラーが発生してもスケジュール作成失敗を報告書作成の失敗にしない
        print(f"スケジュール自動作成エラー: {e}")


def update_schedule_from_work_times(
    report, work_dates, start_times, end_times, property_id
):
    """報告書編集時に関連スケジュールを更新する関数"""
    try:
        # 既存の関連スケジュールを取得
        existing_schedules = Schedule.query.filter_by(report_id=report.id).all()

        # 既存スケジュールを削除
        for schedule in existing_schedules:
            db.session.delete(schedule)

        # 新しい作業時間からスケジュールを再作成
        if work_dates and any(work_dates):
            create_schedule_from_work_times(
                report, work_dates, start_times, end_times, property_id
            )

    except Exception as e:
        print(f"スケジュール更新エラー: {e}")


def sync_schedule_status_with_report(report):
    """報告書のステータス変更に応じてスケジュールのステータスを同期する関数"""
    try:
        # 報告書に関連するスケジュールを取得
        related_schedules = Schedule.query.filter_by(report_id=report.id).all()

        # 報告書ステータスとスケジュールステータスの対応表
        status_mapping = {
            "draft": "pending",  # 下書き → 未完了
            "pending": "pending",  # 作業中 → 未完了
            "completed": "completed",  # 完了 → 完了
            "cancelled": "cancelled",  # キャンセル → キャンセル
            "on_hold": "pending",  # 保留 → 未完了（該当する場合）
        }

        # 対応するスケジュールステータスを取得
        schedule_status = status_mapping.get(report.status, "pending")

        # 関連スケジュールのステータスを更新
        updated_count = 0
        for schedule in related_schedules:
            if schedule.status != schedule_status:
                schedule.status = schedule_status
                schedule.updated_at = datetime.now()
                updated_count += 1

        if updated_count > 0:
            print(
                f"報告書 #{report.id} の関連スケジュール {updated_count} 件のステータスを {schedule_status} に更新しました"
            )

    except Exception as e:
        print(f"スケジュールステータス同期エラー: {e}")


@bp.route("/")
@login_required
@view_permission_required
def list():
    """報告書一覧画面表示"""
    # パラメータの取得
    status = request.args.get("status", None)
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 20  # 1ページあたりの表示件数

    # ベースクエリの作成（WorkTimeテーブルもJOINして作業日での検索を可能にする）
    # WorkTimeテーブルには複数の外部キーがあるため、明示的にJOIN条件を指定
    query = (
        Report.query.join(Property)
        .join(Customer)
        .outerjoin(WorkTime, Report.id == WorkTime.report_id)
    )

    # ステータスフィルタ
    if status:
        query = query.filter(Report.status == status)

    # 検索フィルタ（顧客名、物件名、作業住所、備考、報告日、作業日、ステータス）
    if search:
        search_conditions = [
            Customer.name.contains(search),
            Property.name.contains(search),
            Report.work_address.contains(search),
            Report.note.contains(search),
            # 報告日での検索（YYYY-MM-DD形式）
            Report.date.cast(db.String).contains(search),
            # 作業日での検索（YYYY-MM-DD形式）
            WorkTime.work_date.cast(db.String).contains(search),
            # ステータスでの検索（英語コード）
            Report.status.contains(search),
        ]

        # 日本語ステータス検索
        search_lower = search.lower()
        if "未完了" in search_lower:
            search_conditions.append(Report.status == "pending")
        if "完了" in search_lower and "未完了" not in search_lower:
            search_conditions.append(Report.status == "completed")
        if "下書き" in search_lower:
            search_conditions.append(Report.status == "draft")
        if "キャンセル" in search_lower:
            search_conditions.append(Report.status == "cancelled")

        search_filter = or_(*search_conditions)
        query = query.filter(search_filter)

    # 重複を除去（WorkTimeとのJOINで重複が発生する可能性があるため）
    query = query.distinct()

    # ソート処理
    sort_column = None
    if sort_by == "id":
        sort_column = Report.id
    elif sort_by == "date":
        sort_column = Report.date
    elif sort_by == "work_date":
        # 作業日でのソート（最初の作業日を基準）
        sort_column = WorkTime.work_date
    elif sort_by == "customer":
        sort_column = Customer.name
    elif sort_by == "property":
        sort_column = Property.name
    elif sort_by == "status":
        sort_column = Report.status
    elif sort_by == "updated_at":
        sort_column = Report.updated_at
    else:
        sort_column = Report.created_at

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # ページネーション
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items

    # 各報告書の作業日情報を取得
    for report in reports:
        # その報告書の作業日を取得（日付順）
        work_times = (
            WorkTime.query.filter_by(report_id=report.id)
            .order_by(WorkTime.work_date.asc())
            .all()
        )
        report.work_dates = [wt.work_date for wt in work_times]
        report.work_times_data = work_times

    return render_template(
        "reports/list.html",
        reports=reports,
        pagination=pagination,
        current_status=status,
        current_search=search,
        current_sort=sort_by,
        current_order=order,
    )


@bp.route("/create", methods=("GET", "POST"))
@login_required
@create_permission_required
def create():
    """新規報告書作成"""
    properties = (
        Property.query.join(Customer).order_by(Customer.name, Property.name).all()
    )

    # 作業項目の取得
    work_items = WorkItem.query.filter_by(is_active=True).order_by(WorkItem.name).all()

    # URLパラメータから物件IDを取得
    default_property_id = request.args.get("property_id")
    default_address = ""

    # 物件IDが指定されている場合は住所を取得
    if default_property_id:
        property_obj = Property.query.get(default_property_id)
        if property_obj:
            default_address = property_obj.address or ""

    if request.method == "POST":
        property_id = request.form["property_id"]
        report_date = request.form.get("date")
        work_address = request.form.get("work_address", "")
        note = request.form.get("note", "")

        # 作業時間の取得
        work_dates = request.form.getlist("work_dates[]")
        start_times = request.form.getlist("start_times[]")
        end_times = request.form.getlist("end_times[]")
        work_time_notes = request.form.getlist("work_time_notes[]")  # 備考欄の値を取得

        # 作業内容の取得
        work_item_ids = request.form.getlist("work_item_ids[]")
        work_item_texts = request.form.getlist("work_item_texts[]")
        descriptions = request.form.getlist("descriptions[]")
        confirmations = request.form.getlist("confirmations[]")
        air_conditioner_ids = request.form.getlist("air_conditioner_ids[]")

        error = None

        # 入力検証
        if not property_id:
            error = "物件の選択は必須です"

        if not report_date:
            error = "報告書日付は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            # 新規報告書登録
            report = Report(
                title="作業完了書",  # デフォルトタイトル
                property_id=property_id,
                date=datetime.strptime(report_date, "%Y-%m-%d").date(),
                work_address=work_address,
                note=note,
                status="pending",  # 初期状態は作成中
            )

            db.session.add(report)
            db.session.flush()  # IDを生成するためにフラッシュ

            # 作業時間を登録
            for i in range(len(work_dates)):
                if (
                    i < len(work_dates)
                    and work_dates[i]
                    and i < len(start_times)
                    and start_times[i]
                    and i < len(end_times)
                    and end_times[i]
                ):
                    try:
                        work_time = WorkTime(
                            report_id=report.id,
                            property_id=property_id,
                            work_date=datetime.strptime(
                                work_dates[i], "%Y-%m-%d"
                            ).date(),
                            start_time=datetime.strptime(
                                start_times[i], "%H:%M"
                            ).time(),
                            end_time=datetime.strptime(end_times[i], "%H:%M").time(),
                            note=(
                                work_time_notes[i] if i < len(work_time_notes) else None
                            ),  # 備考欄の値を設定
                        )
                        db.session.add(work_time)
                    except ValueError:
                        # 時間形式が不正な場合はスキップ
                        continue

            # 作業内容を登録
            for i in range(len(descriptions)):
                if i < len(descriptions) and descriptions[i]:
                    # work_item_idかwork_item_textのどちらかを設定
                    work_item_id = None
                    work_item_text = None
                    air_conditioner_id = None

                    if (
                        i < len(work_item_ids)
                        and work_item_ids[i]
                        and work_item_ids[i] != "other"
                    ):
                        work_item_id = work_item_ids[i]
                    elif i < len(work_item_texts) and work_item_texts[i]:
                        work_item_text = work_item_texts[i]
                    else:
                        # どちらも指定がない場合はスキップ
                        continue

                    # エアコンIDの設定（空文字列の場合はNoneに）
                    if i < len(air_conditioner_ids) and air_conditioner_ids[i]:
                        if air_conditioner_ids[i].strip():  # 空白のみでないことを確認
                            try:
                                air_conditioner_id = int(air_conditioner_ids[i])
                                print(
                                    f"DEBUG: エアコンID {air_conditioner_id} が設定されました"
                                )
                            except (ValueError, TypeError):
                                # 整数に変換できない場合はエラーログを出力
                                print(
                                    f"Warning: Invalid air_conditioner_id: {air_conditioner_ids[i]}"
                                )
                                air_conditioner_id = None

                    work_detail = WorkDetail(
                        report_id=report.id,
                        property_id=property_id,  # 常に物件IDを設定
                        air_conditioner_id=air_conditioner_id,
                        work_item_id=work_item_id,
                        work_item_text=work_item_text,
                        description=descriptions[i],
                        confirmation=confirmations[i] if i < len(confirmations) else "",
                    )
                    db.session.add(work_detail)

            # 作業日からスケジュールを自動作成
            create_schedule_from_work_times(
                report, work_dates, start_times, end_times, property_id
            )

            # 作成後のスケジュールのステータスを報告書に合わせて同期
            sync_schedule_status_with_report(report)

            db.session.commit()
            flash(
                "報告書とスケジュールが作成されました。写真を追加してください。",
                "success",
            )
            return redirect(url_for("reports.edit", id=report.id))

    return render_template(
        "reports/create.html",
        properties=properties,
        work_items=work_items,
        default_property_id=default_property_id,
        default_address=default_address,
    )


@bp.route("/<int:id>")
@login_required
@view_permission_required
def view(id):
    """報告書詳細画面表示"""
    report = Report.query.get_or_404(id)

    # 作業時間の取得
    work_times = (
        WorkTime.query.filter_by(report_id=id)
        .order_by(WorkTime.work_date, WorkTime.start_time)
        .all()
    )

    # 作業内容の取得
    work_details = WorkDetail.query.filter_by(report_id=id).all()

    # 施工前後の写真を取得
    before_photos = Photo.query.filter_by(report_id=id, photo_type="before").all()
    after_photos = Photo.query.filter_by(report_id=id, photo_type="after").all()

    # 写真ペアの作成
    photo_pairs = []
    # 最大枚数に合わせてループ
    max_photos = max(len(before_photos), len(after_photos))
    for i in range(max_photos):
        before_photo = before_photos[i] if i < len(before_photos) else None
        after_photo = after_photos[i] if i < len(after_photos) else None
        photo_pairs.append((before_photo, after_photo))

    return render_template(
        "reports/view.html",
        report=report,
        work_times=work_times,
        work_details=work_details,
        photo_pairs=photo_pairs,
    )


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
@edit_permission_required
def edit(id):
    """報告書編集"""
    report = Report.query.get_or_404(id)
    properties = (
        Property.query.join(Customer).order_by(Customer.name, Property.name).all()
    )

    # 作業項目の取得
    work_items = WorkItem.query.filter_by(is_active=True).order_by(WorkItem.name).all()

    # 写真の取得
    before_photos = Photo.query.filter_by(report_id=id, photo_type="before").all()
    after_photos = Photo.query.filter_by(report_id=id, photo_type="after").all()

    # 作業時間の取得
    work_times = (
        WorkTime.query.filter_by(report_id=id)
        .order_by(WorkTime.work_date, WorkTime.start_time)
        .all()
    )

    # 作業内容の取得
    work_details = WorkDetail.query.filter_by(report_id=id).all()

    # エアコンIDと作業内容の整合性を確認（デバッグ用）
    for detail in work_details:
        if detail.air_conditioner_id:
            print(
                f"作業内容ID: {detail.id}, エアコンID: {detail.air_conditioner_id}, 物件ID: {detail.property_id}"
            )

    # 物件の住所を取得
    default_address = ""
    if report.property:
        default_address = report.property.address or ""

    if request.method == "POST":
        if "update_report" in request.form:
            # 報告書情報の更新
            property_id = request.form["property_id"]
            report_date = request.form.get("date")
            work_address = request.form.get("work_address", "")
            note = request.form.get("note", "")
            status = request.form.get("status", "pending")

            # 作業時間の取得
            work_dates = request.form.getlist("work_dates[]")
            start_times = request.form.getlist("start_times[]")
            end_times = request.form.getlist("end_times[]")
            work_time_ids = request.form.getlist("work_time_ids[]")
            work_time_notes = request.form.getlist(
                "work_time_notes[]"
            )  # 備考欄の値を取得

            # 作業内容の取得
            work_item_ids = request.form.getlist("work_item_ids[]")
            work_item_texts = request.form.getlist("work_item_texts[]")
            descriptions = request.form.getlist("descriptions[]")
            confirmations = request.form.getlist("confirmations[]")
            work_detail_ids = request.form.getlist("work_detail_ids[]")
            air_conditioner_ids = request.form.getlist("air_conditioner_ids[]")

            error = None

            # 入力検証
            if not property_id:
                error = "物件の選択は必須です"

            if not report_date:
                error = "報告書日付は必須です"

            if error is not None:
                flash(error, "danger")
            else:
                # 報告書情報更新
                report.property_id = property_id
                report.date = datetime.strptime(report_date, "%Y-%m-%d").date()
                report.work_address = work_address
                report.note = note
                report.status = status

                # 既存の作業時間を更新または削除
                existing_work_time_ids = [wt.id for wt in work_times]
                for wt_id in existing_work_time_ids:
                    if str(wt_id) not in work_time_ids:
                        # 削除するべき作業時間
                        WorkTime.query.filter_by(id=wt_id).delete()

                # 作業時間を更新または追加
                for i in range(len(work_dates)):
                    if (
                        i < len(work_dates)
                        and work_dates[i]
                        and i < len(start_times)
                        and start_times[i]
                        and i < len(end_times)
                        and end_times[i]
                    ):
                        try:
                            if i < len(work_time_ids) and work_time_ids[i]:
                                # 既存の作業時間を更新
                                work_time = WorkTime.query.get(work_time_ids[i])
                                if work_time:
                                    work_time.work_date = datetime.strptime(
                                        work_dates[i], "%Y-%m-%d"
                                    ).date()
                                    work_time.start_time = datetime.strptime(
                                        start_times[i], "%H:%M"
                                    ).time()
                                    work_time.end_time = datetime.strptime(
                                        end_times[i], "%H:%M"
                                    ).time()
                                    work_time.note = (
                                        work_time_notes[i]
                                        if i < len(work_time_notes)
                                        else None
                                    )  # 備考欄の値を設定
                            else:
                                # 新規作業時間を追加
                                work_time = WorkTime(
                                    report_id=report.id,
                                    property_id=property_id,
                                    work_date=datetime.strptime(
                                        work_dates[i], "%Y-%m-%d"
                                    ).date(),
                                    start_time=datetime.strptime(
                                        start_times[i], "%H:%M"
                                    ).time(),
                                    end_time=datetime.strptime(
                                        end_times[i], "%H:%M"
                                    ).time(),
                                    note=(
                                        work_time_notes[i]
                                        if i < len(work_time_notes)
                                        else None
                                    ),  # 備考欄の値を設定
                                )
                                db.session.add(work_time)
                        except ValueError:
                            # 時間形式が不正な場合はスキップ
                            continue

                # 既存の作業内容を更新または削除
                existing_work_detail_ids = [wd.id for wd in work_details]
                for wd_id in existing_work_detail_ids:
                    if str(wd_id) not in work_detail_ids:
                        # 削除するべき作業内容
                        WorkDetail.query.filter_by(id=wd_id).delete()

                # 作業内容を更新または追加
                for i in range(len(descriptions)):
                    if i < len(descriptions) and descriptions[i]:
                        # work_item_idかwork_item_textのどちらかを設定
                        work_item_id = None
                        work_item_text = None
                        air_conditioner_id = None

                        if (
                            i < len(work_item_ids)
                            and work_item_ids[i]
                            and work_item_ids[i] != "other"
                        ):
                            work_item_id = work_item_ids[i]
                        elif i < len(work_item_texts) and work_item_texts[i]:
                            work_item_text = work_item_texts[i]

                        # エアコンIDの設定（空文字列の場合はNoneに）
                        if i < len(air_conditioner_ids) and air_conditioner_ids[i]:
                            if air_conditioner_ids[
                                i
                            ].strip():  # 空白のみでないことを確認
                                try:
                                    air_conditioner_id = int(air_conditioner_ids[i])
                                    print(
                                        f"DEBUG: エアコンID {air_conditioner_id} が設定されました"
                                    )
                                except (ValueError, TypeError):
                                    # 整数に変換できない場合はエラーログを出力
                                    print(
                                        f"Warning: Invalid air_conditioner_id: {air_conditioner_ids[i]}"
                                    )
                                    air_conditioner_id = None

                        if i < len(work_detail_ids) and work_detail_ids[i]:
                            # 既存の作業内容を更新
                            work_detail = WorkDetail.query.get(work_detail_ids[i])
                            if work_detail:
                                work_detail.work_item_id = work_item_id
                                work_detail.work_item_text = work_item_text
                                work_detail.description = descriptions[i]
                                work_detail.confirmation = (
                                    confirmations[i] if i < len(confirmations) else ""
                                )
                                # エアコンIDの更新
                                work_detail.air_conditioner_id = air_conditioner_id
                                # 物件IDの更新 (常に物件IDを設定する)
                                work_detail.property_id = property_id
                        else:
                            # 新規作業内容を追加
                            work_detail = WorkDetail(
                                report_id=report.id,
                                property_id=property_id,  # 常に物件IDを設定
                                air_conditioner_id=air_conditioner_id,
                                work_item_id=work_item_id,
                                work_item_text=work_item_text,
                                description=descriptions[i],
                                confirmation=(
                                    confirmations[i] if i < len(confirmations) else ""
                                ),
                            )
                            db.session.add(work_detail)

                # 作業時間の変更に伴いスケジュールを更新
                update_schedule_from_work_times(
                    report, work_dates, start_times, end_times, property_id
                )

                # スケジュール更新後に報告書ステータスと同期
                sync_schedule_status_with_report(report)

                db.session.commit()
                flash("報告書情報とスケジュールが更新されました", "success")

                # current_tabパラメータを取得（デフォルトは'info'）
                current_tab = request.form.get("current_tab", "info")

                # データの詳細表示ページに戻るか、編集ページの特定のタブに戻るか判定
                if current_tab in ["photos", "times", "details"]:
                    # 編集ページの特定のタブに戻る
                    return redirect(
                        url_for("reports.edit", id=report.id, active_tab=current_tab)
                    )
                else:
                    # データの詳細表示ページに戻る
                    return redirect(url_for("reports.view", id=report.id))

        elif "upload_photo" in request.form:
            # 写真アップロード処理
            photo_type = request.form["photo_type"]
            photo_files = request.files.getlist("photos")
            caption = request.form.get("caption", "")
            room_name = request.form.get("room_name", "")
            air_conditioner_id = request.form.get("air_conditioner_id")
            work_item_id = request.form.get("work_item_id")

            # 値の検証（空文字列の場合はNoneに変換）
            if air_conditioner_id and air_conditioner_id.strip():
                try:
                    air_conditioner_id = int(air_conditioner_id)
                except (ValueError, TypeError):
                    air_conditioner_id = None
            else:
                air_conditioner_id = None

            if work_item_id and work_item_id.strip():
                try:
                    work_item_id = int(work_item_id)
                except (ValueError, TypeError):
                    work_item_id = None
            else:
                work_item_id = None

            uploaded_photos = []  # アップロードした写真のリストを保持

            # 関連情報の取得
            report_property = Property.query.get(report.property_id)
            customer = None
            air_conditioner = None
            work_item = None

            if report_property:
                customer = Customer.query.get(report_property.customer_id)

            if air_conditioner_id:
                air_conditioner = AirConditioner.query.get(air_conditioner_id)

            if work_item_id:
                work_item = WorkItem.query.get(work_item_id)

            for photo_file in photo_files:
                if photo_file and photo_file.filename:
                    filename = secure_filename(photo_file.filename)
                    # タイムスタンプを付与してファイル名の重複を避ける
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"{timestamp}_{filename}"

                    # 新しいフォルダ構造の構築（顧客>物件>エアコン>作業項目>作業日）
                    # ベースディレクトリは before または after から始まる
                    base_folder = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], photo_type
                    )

                    # 顧客フォルダ
                    customer_folder = "unknown_customer"
                    if customer:
                        customer_folder = secure_filename(customer.name)

                    # 物件フォルダ
                    property_folder = "unknown_property"
                    if report_property:
                        # 物件IDを追加して、同名物件でも区別できるようにする
                        property_folder = secure_filename(
                            f"{report_property.name}_{report_property.id}"
                        )
                        # 物件の住所も追加する（あれば）
                        if report_property.address:
                            # 住所が長すぎる場合は短縮する
                            address_part = secure_filename(report_property.address[:30])
                            property_folder = f"{property_folder}_{address_part}"

                    # エアコンフォルダ
                    air_conditioner_folder = "unknown_air_conditioner"
                    if air_conditioner:
                        # 製造元、型番、設置場所を組み合わせたフォルダ名
                        air_conditioner_info = []
                        if air_conditioner.manufacturer:
                            air_conditioner_info.append(air_conditioner.manufacturer)
                        if air_conditioner.model_number:
                            air_conditioner_info.append(air_conditioner.model_number)
                        if air_conditioner.location:
                            air_conditioner_info.append(f"({air_conditioner.location})")

                        if air_conditioner_info:
                            air_conditioner_folder = secure_filename(
                                "_".join(air_conditioner_info)
                            )
                        else:
                            air_conditioner_folder = f"aircon_{air_conditioner.id}"

                    # 作業項目フォルダ
                    work_item_folder = "unknown_work_item"
                    if work_item:
                        work_item_folder = secure_filename(work_item.name)

                    # 作業日フォルダ（報告書の日付を使用）
                    work_date_folder = "unknown_date"
                    if report.date:
                        work_date_folder = report.date.strftime("%Y%m%d")

                    # 完全なパスを構築
                    upload_path = os.path.join(
                        base_folder,
                        customer_folder,
                        property_folder,
                        air_conditioner_folder,
                        work_item_folder,
                        work_date_folder,
                    )

                    # ディレクトリが存在しない場合は作成
                    if not os.path.exists(upload_path):
                        os.makedirs(upload_path)

                    filepath = os.path.join(upload_path, filename)

                    # ファイル保存
                    photo_file.save(filepath)

                    # 相対パスを保存（uploads/before または uploads/after からの相対パス）
                    relative_path = os.path.join(
                        photo_type,
                        customer_folder,
                        property_folder,
                        air_conditioner_folder,
                        work_item_folder,
                        work_date_folder,
                        filename,
                    )

                    # データベースに写真情報を保存
                    photo = Photo(
                        report_id=id,
                        photo_type=photo_type,
                        filename=filename,
                        original_filename=photo_file.filename,
                        caption=caption,
                        room_name=room_name,
                        air_conditioner_id=air_conditioner_id,
                        work_item_id=work_item_id,
                        # ファイルパスの保存用に新たなフィールドを使用（もし存在すれば）
                        # このフィールドがない場合は、モデルに追加する必要があります
                        filepath=relative_path,
                    )
                    db.session.add(photo)
                    uploaded_photos.append(photo)

            db.session.commit()

            # 写真アップロード後はすべての写真を取得して表示する
            flash("写真がアップロードされました", "success")

            # 全写真を再取得する
            before_photos = Photo.query.filter_by(
                report_id=id, photo_type="before"
            ).all()
            after_photos = Photo.query.filter_by(report_id=id, photo_type="after").all()

            # 施工後写真の場合は次回用に施工前に戻し、エアコンと作業項目をクリアする
            # 施工前写真の場合は施工後に切り替え、エアコンと作業項目は引き継ぐ
            next_photo_type = "before" if photo_type == "after" else "after"

            # 施工前→施工後の場合はデータを引き継ぎ、施工後→施工前の場合は初期化
            if photo_type == "before":
                # 施工前→施工後の場合：データを引き継ぐ
                next_air_conditioner_id = (
                    int(air_conditioner_id) if air_conditioner_id is not None else None
                )
                next_work_item_id = (
                    int(work_item_id) if work_item_id is not None else None
                )
                print(
                    f"施工前→施工後: エアコンID {air_conditioner_id} -> {next_air_conditioner_id} (型: {type(next_air_conditioner_id)})"
                )
                print(
                    f"施工前→施工後: 作業項目ID {work_item_id} -> {next_work_item_id} (型: {type(next_work_item_id)})"
                )
            else:
                # 施工後→施工前の場合：データを初期化
                next_air_conditioner_id = None
                next_work_item_id = None
                print(
                    f"施工後→施工前: エアコンID {air_conditioner_id} -> {next_air_conditioner_id} (型: {type(next_air_conditioner_id)})"
                )
                print(
                    f"施工後→施工前: 作業項目ID {work_item_id} -> {next_work_item_id} (型: {type(next_work_item_id)})"
                )

            # デバッグ用ログ出力
            print(f"写真タイプ: {photo_type} -> {next_photo_type}")
            print(f"エアコンID: {air_conditioner_id} -> {next_air_conditioner_id}")
            print(f"作業項目ID: {work_item_id} -> {next_work_item_id}")

            # current_tabパラメータを取得して写真タブを表示するように設定
            print(
                f"テンプレートに渡す値: last_photo_type={next_photo_type}, last_air_conditioner_id={next_air_conditioner_id}, last_work_item_id={next_work_item_id}"
            )

            return render_template(
                "reports/edit.html",
                report=report,
                properties=properties,
                work_items=work_items,
                before_photos=before_photos,
                after_photos=after_photos,
                work_times=work_times,
                work_details=work_details,
                default_address=default_address,
                # 常に値を提供して未定義エラーを回避
                last_photo_type=next_photo_type,  # 次回の写真タイプを設定
                last_air_conditioner_id=next_air_conditioner_id,  # 次回のエアコンID
                last_work_item_id=next_work_item_id,  # 次回の作業項目ID
                active_tab="photos",  # 写真タブを選択状態にする
            )

    return render_template(
        "reports/edit.html",
        report=report,
        properties=properties,
        work_items=work_items,
        before_photos=before_photos,
        after_photos=after_photos,
        work_times=work_times,
        work_details=work_details,
        default_address=default_address,
        # 常に値を提供して未定義エラーを回避
        last_photo_type="before",  # デフォルトは施工前
        last_air_conditioner_id=None,  # デフォルトはNone
        last_work_item_id=None,  # デフォルトはNone
        # URLパラメータからactive_tabを取得
        active_tab=request.args.get(
            "active_tab"
        ),  # タブ情報がURLパラメータにある場合はそれを使用
    )


@bp.route("/work_items")
@login_required
def work_items():
    """作業項目一覧の表示と管理"""
    items = WorkItem.query.order_by(WorkItem.name).all()
    # 前のページのURLはback_urlクエリパラメータ、もしくはreferrerから取得
    back_url = request.args.get("back_url")
    if not back_url:
        back_url = request.referrer or url_for("reports.list")
    return render_template("reports/work_items.html", items=items, referer=back_url)


@bp.route("/work_items/add", methods=["POST"])
@login_required
def add_work_item():
    """作業項目の追加"""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    referer = request.form.get("referer", url_for("reports.work_items"))  # 戻り先URL

    if not name:
        flash("作業項目名は必須です", "danger")
        return redirect(url_for("reports.work_items", back_url=referer))

    # 既存項目の確認
    existing = WorkItem.query.filter_by(name=name).first()
    if existing:
        flash(f"「{name}」は既に登録されています", "warning")
        return redirect(url_for("reports.work_items", back_url=referer))

    # 新規作業項目を追加
    item = WorkItem(name=name, description=description, is_active=True)
    db.session.add(item)
    db.session.commit()

    flash(f"作業項目「{name}」を追加しました", "success")
    # 戻るボタンでrefererにリダイレクトできるよう、refererを維持しながらwork_itemsにリダイレクト
    return redirect(url_for("reports.work_items", back_url=referer))


@bp.route("/work_items/<int:id>/toggle", methods=["POST"])
@login_required
def toggle_work_item(id):
    """作業項目の有効/無効を切り替え"""
    item = WorkItem.query.get_or_404(id)
    referer = request.form.get("referer", url_for("reports.work_items"))  # 戻り先URL

    item.is_active = not item.is_active
    db.session.commit()

    status = "有効" if item.is_active else "無効"
    flash(f"作業項目「{item.name}」を{status}にしました", "success")
    # 戻るボタンでrefererにリダイレクトできるよう、refererを維持しながらwork_itemsにリダイレクト
    return redirect(url_for("reports.work_items", back_url=referer))


@bp.route("/work_items/<int:id>/delete", methods=["POST"])
@login_required
def delete_work_item(id):
    """作業項目の削除"""
    item = WorkItem.query.get_or_404(id)
    referer = request.form.get("referer", url_for("reports.work_items"))  # 戻り先URL

    # 作業項目が既に使用されているか確認
    work_details = WorkDetail.query.filter_by(work_item_id=id).first()
    if work_details:
        flash(
            f"作業項目「{item.name}」は既に使用されているため削除できません。無効化してください。",
            "warning",
        )
        return redirect(url_for("reports.work_items", back_url=referer))

    item_name = item.name
    db.session.delete(item)
    db.session.commit()

    flash(f"作業項目「{item_name}」を削除しました", "success")
    # 戻るボタンでrefererにリダイレクトできるよう、refererを維持しながらwork_itemsにリダイレクト
    return redirect(url_for("reports.work_items", back_url=referer))


@bp.route("/work_items/<int:id>/edit", methods=["POST"])
@login_required
def edit_work_item(id):
    """作業項目の編集"""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    referer = request.form.get("referer", url_for("reports.work_items"))  # 戻り先URL

    if not name:
        flash("作業項目名は必須です", "danger")
        return redirect(url_for("reports.work_items", back_url=referer))

    # 既存項目の確認（自分以外で同じ名前がないか）
    existing = WorkItem.query.filter(WorkItem.name == name, WorkItem.id != id).first()
    if existing:
        flash(f"「{name}」は既に登録されています", "warning")
        return redirect(url_for("reports.work_items", back_url=referer))

    # 作業項目を更新
    item = WorkItem.query.get_or_404(id)
    item.name = name
    item.description = description
    db.session.commit()

    flash(f"作業項目「{name}」を更新しました", "success")
    return redirect(referer)


@bp.route("/api/past_descriptions", methods=["GET"])
@login_required
def get_past_descriptions():
    """過去に入力した作業内容を検索して返すAPI"""
    search_term = request.args.get("term", "").strip()
    work_item_id = request.args.get("work_item_id")

    # 検索前のログ
    print(
        f"過去の作業内容検索リクエスト: 検索語='{search_term}', 作業項目ID={work_item_id}"
    )

    # 検索クエリの構築
    # distinct()の適用方法を変更し、より明示的なクエリを作成
    base_query = db.session.query(WorkDetail.description, WorkDetail.created_at)

    # 作業項目IDが指定されている場合は絞り込み
    if work_item_id and work_item_id != "other":
        base_query = base_query.filter(WorkDetail.work_item_id == work_item_id)

    # 検索語が指定されている場合は部分一致で絞り込み
    if search_term:
        base_query = base_query.filter(WorkDetail.description.ilike(f"%{search_term}%"))

    # 作成日の降順で並べ替え
    base_query = base_query.order_by(WorkDetail.created_at.desc())

    # 結果を取得
    raw_results = base_query.limit(20).all()

    # 重複排除（Pythonで実行）
    unique_descriptions = {}
    for description, created_at in raw_results:
        if description and description not in unique_descriptions:
            unique_descriptions[description] = created_at

    # 結果を整形（クエリの方式が変わったので整形方法も変更）
    descriptions = [
        {"id": i, "text": desc} for i, desc in enumerate(unique_descriptions.keys())
    ]

    # デバッグ用ロギング
    print(f"過去の作業内容検索結果: {len(descriptions)}件")
    for item in descriptions:
        print(f"  - {item['text'][:50]}...")

    return jsonify(descriptions)


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@delete_permission_required
def delete_report(id):
    """報告書と関連データの削除"""
    report = Report.query.get_or_404(id)

    try:
        # 関連スケジュールのステータスを「キャンセル」に更新（削除前に実行）
        related_schedules = Schedule.query.filter_by(report_id=report.id).all()
        for schedule in related_schedules:
            schedule.status = "cancelled"
            schedule.updated_at = datetime.now()
            # report_idはクリアして関連を断つ
            schedule.report_id = None
            print(
                f"スケジュール #{schedule.id} のステータスを「キャンセル」に更新しました"
            )

        # 関連する写真ファイルの削除
        photos = Photo.query.filter_by(report_id=id).all()
        for photo in photos:
            try:
                # ファイルパスを取得
                photo_path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"],
                    "before" if photo.photo_type == "before" else "after",
                    photo.filename,
                )

                # ファイルが存在する場合は削除
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"ファイル削除: {photo_path}")
            except Exception as e:
                print(f"写真ファイル削除エラー: {e}")

        # 関連データの削除（外部キー制約により、報告書を削除する前に関連データを削除する必要がある）
        # 写真データの削除
        Photo.query.filter_by(report_id=id).delete()

        # 作業時間データの削除
        WorkTime.query.filter_by(report_id=id).delete()

        # 作業内容データの削除
        WorkDetail.query.filter_by(report_id=id).delete()

        # 報告書自体の削除
        db.session.delete(report)

        # 変更をコミット
        db.session.commit()

        flash(
            "報告書とすべての関連データが削除されました。関連スケジュールはキャンセル状態に変更されました。",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        print(f"削除エラー: {e}")
        flash(f"報告書の削除中にエラーが発生しました: {e}", "danger")

    return redirect(url_for("reports.list"))


@bp.route("/api/properties/<int:property_id>/air_conditioners")
@login_required
@view_permission_required
def api_property_air_conditioners(property_id):
    """物件に紐づくエアコン一覧をJSON形式で返すAPI"""
    # 物件の存在チェック
    property = Property.query.get_or_404(property_id)

    # 物件に紐づくエアコン情報を取得
    air_conditioners = AirConditioner.query.filter_by(property_id=property_id).all()

    # JSONレスポンスを作成
    air_conditioner_list = []
    for ac in air_conditioners:
        air_conditioner_list.append(
            {
                "id": ac.id,
                "ac_type": ac.ac_type,
                "manufacturer": ac.manufacturer,
                "model_number": ac.model_number,
                "location": ac.location,
            }
        )

    # フロントエンドで期待されている形式（{'air_conditioners': [...]}）で返す
    return jsonify({"air_conditioners": air_conditioner_list})


@bp.route("/<int:report_id>/photos/<int:photo_id>/delete", methods=["POST"])
@login_required
@delete_permission_required
def delete_photo(report_id, photo_id):
    """報告書の写真を削除する"""
    # 指定された写真を取得
    photo = Photo.query.get_or_404(photo_id)

    # 写真が指定された報告書のものであることを確認
    if photo.report_id != report_id:
        flash("不正なリクエストです", "danger")
        return redirect(url_for("reports.edit", id=report_id, active_tab="photos"))

    try:
        # ファイルパスを取得
        photo_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            "before" if photo.photo_type == "before" else "after",
            photo.filename,
        )

        # ファイルが存在する場合は削除
        if os.path.exists(photo_path):
            os.remove(photo_path)
            print(f"ファイル削除: {photo_path}")

        # 写真データをデータベースから削除
        db.session.delete(photo)
        db.session.commit()

        flash("写真が削除されました", "success")
    except Exception as e:
        db.session.rollback()
        print(f"写真削除エラー: {e}")
        flash(f"写真の削除中にエラーが発生しました: {e}", "danger")

    return redirect(url_for("reports.edit", id=report_id, active_tab="photos"))


@bp.route("/<int:report_id>/photos/<int:photo_id>/edit", methods=["POST"])
@login_required
@edit_permission_required
def edit_photo(report_id, photo_id):
    """報告書の写真情報（キャプション、撮影場所）を編集する"""
    # 指定された写真を取得
    photo = Photo.query.get_or_404(photo_id)

    # 写真が指定された報告書のものであることを確認
    if photo.report_id != report_id:
        flash("不正なリクエストです", "danger")
        return redirect(url_for("reports.edit", id=report_id, active_tab="photos"))

    try:
        # フォームから新しい情報を取得
        new_caption = request.form.get("caption", "").strip()
        new_room_name = request.form.get("room_name", "").strip()

        # current_tabパラメータ取得（どこから来ても写真タブに戻す）
        current_tab = "photos"

        # 情報を更新
        photo.caption = new_caption
        photo.room_name = new_room_name
        db.session.commit()

        flash("写真情報が更新されました", "success")
    except Exception as e:
        db.session.rollback()
        print(f"写真情報更新エラー: {e}")
        flash(f"写真情報の更新中にエラーが発生しました: {e}", "danger")

    # 確実に写真タブにリダイレクト
    return redirect(url_for("reports.edit", id=report_id, active_tab="photos"))


@bp.route("/<int:id>/pdf")
@login_required
@view_permission_required
def download_pdf(id):
    """報告書のPDFをダウンロード"""
    report = Report.query.get_or_404(id)

    # 作業時間の取得
    work_times = (
        WorkTime.query.filter_by(report_id=id)
        .order_by(WorkTime.work_date, WorkTime.start_time)
        .all()
    )

    # 作業内容の取得
    work_details = WorkDetail.query.filter_by(report_id=id).all()

    # 施工前後の写真を取得
    before_photos = Photo.query.filter_by(report_id=id, photo_type="before").all()
    after_photos = Photo.query.filter_by(report_id=id, photo_type="after").all()

    # 写真ペアの作成
    photo_pairs = []
    # 最大枚数に合わせてループ
    max_photos = max(len(before_photos), len(after_photos))
    for i in range(max_photos):
        before_photo = before_photos[i] if i < len(before_photos) else None
        after_photo = after_photos[i] if i < len(after_photos) else None
        photo_pairs.append((before_photo, after_photo))

    # PDFをディスクに保存するかどうか
    save_to_disk = request.args.get("save", "0") == "1"

    # PDFサービスを使用してPDFを生成
    if save_to_disk:
        # ファイルを保存し、保存先を取得
        pdf_buffer, pdf_filepath = PDFService.generate_report_pdf(
            report, work_times, work_details, photo_pairs, save_to_disk=True
        )
        flash(f"PDFを保存しました: {pdf_filepath}", "success")
        # 保存だけで、ダウンロードはしない
        return redirect(url_for("reports.view", id=report.id))
    else:
        # ダウンロードする場合
        pdf_buffer = PDFService.generate_report_pdf(
            report, work_times, work_details, photo_pairs
        )

        # ファイル名の設定
        property_name = (
            report.property.name
            if report.property and report.property.name
            else "unknown"
        )
        customer_name = (
            report.property.customer.name
            if report.property
            and report.property.customer
            and report.property.customer.name
            else "unknown"
        )
        date_str = (
            report.date.strftime("%Y%m%d")
            if report.date
            else datetime.now().strftime("%Y%m%d")
        )

        filename = f"作業完了報告書_{customer_name}_{property_name}_{date_str}.pdf"
        filename = secure_filename(filename)

        # PDFをクライアントに送信
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf",
        )


@bp.route("/order-details")
@login_required
@view_permission_required
def order_details_list():
    """受注明細一覧画面表示（最新作業日ベースで時系列表示、重複防止）"""
    # パラメータの取得
    search = request.args.get("search", "").strip()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    sort_by = request.args.get("sort", "work_date")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # 各報告書の最新作業日を取得するサブクエリ
    latest_work_date_subquery = (
        db.session.query(
            WorkTime.report_id,
            db.func.max(WorkTime.work_date).label("latest_work_date"),
        )
        .group_by(WorkTime.report_id)
        .subquery()
    )

    # ベースクエリの作成（最新作業日のWorkTimeのみをJOIN）
    query = (
        Report.query.join(Property)
        .join(Customer)
        .outerjoin(WorkDetail, Report.id == WorkDetail.report_id)
        .join(
            latest_work_date_subquery,
            Report.id == latest_work_date_subquery.c.report_id,
        )
        .outerjoin(
            WorkTime,
            db.and_(
                Report.id == WorkTime.report_id,
                WorkTime.work_date == latest_work_date_subquery.c.latest_work_date,
            ),
        )
    )

    # 検索フィルタ
    if search:
        search_conditions = [
            Customer.name.contains(search),
            Property.name.contains(search),
            Property.reception_type.contains(search),
            Property.reception_detail.contains(search),
            WorkDetail.description.contains(search),
            # ステータスでの検索（英語コード）
            Report.status.contains(search),
        ]

        # 日本語ステータス検索
        search_lower = search.lower()
        if "未完了" in search_lower:
            search_conditions.append(Report.status == "pending")
        if "完了" in search_lower and "未完了" not in search_lower:
            search_conditions.append(Report.status == "completed")
        if "下書き" in search_lower:
            search_conditions.append(Report.status == "draft")
        if "キャンセル" in search_lower:
            search_conditions.append(Report.status == "cancelled")

        search_filter = or_(*search_conditions)
        query = query.filter(search_filter)

    # 期間フィルタ（最新作業日ベース）
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(
                latest_work_date_subquery.c.latest_work_date >= start_date_obj
            )
        except ValueError:
            pass

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(
                latest_work_date_subquery.c.latest_work_date <= end_date_obj
            )
        except ValueError:
            pass

    # 重複除去
    query = query.distinct()

    # ソート処理
    sort_column = None
    if sort_by == "id":
        sort_column = Report.id
    elif sort_by == "customer":
        sort_column = Customer.name
    elif sort_by == "property":
        sort_column = Property.name
    elif sort_by == "reception_type":
        sort_column = Property.reception_type
    elif sort_by == "work_date":
        sort_column = latest_work_date_subquery.c.latest_work_date
    elif sort_by == "date":
        sort_column = Report.date
    elif sort_by == "created_at":
        sort_column = Report.created_at
    else:
        sort_column = latest_work_date_subquery.c.latest_work_date

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # ページネーション
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items

    # 各報告書の詳細情報を取得
    order_details = []
    for report in reports:
        # 作業内容の総数（この報告書の）
        work_detail_count = WorkDetail.query.filter_by(report_id=report.id).count()

        # エアコンの数（この報告書で作業したエアコンのみ）
        ac_count = (
            db.session.query(
                db.func.count(db.func.distinct(WorkDetail.air_conditioner_id))
            )
            .filter(
                WorkDetail.report_id == report.id,
                WorkDetail.air_conditioner_id.isnot(None),
            )
            .scalar()
            or 0
        )

        # 金額の合計（この報告書で作業したエアコンのみ）
        total_amount = (
            db.session.query(db.func.sum(AirConditioner.total_amount))
            .join(WorkDetail, AirConditioner.id == WorkDetail.air_conditioner_id)
            .filter(WorkDetail.report_id == report.id)
            .scalar()
            or 0
        )

        # 作業日情報を取得（すべての作業日を表示用に取得）
        work_times = (
            WorkTime.query.filter_by(report_id=report.id)
            .order_by(WorkTime.work_date.asc())
            .all()
        )
        work_dates = [wt.work_date for wt in work_times]

        order_details.append(
            {
                "report": report,
                "property": report.property,
                "customer": report.property.customer,
                "work_detail_count": work_detail_count,
                "ac_count": ac_count,
                "total_amount": total_amount,
                "work_dates": work_dates,
            }
        )

    return render_template(
        "reports/order_details_list.html",
        order_details=order_details,
        pagination=pagination,
        current_search=search,
        current_start_date=start_date,
        current_end_date=end_date,
        current_sort=sort_by,
        current_order=order,
    )


@bp.route("/order-details/pdf")
@login_required
@view_permission_required
def order_details_pdf():
    """受注明細一覧PDF出力（最新作業日ベース、重複防止）"""
    # パラメータの取得（一覧画面と同じフィルタを適用）
    search = request.args.get("search", "").strip()
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    sort_by = request.args.get("sort", "work_date")
    order = request.args.get("order", "desc")

    # 各報告書の最新作業日を取得するサブクエリ
    latest_work_date_subquery = (
        db.session.query(
            WorkTime.report_id,
            db.func.max(WorkTime.work_date).label("latest_work_date"),
        )
        .group_by(WorkTime.report_id)
        .subquery()
    )

    # データ取得（ページネーションなし、最新作業日のWorkTimeのみをJOIN）
    query = (
        Report.query.join(Property)
        .join(Customer)
        .outerjoin(WorkDetail, Report.id == WorkDetail.report_id)
        .join(
            latest_work_date_subquery,
            Report.id == latest_work_date_subquery.c.report_id,
        )
        .outerjoin(
            WorkTime,
            db.and_(
                Report.id == WorkTime.report_id,
                WorkTime.work_date == latest_work_date_subquery.c.latest_work_date,
            ),
        )
    )

    # 同じフィルタ条件を適用
    if search:
        search_conditions = [
            Customer.name.contains(search),
            Property.name.contains(search),
            Property.reception_type.contains(search),
            Property.reception_detail.contains(search),
            WorkDetail.description.contains(search),
            # ステータスでの検索（英語コード）
            Report.status.contains(search),
        ]

        # 日本語ステータス検索
        search_lower = search.lower()
        if "未完了" in search_lower:
            search_conditions.append(Report.status == "pending")
        if "完了" in search_lower and "未完了" not in search_lower:
            search_conditions.append(Report.status == "completed")
        if "下書き" in search_lower:
            search_conditions.append(Report.status == "draft")
        if "キャンセル" in search_lower:
            search_conditions.append(Report.status == "cancelled")

        search_filter = or_(*search_conditions)
        query = query.filter(search_filter)

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(
                latest_work_date_subquery.c.latest_work_date >= start_date_obj
            )
        except ValueError:
            pass

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(
                latest_work_date_subquery.c.latest_work_date <= end_date_obj
            )
        except ValueError:
            pass

    # 重複除去とソート
    query = query.distinct()

    sort_column = None
    if sort_by == "id":
        sort_column = Report.id
    elif sort_by == "customer":
        sort_column = Customer.name
    elif sort_by == "property":
        sort_column = Property.name
    elif sort_by == "reception_type":
        sort_column = Property.reception_type
    elif sort_by == "work_date":
        sort_column = latest_work_date_subquery.c.latest_work_date
    elif sort_by == "date":
        sort_column = Report.date
    elif sort_by == "created_at":
        sort_column = Report.created_at
    else:
        sort_column = latest_work_date_subquery.c.latest_work_date

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    reports = query.all()

    # PDF作成
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)

    # 日本語フォントの登録
    try:
        # Windowsの場合
        pdfmetrics.registerFont(TTFont("Japanese", "C:/Windows/Fonts/msgothic.ttc"))
        japanese_font = "Japanese"
    except:
        try:
            # その他のフォント
            pdfmetrics.registerFont(
                TTFont("Japanese", "C:/Windows/Fonts/NotoSansCJK-Regular.ttc")
            )
            japanese_font = "Japanese"
        except:
            # フォントが見つからない場合はデフォルトを使用
            japanese_font = "Helvetica"

    # スタイル設定
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle", fontSize=16, alignment=1, spaceAfter=20, fontName=japanese_font
    )

    normal_style = ParagraphStyle("JapaneseNormal", fontSize=10, fontName=japanese_font)

    # PDFコンテンツ
    story = []

    # タイトル
    today = datetime.now().strftime("%Y年%m月%d日")
    title = f"受注明細一覧表　({today})"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))

    # 検索条件の表示
    if search or start_date or end_date:
        condition_text = "検索条件: "
        conditions = []
        if search:
            conditions.append(f"キーワード「{search}」")
        if start_date:
            conditions.append(f"開始日：{start_date}")
        if end_date:
            conditions.append(f"終了日：{end_date}")
        condition_text += " / ".join(conditions)
        story.append(Paragraph(condition_text, normal_style))
        story.append(Spacer(1, 10))

    # テーブルデータの準備
    data = [
        [
            "No.",
            "物件ID",
            "顧客名",
            "物件名",
            "受付種別",
            "AC数",
            "作業数",
            "金額",
            "報告日",
        ]
    ]

    # 合計計算用変数
    total_ac_count = 0
    total_work_count = 0
    total_amount_sum = 0

    for i, report in enumerate(reports, 1):
        # 作業内容の総数（この報告書の）
        work_detail_count = WorkDetail.query.filter_by(report_id=report.id).count()

        # エアコンの数（この報告書で作業したエアコンのみ）
        ac_count = (
            db.session.query(
                db.func.count(db.func.distinct(WorkDetail.air_conditioner_id))
            )
            .filter(
                WorkDetail.report_id == report.id,
                WorkDetail.air_conditioner_id.isnot(None),
            )
            .scalar()
            or 0
        )

        # 金額の合計（この報告書で作業したエアコンのみ）
        total_amount = (
            db.session.query(db.func.sum(AirConditioner.total_amount))
            .join(WorkDetail, AirConditioner.id == WorkDetail.air_conditioner_id)
            .filter(WorkDetail.report_id == report.id)
            .scalar()
            or 0
        )

        # 合計に加算
        total_ac_count += ac_count
        total_work_count += work_detail_count
        total_amount_sum += total_amount

        # 長いテキストを改行で折り返し
        customer_name = (
            report.property.customer.name if report.property.customer else ""
        )
        if len(customer_name) > 8:
            customer_name = customer_name[:8] + "\n" + customer_name[8:]

        property_name = report.property.name or ""
        if len(property_name) > 8:
            property_name = property_name[:8] + "\n" + property_name[8:]

        row = [
            str(i),
            str(report.property.id),
            customer_name,
            property_name,
            report.property.reception_type or "",
            str(ac_count),
            str(work_detail_count),
            f"¥{total_amount:,}" if total_amount else "¥0",
            report.date.strftime("%Y/%m/%d") if report.date else "",
        ]
        data.append(row)

    # 合計行を追加
    data.append(
        [
            "合計",
            "",
            "",
            "",
            "",
            str(total_ac_count),
            str(total_work_count),
            f"¥{total_amount_sum:,}",
            "",
        ]
    )

    # テーブル作成（A4サイズに収まるよう列幅を調整）
    table = Table(
        data,
        colWidths=[
            0.3 * inch,  # No.
            0.5 * inch,  # 物件ID
            0.9 * inch,  # 顧客名
            0.9 * inch,  # 物件名
            0.7 * inch,  # 受付種別
            0.7 * inch,  # エアコン数
            0.7 * inch,  # 作業台数
            0.9 * inch,  # 金額
            0.7 * inch,  # 報告日
        ],
        repeatRows=1,  # ヘッダー行を各ページで繰り返し
    )
    table.setStyle(
        TableStyle(
            [
                # ヘッダー行のスタイル
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), japanese_font),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # データ行のスタイル
                ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                ("FONTNAME", (0, 1), (-1, -2), japanese_font),
                ("FONTSIZE", (0, 1), (-1, -2), 8),
                # 合計行のスタイル
                ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, -1), (-1, -1), japanese_font),
                ("FONTSIZE", (0, -1), (-1, -1), 9),
                ("FONTWEIGHT", (0, -1), (-1, -1), "BOLD"),
                # 枠線
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                # 行の高さを調整（改行対応）
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.beige]),
            ]
        )
    )

    story.append(table)

    # 集計情報
    story.append(Spacer(1, 20))
    summary_text = f"合計件数: {len(reports)}件"
    story.append(Paragraph(summary_text, normal_style))

    # PDF生成
    doc.build(story)
    buffer.seek(0)

    # レスポンス作成
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f'attachment; filename=order_details_{today.replace("年", "").replace("月", "").replace("日", "")}.pdf'
    )

    return response
