from app import create_app, db
from app.models.work_detail import WorkDetail
from app.models.report import Report

app = create_app()

with app.app_context():
    # property_idがNULLの作業内容レコードを抽出
    null_property_records = WorkDetail.query.filter(
        WorkDetail.property_id.is_(None)
    ).all()

    count = 0
    for record in null_property_records:
        # レポートから物件IDを取得
        report = Report.query.get(record.report_id)
        if report:
            # 物件IDを設定
            record.property_id = report.property_id
            count += 1

    # 変更があれば保存
    if count > 0:
        db.session.commit()
        print(f"{count}件の作業内容レコードを修正しました。")
    else:
        print("修正が必要なレコードはありませんでした。")
