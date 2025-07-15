#!/usr/bin/env python3
"""
PDF生成パフォーマンステスト用スクリプト
大量の写真を持つレポートでPDF生成時間を測定する
"""

import os
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app, db
from app.models.report import Report
from app.models.photo import Photo
from app.services.pdf_service import PDFService


def test_pdf_generation():
    """PDF生成のパフォーマンステスト"""
    app = create_app()

    with app.app_context():
        print("=== PDF生成パフォーマンステスト ===")
        print(f"テスト開始時刻: {datetime.now()}")

        # 写真が多いレポートを検索
        reports_with_photos = db.session.query(Report).join(Photo).all()

        if not reports_with_photos:
            print("写真付きのレポートが見つかりません")
            return

        # 写真数でソートして最も写真が多いレポートを選択
        target_report = None
        max_photos = 0

        for report in reports_with_photos:
            photo_count = len(report.photos)
            if photo_count > max_photos:
                max_photos = photo_count
                target_report = report

        if not target_report:
            print("テスト対象のレポートが見つかりません")
            return

        print(f"テスト対象レポート: ID {target_report.id}")
        print(f"写真数: {max_photos} 枚")

        # PDF生成データを準備
        work_times = target_report.work_times
        work_details = target_report.work_details

        # 写真ペアを作成
        photo_pairs = []
        before_photos = [p for p in target_report.photos if p.type == "before"]
        after_photos = [p for p in target_report.photos if p.type == "after"]

        for i in range(max(len(before_photos), len(after_photos))):
            before = before_photos[i] if i < len(before_photos) else None
            after = after_photos[i] if i < len(after_photos) else None
            photo_pairs.append((before, after))

        print(f"写真ペア数: {len(photo_pairs)}")

        # PDF生成の実行時間を測定
        start_time = time.time()

        try:
            pdf_buffer = PDFService.generate_report_pdf(
                target_report, work_times, work_details, photo_pairs
            )

            end_time = time.time()
            generation_time = end_time - start_time

            print(f"PDF生成成功!")
            print(f"生成時間: {generation_time:.2f} 秒")
            print(f"PDFサイズ: {len(pdf_buffer.getvalue()) / 1024 / 1024:.2f} MB")

            # 1分半（90秒）以下なら成功
            if generation_time < 90:
                print("✅ パフォーマンステスト合格 (90秒以下)")
            else:
                print("⚠️  パフォーマンス改善が必要 (90秒超過)")

        except Exception as e:
            end_time = time.time()
            generation_time = end_time - start_time
            print(f"❌ PDF生成エラー: {e}")
            print(f"エラー発生までの時間: {generation_time:.2f} 秒")

        print(f"テスト終了時刻: {datetime.now()}")


if __name__ == "__main__":
    test_pdf_generation()
