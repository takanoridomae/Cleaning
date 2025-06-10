from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models.schedule import Schedule
from app.models.customer import Customer
from app.models.property import Property
from app.models.report import Report
from app import db
from app.routes.auth import (
    login_required,
    view_permission_required,
    edit_permission_required,
    create_permission_required,
    delete_permission_required,
)
from sqlalchemy import or_, and_
from datetime import datetime, date, timedelta
import calendar

bp = Blueprint("schedules", __name__, url_prefix="/schedules")


@bp.route("/")
@login_required
@view_permission_required
def list():
    """スケジュール一覧画面表示（月表示）"""
    # パラメータの取得
    view_type = request.args.get("view", "month")  # month, week, list
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    week_start = request.args.get("week_start")  # 週表示用の開始日（YYYY-MM-DD形式）
    status_filter = request.args.get("status", "all")  # all, pending, completed

    # 表示期間の計算
    if view_type == "month":
        # 月表示の場合
        start_date = date(year, month, 1)
        # 月末日を取得
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)
    elif view_type == "week":
        # 週表示の場合
        if week_start:
            # パラメータで指定された週の開始日を使用
            start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        else:
            # 今週の月曜日を取得
            today = date.today()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        # 週間ナビゲーション用の前週・次週計算
        prev_week_start = start_date - timedelta(days=7)
        next_week_start = start_date + timedelta(days=7)
    else:
        # リスト表示の場合（今月）
        start_date = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)

    # クエリ構築
    query = Schedule.query.filter(
        and_(
            Schedule.start_datetime
            >= datetime.combine(start_date, datetime.min.time()),
            Schedule.start_datetime <= datetime.combine(end_date, datetime.max.time()),
        )
    )

    # ステータスフィルタ
    if status_filter != "all":
        query = query.filter(Schedule.status == status_filter)

    # 並び替え
    schedules = query.order_by(Schedule.start_datetime.asc()).all()

    # 週表示用のデータ構造を作成
    week_data = {}
    if view_type == "week":
        # 7日間の日付リストを作成
        week_dates = []
        for i in range(7):
            date_obj = start_date + timedelta(days=i)
            week_dates.append(date_obj)
            week_data[date_obj] = []

        # スケジュールを日付ごとに分類
        for schedule in schedules:
            schedule_date = schedule.start_datetime.date()
            if schedule_date in week_data:
                week_data[schedule_date].append(schedule)

    # ナビゲーション用の前月・次月計算
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    template_data = {
        "schedules": schedules,
        "view_type": view_type,
        "current_year": year,
        "current_month": month,
        "current_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }

    # 週表示用の追加データ
    if view_type == "week":
        template_data.update(
            {
                "week_dates": week_dates,
                "week_data": week_data,
                "prev_week_start": prev_week_start,
                "next_week_start": next_week_start,
            }
        )

    return render_template("schedules/list.html", **template_data)


@bp.route("/create", methods=("GET", "POST"))
@login_required
@create_permission_required
def create():
    """新規スケジュール作成"""
    customers = Customer.query.order_by(Customer.name).all()
    properties = (
        Property.query.join(Customer).order_by(Customer.name, Property.name).all()
    )
    # 報告書一覧を取得（IDの降順で表示）
    reports = (
        Report.query.join(Property).join(Customer).order_by(Report.id.desc()).all()
    )

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        start_date = request.form["start_date"]
        start_time = request.form.get("start_time", "09:00")
        end_date = request.form.get("end_date", start_date)
        end_time = request.form.get("end_time", "18:00")
        all_day = request.form.get("all_day") == "on"
        priority = request.form.get("priority", "normal")
        customer_id = request.form.get("customer_id") or None
        property_id = request.form.get("property_id") or None
        report_id = request.form.get("report_id") or None

        # 通知設定
        notification_enabled = request.form.get("notification_enabled") == "on"
        notification_minutes = int(request.form.get("notification_minutes", 30))

        error = None

        # 入力検証
        if not title:
            error = "タイトルは必須です"

        if not start_date:
            error = "開始日は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            try:
                # 日時の結合
                if all_day:
                    start_datetime = datetime.combine(
                        datetime.strptime(start_date, "%Y-%m-%d").date(),
                        datetime.min.time(),
                    )
                    end_datetime = datetime.combine(
                        datetime.strptime(end_date, "%Y-%m-%d").date(),
                        datetime.max.time(),
                    )
                else:
                    start_datetime = datetime.strptime(
                        f"{start_date} {start_time}", "%Y-%m-%d %H:%M"
                    )
                    end_datetime = datetime.strptime(
                        f"{end_date} {end_time}", "%Y-%m-%d %H:%M"
                    )

                # スケジュール作成
                schedule = Schedule(
                    title=title,
                    description=description,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    all_day=all_day,
                    priority=priority,
                    customer_id=int(customer_id) if customer_id else None,
                    property_id=int(property_id) if property_id else None,
                    report_id=int(report_id) if report_id else None,
                    status="pending",
                    notification_enabled=notification_enabled,
                    notification_minutes=notification_minutes,
                    created_by=g.user.id,
                )

                db.session.add(schedule)
                db.session.commit()
                flash("スケジュールが作成されました", "success")
                return redirect(url_for("schedules.list"))

            except ValueError as e:
                flash(f"日時の形式が正しくありません: {e}", "danger")
            except Exception as e:
                flash(f"スケジュールの作成中にエラーが発生しました: {e}", "danger")

    return render_template(
        "schedules/create.html",
        customers=customers,
        properties=properties,
        reports=reports,
    )


@bp.route("/<int:id>")
@login_required
@view_permission_required
def view(id):
    """スケジュール詳細表示"""
    schedule = Schedule.query.get_or_404(id)
    return render_template("schedules/view.html", schedule=schedule)


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
@edit_permission_required
def edit(id):
    """スケジュール編集"""
    schedule = Schedule.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    properties = (
        Property.query.join(Customer).order_by(Customer.name, Property.name).all()
    )
    # 報告書一覧を取得（IDの降順で表示）
    reports = (
        Report.query.join(Property).join(Customer).order_by(Report.id.desc()).all()
    )

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "")
        start_date = request.form["start_date"]
        start_time = request.form.get("start_time", "09:00")
        end_date = request.form.get("end_date", start_date)
        end_time = request.form.get("end_time", "18:00")
        all_day = request.form.get("all_day") == "on"
        priority = request.form.get("priority", "normal")
        status = request.form.get("status", "pending")
        customer_id = request.form.get("customer_id") or None
        property_id = request.form.get("property_id") or None
        report_id = request.form.get("report_id") or None

        # 通知設定
        notification_enabled = request.form.get("notification_enabled") == "on"
        notification_minutes = int(request.form.get("notification_minutes", 30))

        error = None

        # 入力検証
        if not title:
            error = "タイトルは必須です"

        if not start_date:
            error = "開始日は必須です"

        if error is not None:
            flash(error, "danger")
        else:
            try:
                # 日時の結合
                if all_day:
                    start_datetime = datetime.combine(
                        datetime.strptime(start_date, "%Y-%m-%d").date(),
                        datetime.min.time(),
                    )
                    end_datetime = datetime.combine(
                        datetime.strptime(end_date, "%Y-%m-%d").date(),
                        datetime.max.time(),
                    )
                else:
                    start_datetime = datetime.strptime(
                        f"{start_date} {start_time}", "%Y-%m-%d %H:%M"
                    )
                    end_datetime = datetime.strptime(
                        f"{end_date} {end_time}", "%Y-%m-%d %H:%M"
                    )

                # スケジュール更新
                schedule.title = title
                schedule.description = description
                schedule.start_datetime = start_datetime
                schedule.end_datetime = end_datetime
                schedule.all_day = all_day
                schedule.priority = priority
                schedule.status = status
                schedule.customer_id = int(customer_id) if customer_id else None
                schedule.property_id = int(property_id) if property_id else None
                schedule.report_id = int(report_id) if report_id else None
                schedule.notification_enabled = notification_enabled
                schedule.notification_minutes = notification_minutes

                db.session.commit()
                flash("スケジュールが更新されました", "success")
                return redirect(url_for("schedules.view", id=schedule.id))

            except ValueError as e:
                flash(f"日時の形式が正しくありません: {e}", "danger")
            except Exception as e:
                flash(f"スケジュールの更新中にエラーが発生しました: {e}", "danger")

    return render_template(
        "schedules/edit.html",
        schedule=schedule,
        customers=customers,
        properties=properties,
        reports=reports,
    )


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@delete_permission_required
def delete(id):
    """スケジュール削除"""
    schedule = Schedule.query.get_or_404(id)

    try:
        title = schedule.title
        db.session.delete(schedule)
        db.session.commit()
        flash(f"スケジュール「{title}」が削除されました", "success")
    except Exception as e:
        flash(f"スケジュールの削除中にエラーが発生しました: {e}", "danger")

    return redirect(url_for("schedules.list"))


@bp.route("/<int:id>/complete", methods=["POST"])
@login_required
@edit_permission_required
def complete(id):
    """スケジュール完了"""
    schedule = Schedule.query.get_or_404(id)

    try:
        schedule.status = "completed"
        db.session.commit()
        flash(f"スケジュール「{schedule.title}」を完了しました", "success")
    except Exception as e:
        flash(f"ステータス更新中にエラーが発生しました: {e}", "danger")

    return redirect(url_for("schedules.list"))


@bp.route("/api/move", methods=["POST"])
@login_required
@edit_permission_required
def move_schedule():
    """ドラッグ&ドロップによるスケジュール移動処理"""
    try:
        data = request.get_json()
        schedule_id = data.get("schedule_id")
        new_date = data.get("new_date")  # YYYY-MM-DD形式

        if not schedule_id or not new_date:
            return jsonify({"error": "schedule_idとnew_dateは必須です"}), 400

        # スケジュールを取得
        schedule = Schedule.query.get_or_404(schedule_id)
        original_date = schedule.start_datetime.date()

        # 新しい日付をパース
        try:
            new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "日付の形式が正しくありません"}), 400

        # 日付が変更されない場合は何もしない
        if original_date == new_date_obj:
            return jsonify({"message": "日付に変更がありません"}), 200

        # 時間は変更せず、日付のみ変更
        original_start_time = schedule.start_datetime.time()
        original_end_time = schedule.end_datetime.time()

        new_start_datetime = datetime.combine(new_date_obj, original_start_time)
        new_end_datetime = datetime.combine(new_date_obj, original_end_time)

        # スケジュールの日時を更新
        schedule.start_datetime = new_start_datetime
        schedule.end_datetime = new_end_datetime

        # 関連する報告書の作業日も同期更新
        if schedule.report_id:
            # 関連する報告書の作業時間を更新
            from app.models.work_time import WorkTime

            work_times = WorkTime.query.filter_by(report_id=schedule.report_id).all()

            # 移動元の日付と一致する作業時間を新しい日付に更新
            for work_time in work_times:
                if work_time.work_date == original_date:
                    work_time.work_date = new_date_obj
                    print(
                        f"作業時間ID {work_time.id}: {original_date} -> {new_date_obj} に更新"
                    )

            # 報告書の基本日付も最初の作業日に合わせて更新
            if work_times:
                report = schedule.report
                earliest_work_date = min(wt.work_date for wt in work_times)
                if report.date != earliest_work_date:
                    print(
                        f"報告書ID {report.id}: 基本日付を {report.date} -> {earliest_work_date} に更新"
                    )
                    report.date = earliest_work_date

        db.session.commit()

        return (
            jsonify(
                {
                    "message": "スケジュールを移動しました",
                    "schedule": {
                        "id": schedule.id,
                        "title": schedule.title,
                        "start_datetime": schedule.start_datetime.isoformat(),
                        "end_datetime": schedule.end_datetime.isoformat(),
                        "original_date": original_date.isoformat(),
                        "new_date": new_date_obj.isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        print(f"スケジュール移動エラー: {e}")
        return (
            jsonify({"error": f"スケジュールの移動中にエラーが発生しました: {str(e)}"}),
            500,
        )


@bp.route("/api/events")
@login_required
@view_permission_required
def api_events():
    """カレンダー表示用のイベントデータを返すAPI"""
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    status_filter = request.args.get("status", "all")  # ステータスフィルタを追加

    if start_date and end_date:
        try:
            # 日付パースの改善（無効な日付を修正）
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

            # 月末日の場合は適切な日付に修正
            end_year, end_month, end_day = map(int, end_date.split("-"))
            max_day = calendar.monthrange(end_year, end_month)[1]
            if end_day > max_day:
                end_day = max_day
            end_dt = datetime(end_year, end_month, end_day, 23, 59, 59)

        except ValueError:
            # フォールバック：現在月のデータを取得
            now = datetime.now()
            start_dt = datetime(now.year, now.month, 1)
            end_dt = datetime(
                now.year,
                now.month,
                calendar.monthrange(now.year, now.month)[1],
                23,
                59,
                59,
            )

        # 基本的な日付フィルタ
        query = Schedule.query.filter(
            and_(Schedule.start_datetime >= start_dt, Schedule.start_datetime <= end_dt)
        )

        # ステータスフィルタを追加
        if status_filter != "all":
            query = query.filter(Schedule.status == status_filter)

        schedules = query.all()
    else:
        query = Schedule.query
        # ステータスフィルタを追加
        if status_filter != "all":
            query = query.filter(Schedule.status == status_filter)
        schedules = query.all()

    events = []
    for schedule in schedules:
        # ステータスに応じた色設定
        color_map = {
            "pending": "#ffc107",  # 黄色（警告）
            "completed": "#28a745",  # 緑色（成功）
            "cancelled": "#6c757d",  # 灰色（無効）
        }

        events.append(
            {
                "id": schedule.id,
                "title": schedule.title,
                "start": schedule.start_datetime.isoformat(),
                "end": schedule.end_datetime.isoformat(),
                "allDay": schedule.all_day,
                "backgroundColor": color_map.get(schedule.status, "#007bff"),
                "borderColor": color_map.get(schedule.status, "#007bff"),
                "extendedProps": {
                    "status": schedule.status,
                    "priority": schedule.priority,
                    "description": schedule.description,
                    "customer_name": (
                        schedule.customer.name if schedule.customer else None
                    ),
                    "property_name": (
                        schedule.schedule_property.name
                        if schedule.schedule_property
                        else None
                    ),
                },
            }
        )

    return jsonify(events)
