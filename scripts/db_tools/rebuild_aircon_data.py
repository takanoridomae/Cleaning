from app import create_app, db
from app.models.work_detail import WorkDetail
from app.models.air_conditioner import AirConditioner
from app.models.property import Property
import json

app = create_app()

with app.app_context():
    # エアコンと作業内容の関連を再構築

    # 1. 現在のエアコン情報をダンプ
    all_acs = AirConditioner.query.all()
    ac_data = []
    for ac in all_acs:
        ac_data.append(
            {
                "id": ac.id,
                "manufacturer": ac.manufacturer,
                "model_number": ac.model_number,
                "location": ac.location,
                "property_id": ac.property_id,
            }
        )

    # ダンプデータをファイルに保存
    with open("aircon_backup.json", "w") as f:
        json.dump(ac_data, f, indent=2)

    print(f"{len(ac_data)}件のエアコン情報をバックアップしました。")

    # 2. 作業内容データの修正
    work_details = WorkDetail.query.all()
    updated_count = 0

    print(f"{len(work_details)}件の作業内容を確認中...")

    for detail in work_details:
        if detail.air_conditioner_id:
            ac = AirConditioner.query.get(detail.air_conditioner_id)
            if ac:
                print(
                    f"作業内容ID: {detail.id}, エアコンID: {detail.air_conditioner_id}"
                )
                print(
                    f"  エアコン情報: {ac.manufacturer} {ac.model_number} ({ac.location})"
                )

                # 物件IDが正しく設定されているか確認
                if detail.property_id != ac.property_id:
                    print(
                        f"  物件ID不一致: 修正前={detail.property_id}, 修正後={ac.property_id}"
                    )
                    detail.property_id = ac.property_id
                    updated_count += 1

    if updated_count > 0:
        print(f"{updated_count}件の作業内容を修正しました。")
        db.session.commit()
    else:
        print("修正が必要なレコードはありませんでした。")

    # 3. 作業内容のエアコンIDが正しいか確認
    print("\nエアコンID確認：")
    for detail in work_details:
        if detail.air_conditioner_id:
            ac = AirConditioner.query.get(detail.air_conditioner_id)
            if ac:
                print(
                    f"作業内容ID: {detail.id}, エアコンID: {detail.air_conditioner_id}, エアコン: {ac.manufacturer} {ac.model_number}"
                )
            else:
                print(
                    f"作業内容ID: {detail.id}, エアコンID: {detail.air_conditioner_id} - 存在しないエアコンIDです"
                )

    print("\n処理が完了しました。")
