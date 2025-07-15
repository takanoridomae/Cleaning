import os
import tempfile
import re
from io import BytesIO
from flask import render_template, current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from datetime import datetime
from werkzeug.utils import secure_filename
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image as PILImage


def sanitize_filename(filename):
    """ファイル名に使用できない文字を除去する（日本語は保持）"""
    # Windowsのファイル名に使用できない文字を削除
    invalid_chars = r'[\\/:*?"<>|]'
    return re.sub(invalid_chars, "", filename)


def fix_image_orientation(image_path):
    """
    画像のEXIF情報を読み取り、正しい向きに回転させる（最適化版）

    Args:
        image_path (str): 画像ファイルのパス

    Returns:
        PIL.Image: 正しい向きに回転された画像オブジェクト
    """
    try:
        # PILで画像を開く
        image = PILImage.open(image_path)

        # 高速化のため、大きすぎる画像は事前に縮小
        if image.size[0] > 2000 or image.size[1] > 2000:
            image.thumbnail((2000, 2000), PILImage.Resampling.LANCZOS)

        # EXIF情報を取得
        exif = image._getexif()

        if exif is not None:
            # Orientation情報を取得（EXIF tag 274）
            orientation = exif.get(274)  # 274はOrientationのタグ番号

            # Orientationに基づいて画像を回転
            if orientation == 2:
                # 水平反転
                image = image.transpose(PILImage.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                # 180度回転
                image = image.rotate(180, expand=True)
            elif orientation == 4:
                # 垂直反転
                image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                # 90度反時計回りに回転 + 水平反転
                image = image.rotate(-90, expand=True).transpose(
                    PILImage.FLIP_LEFT_RIGHT
                )
            elif orientation == 6:
                # 90度時計回りに回転
                image = image.rotate(-90, expand=True)
            elif orientation == 7:
                # 90度時計回りに回転 + 水平反転
                image = image.rotate(90, expand=True).transpose(
                    PILImage.FLIP_LEFT_RIGHT
                )
            elif orientation == 8:
                # 90度反時計回りに回転
                image = image.rotate(90, expand=True)

        return image

    except Exception as e:
        print(f"画像の向き修正エラー: {e}")
        # エラーの場合は元の画像をそのまま返す
        try:
            image = PILImage.open(image_path)
            # エラー時も縮小して負荷軽減
            if image.size[0] > 2000 or image.size[1] > 2000:
                image.thumbnail((2000, 2000), PILImage.Resampling.LANCZOS)
            return image
        except:
            # 最悪の場合は空の画像を返す
            return PILImage.new("RGB", (100, 100), color="white")


class PDFService:
    """PDFを生成するためのサービス"""

    @staticmethod
    def generate_report_pdf(
        report, work_times, work_details, photo_pairs, save_to_disk=False
    ):
        """
        報告書のPDFを生成する

        Args:
            report (Report): 報告書オブジェクト
            work_times (list): 作業時間のリスト
            work_details (list): 作業内容のリスト
            photo_pairs (list): 写真ペアのリスト
            save_to_disk (bool): ディスクに保存するかどうか

        Returns:
            BytesIO: PDF形式のバイトデータ
            str: 保存されたPDFのパス（save_to_diskがTrueの場合）
        """
        # PDF用のバッファを作成
        buffer = BytesIO()

        # PDFドキュメントを作成
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            title=f"作業完了書_{report.id}",
            author="エアコンクリーニング完了報告書システム",
        )

        # 日本語フォントの登録（UnicodeCIDFont）
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

        # スタイルを設定
        styles = getSampleStyleSheet()
        # 日本語スタイルを追加
        styles.add(
            ParagraphStyle(
                name="JapaneseNormal",
                fontName="HeiseiKakuGo-W5",
                fontSize=10,
                leading=12,
                firstLineIndent=0,
                alignment=4,  # 4=左揃え
            )
        )

        styles.add(
            ParagraphStyle(
                name="JapaneseHeading1",
                parent=styles["Heading1"],
                fontName="HeiseiKakuGo-W5",
                fontSize=16,
                leading=18,
            )
        )

        styles.add(
            ParagraphStyle(
                name="JapaneseHeading2",
                parent=styles["Heading2"],
                fontName="HeiseiKakuGo-W5",
                fontSize=14,
                leading=16,
            )
        )

        styles.add(
            ParagraphStyle(
                name="JapaneseHeading3",
                parent=styles["Heading3"],
                fontName="HeiseiKakuGo-W5",
                fontSize=12,
                leading=14,
            )
        )

        # 写真セット間の区切り線スタイルを追加
        styles.add(
            ParagraphStyle(
                name="JapaneseDivider",
                fontName="HeiseiKakuGo-W5",
                fontSize=1,
                leading=1,
                spaceBefore=3,
                spaceAfter=3,
                alignment=1,  # 中央揃え
            )
        )

        # エアコン情報用のスタイル（余白を減らす）
        styles.add(
            ParagraphStyle(
                name="JapaneseAcInfo",
                parent=styles["JapaneseNormal"],
                fontName="HeiseiKakuGo-W5",
                fontSize=8,  # フォントサイズをさらに小さく
                leading=9,  # リーディングを縮小
                spaceAfter=0,  # 余白をなくす
            )
        )

        # タイトル部分のスタイルを変更
        styles.add(
            ParagraphStyle(
                name="JapaneseTitle",
                fontName="HeiseiKakuGo-W5",
                fontSize=14,  # タイトルのフォントサイズを小さくする
                leading=16,
                alignment=0,  # 左揃え
            )
        )

        styles.add(
            ParagraphStyle(
                name="JapaneseIdText",
                fontName="HeiseiKakuGo-W5",
                fontSize=11,  # IDテキストのフォントサイズをさらに小さく
                leading=13,
                alignment=2,  # 右揃え
                underline=True,  # 下線を追加
            )
        )

        # 写真セット用のスタイル
        styles.add(
            ParagraphStyle(
                name="JapanesePhotoCaption",
                parent=styles["JapaneseHeading3"],
                fontName="HeiseiKakuGo-W5",
                fontSize=12,  # フォントサイズを少し大きく
                leading=14,  # リーディングを調整
                spaceAfter=3,  # 写真キャプションの下部余白を調整
                alignment=1,  # 中央揃え
                textColor=colors.darkblue,  # 色を追加
            )
        )

        # 写真セット間の区切り線用関数
        def create_divider():
            return [
                Spacer(1, 10),  # 上部スペースを増やす
                Table(
                    [[""]],
                    colWidths=[500],  # 幅を広げる
                    rowHeights=[2],  # 線の太さを少し太くする
                ).setStyle(
                    TableStyle(
                        [
                            # より濃いグレーの線でエレガントな区切り
                            ("LINEABOVE", (0, 0), (0, 0), 1.0, colors.grey),
                        ]
                    )
                ),
                Spacer(1, 12),  # 下部スペースを増やす
            ]

        # ドキュメントの要素を格納するリスト
        elements = []

        # タイトルをテーブルで構成して左右の配置を調整
        title_table_data = [
            [
                Paragraph("作業完了報告書", styles["JapaneseTitle"]),
                Paragraph(f"ID: {report.id}", styles["JapaneseIdText"]),
            ]
        ]

        title_table = Table(title_table_data, colWidths=[300, 200])
        title_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    (
                        "LINEBELOW",
                        (1, 0),
                        (1, 0),
                        0.5,
                        colors.black,
                    ),  # IDの下に線を引く
                ]
            )
        )

        elements.append(title_table)
        elements.append(Spacer(1, 12))

        # 基本情報
        # 顧客名と会社名を組み合わせて表示
        if report.property and report.property.customer:
            customer_name = report.property.customer.name
            company_name = report.property.customer.company_name
            if company_name:
                property_name = f"{customer_name}（{company_name}）"
            else:
                property_name = customer_name
        else:
            property_name = "不明"

        address = report.work_address or (
            report.property.address if report.property else ""
        )

        # 報告者情報
        elements.append(Paragraph("＜報告者＞", styles["JapaneseHeading2"]))
        reporter_data = [
            ["報告者", "クリーンアップ"],
            ["連絡先", "〒635-0814 奈良県北葛城郡広陵町南郷１０５７－５"],
            ["担当者", "植田"],
            ["TEL", "０８０－４６４６－２２６６"],
        ]
        reporter_table = Table(reporter_data, colWidths=[100, 400])
        reporter_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(reporter_table)
        elements.append(Spacer(1, 12))

        # 顧客・物件情報
        elements.append(Paragraph("＜顧客情報＞", styles["JapaneseHeading2"]))
        customer_data = [
            ["お客様", property_name],
            ["作業場所", report.property.name if report.property else "不明"],
            ["住所", address],
        ]

        # 案件詳細の基本情報の備考がある場合は追加
        if report.property and report.property.note:
            property_note_para = Paragraph(
                report.property.note, styles["JapaneseNormal"]
            )
            customer_data.append(["備考", property_note_para])

        customer_table = Table(customer_data, colWidths=[100, 400])
        customer_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("WORDWRAP", (0, 0), (-1, -1), True),  # テキスト折り返しを有効化
                ]
            )
        )
        elements.append(customer_table)
        elements.append(Spacer(1, 12))

        # 作業日時
        elements.append(Paragraph("＜作業日時＞", styles["JapaneseHeading2"]))
        if work_times:
            work_time_data = [["日付", "開始時間", "終了時間", "備考"]]
            for work_time in work_times:
                # 備考をParagraphオブジェクトに変換して折り返しを確実にする
                note_para = Paragraph(work_time.note or "", styles["JapaneseNormal"])

                work_time_data.append(
                    [
                        (
                            work_time.work_date.strftime("%Y-%m-%d")
                            if work_time.work_date
                            else ""
                        ),
                        (
                            work_time.start_time.strftime("%H:%M")
                            if work_time.start_time
                            else ""
                        ),
                        (
                            work_time.end_time.strftime("%H:%M")
                            if work_time.end_time
                            else ""
                        ),
                        note_para,
                    ]
                )
            # カラム幅を調整（日付、開始時間、終了時間は固定幅、備考は広く取る）
            work_time_table = Table(
                work_time_data,
                colWidths=[80, 60, 60, 300],
                rowHeights=[25]
                + [None]
                * (len(work_time_data) - 1),  # ヘッダー行は25px、データ行は自動調整
            )
            work_time_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        (
                            "WORDWRAP",
                            (0, 0),
                            (-1, -1),
                            True,
                        ),  # すべてのセルでテキスト折り返しを有効化
                    ]
                )
            )
            elements.append(work_time_table)
        else:
            elements.append(Paragraph("作業日時情報なし", styles["JapaneseNormal"]))
        elements.append(Spacer(1, 12))

        # 作業内容
        elements.append(Paragraph("＜作業内容＞", styles["JapaneseHeading2"]))
        if work_details:
            # ヘッダー行もParagraphオブジェクトに変換
            header_style = ParagraphStyle(
                name="JapaneseTableHeader",
                parent=styles["JapaneseNormal"],
                fontName="HeiseiKakuGo-W5",
                fontSize=10,
                alignment=4,  # 左揃え
            )
            work_detail_data = [
                [
                    Paragraph("エアコン情報", header_style),
                    Paragraph("作業項目", header_style),
                    Paragraph("内容", header_style),
                    Paragraph("確認", header_style),
                ]
            ]

            for detail in work_details:
                work_item_name = ""
                if detail.work_item:
                    work_item_name = detail.work_item.name
                elif detail.work_item_text:
                    work_item_name = detail.work_item_text

                # エアコン情報を取得
                ac_info = ""
                if detail.air_conditioner:
                    ac_info = f"{detail.air_conditioner.manufacturer or ''} {detail.air_conditioner.model_number or ''}"
                    if detail.air_conditioner.location:
                        ac_info += f"（{detail.air_conditioner.location}）"

                # テキストをParagraphオブジェクトに変換して折り返しを確実にする
                ac_info_para = Paragraph(ac_info, styles["JapaneseNormal"])
                work_item_para = Paragraph(work_item_name, styles["JapaneseNormal"])
                description_para = Paragraph(
                    detail.description or "", styles["JapaneseNormal"]
                )
                confirmation_para = Paragraph(
                    detail.confirmation or "", styles["JapaneseNormal"]
                )

                work_detail_data.append(
                    [
                        ac_info_para,
                        work_item_para,
                        description_para,
                        confirmation_para,
                    ]
                )
            # 列幅を調整（エアコン情報を広く、確認を狭く）
            work_detail_table = Table(
                work_detail_data,
                colWidths=[130, 90, 210, 70],
                rowHeights=[25]
                + [None]
                * (
                    len(work_detail_data) - 1
                ),  # ヘッダー行は25px、データ行は自動調整（コンテンツに合わせる）
            )
            work_detail_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        (
                            "WORDWRAP",
                            (0, 0),
                            (-1, -1),
                            True,
                        ),  # すべてのセルでテキスト折り返しを有効化
                    ]
                )
            )
            elements.append(work_detail_table)
        else:
            elements.append(Paragraph("作業内容情報なし", styles["JapaneseNormal"]))
        elements.append(Spacer(1, 12))

        # 備考
        if report.note:
            elements.append(Paragraph("＜備考＞", styles["JapaneseHeading2"]))
            elements.append(Paragraph(report.note, styles["JapaneseNormal"]))
            elements.append(Spacer(1, 12))

        # PDFドキュメントを生成（1ページ目、基本情報と作業内容）
        doc.build(elements)

        # 新しいバッファを作成（写真用）
        if photo_pairs:
            # 初期化したバッファを保存
            buffer_content = buffer.getvalue()
            buffer.close()

            # マージするためのPDFライター
            pdf_writer = PdfWriter()

            # 1ページ目のPDFを読み込む
            pdf_reader = PdfReader(BytesIO(buffer_content))
            for page in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page])

            # 写真用の新しいPDFを作成
            photo_buffer = BytesIO()
            photo_doc = SimpleDocTemplate(
                photo_buffer,
                pagesize=A4,
                title=f"作業完了書_{report.id}_写真",
                author="エアコンクリーニング完了報告書システム",
            )

            # 一時ファイルのリストを保持
            temp_files = []

            # 写真ページを調整するための追加設定
            # 写真ページのコンテンツ
            photo_elements = []
            photo_elements.append(
                Paragraph("＜施工前後写真＞", styles["JapaneseHeading2"])
            )
            photo_elements.append(Spacer(1, 8))  # 間隔を少し増やす

            # 写真を2セットごとにグループ化（1ページに2セット表示）
            photos_per_page = 2
            photo_groups = [
                photo_pairs[i : i + photos_per_page]
                for i in range(0, len(photo_pairs), photos_per_page)
            ]

            for group_index, group in enumerate(photo_groups):
                if group_index > 0:
                    # 2ページ目以降は新しいページを開始
                    photo_elements.append(PageBreak())
                    photo_elements.append(
                        Paragraph("＜施工前後写真＞", styles["JapaneseHeading2"])
                    )
                    photo_elements.append(Spacer(1, 8))  # 間隔を少し増やす

                # 各グループの写真セットと画像を一つのまとまりとして処理する
                for i, (before_photo, after_photo) in enumerate(group):
                    if before_photo or after_photo:
                        # 前のセットとの間に区切りを入れる（最初のセット以外）
                        if i > 0:
                            for element in create_divider():
                                photo_elements.append(element)

                        # 写真セットの開始
                        photo_set_elements = []

                        # 写真キャプションを作成（余白を減らしたスタイルを使用）
                        if group_index > 0:
                            caption = f"写真 #{group_index * photos_per_page + i + 1}"
                        else:
                            caption = f"写真 #{i + 1}"

                        photo_set_elements.append(
                            Paragraph(caption, styles["JapanesePhotoCaption"])
                        )

                        # エアコン情報を追加
                        ac_info = ""
                        work_item_info = ""

                        if before_photo and before_photo.air_conditioner:
                            manufacturer = (
                                before_photo.air_conditioner.manufacturer or ""
                            )
                            model = before_photo.air_conditioner.model_number or ""
                            location = before_photo.air_conditioner.location or ""
                            ac_info = f"{manufacturer} {model} ({location})"

                            # 作業項目の情報を取得
                            if before_photo.work_item:
                                work_item_info = before_photo.work_item.name or ""
                        elif after_photo and after_photo.air_conditioner:
                            manufacturer = (
                                after_photo.air_conditioner.manufacturer or ""
                            )
                            model = after_photo.air_conditioner.model_number or ""
                            location = after_photo.air_conditioner.location or ""
                            ac_info = f"{manufacturer} {model} ({location})"

                            # 作業項目の情報を取得
                            if after_photo.work_item:
                                work_item_info = after_photo.work_item.name or ""

                        if ac_info:
                            photo_set_elements.append(
                                Paragraph(
                                    f"エアコン: {ac_info}", styles["JapaneseAcInfo"]
                                )
                            )

                        # 作業項目の情報を表示
                        if work_item_info:
                            photo_set_elements.append(
                                Paragraph(
                                    f"作業項目: {work_item_info}",
                                    styles["JapaneseAcInfo"],
                                )
                            )

                        photo_set_elements.append(Spacer(1, 4))  # 間隔を少し増やす

                        # 写真のパスとキャプションのデータを準備
                        photo_data = []

                        # 施工前/施工後のヘッダー行を追加
                        header_row = [
                            Paragraph("施工前", styles["JapaneseHeading3"]),
                            Paragraph("施工後", styles["JapaneseHeading3"]),
                        ]
                        photo_data.append(header_row)

                        photo_row = []
                        caption_row = []

                        # 施工前の写真
                        if (
                            before_photo
                            and before_photo.filepath
                            and os.path.exists(
                                os.path.join(
                                    current_app.config["UPLOAD_FOLDER"],
                                    before_photo.filepath,
                                )
                            )
                        ):
                            try:
                                # 画像パスを取得
                                image_path = os.path.join(
                                    current_app.config["UPLOAD_FOLDER"],
                                    before_photo.filepath,
                                )

                                # 画像の向きを修正
                                corrected_image = fix_image_orientation(image_path)

                                # 画像をリサイズしてから一時ファイルに保存（パフォーマンス最適化）
                                # まず画像をPDFに適したサイズにリサイズ
                                corrected_image.thumbnail(
                                    (480, 360), PILImage.Resampling.LANCZOS
                                )

                                # 一時ファイルに保存
                                with tempfile.NamedTemporaryFile(
                                    suffix=".jpg", delete=False
                                ) as temp_file:
                                    corrected_image.save(
                                        temp_file.name,
                                        "JPEG",
                                        quality=85,
                                        optimize=True,
                                    )
                                    temp_path = temp_file.name
                                    temp_files.append(
                                        temp_path
                                    )  # 一時ファイルリストに追加

                                # 画像をPDFに挿入（サイズを調整）
                                img = Image(
                                    temp_path,
                                    width=240,  # 幅を拡大（180→240）
                                    height=180,  # 高さを拡大（135→180）
                                )
                                photo_row.append(img)

                                caption_text = before_photo.caption or ""
                                if before_photo.room_name:
                                    caption_text = (
                                        f"{before_photo.room_name}: {caption_text}"
                                    )
                                caption_row.append(
                                    Paragraph(
                                        caption_text,
                                        styles["JapaneseNormal"],
                                    )
                                )
                            except Exception as e:
                                print(f"施工前画像処理エラー: {e}")
                                photo_row.append(
                                    Paragraph(
                                        "画像を読み込めませんでした",
                                        styles["JapaneseNormal"],
                                    )
                                )
                                caption_row.append(
                                    Paragraph(
                                        "施工前",
                                        styles["JapaneseNormal"],
                                    )
                                )
                        else:
                            photo_row.append(
                                Paragraph("画像なし", styles["JapaneseNormal"])
                            )
                            caption_row.append(
                                Paragraph("施工前", styles["JapaneseNormal"])
                            )

                        # 施工後の写真
                        if (
                            after_photo
                            and after_photo.filepath
                            and os.path.exists(
                                os.path.join(
                                    current_app.config["UPLOAD_FOLDER"],
                                    after_photo.filepath,
                                )
                            )
                        ):
                            try:
                                # 画像パスを取得
                                image_path = os.path.join(
                                    current_app.config["UPLOAD_FOLDER"],
                                    after_photo.filepath,
                                )

                                # 画像の向きを修正
                                corrected_image = fix_image_orientation(image_path)

                                # 画像をリサイズしてから一時ファイルに保存（パフォーマンス最適化）
                                # まず画像をPDFに適したサイズにリサイズ
                                corrected_image.thumbnail(
                                    (480, 360), PILImage.Resampling.LANCZOS
                                )

                                # 一時ファイルに保存
                                with tempfile.NamedTemporaryFile(
                                    suffix=".jpg", delete=False
                                ) as temp_file:
                                    corrected_image.save(
                                        temp_file.name,
                                        "JPEG",
                                        quality=85,
                                        optimize=True,
                                    )
                                    temp_path = temp_file.name
                                    temp_files.append(
                                        temp_path
                                    )  # 一時ファイルリストに追加

                                # 画像をPDFに挿入（サイズを調整）
                                img = Image(
                                    temp_path,
                                    width=240,  # 幅を拡大（180→240）
                                    height=180,  # 高さを拡大（135→180）
                                )
                                photo_row.append(img)

                                caption_text = after_photo.caption or ""
                                if after_photo.room_name:
                                    caption_text = (
                                        f"{after_photo.room_name}: {caption_text}"
                                    )
                                caption_row.append(
                                    Paragraph(
                                        caption_text,
                                        styles["JapaneseNormal"],
                                    )
                                )
                            except Exception as e:
                                print(f"施工後画像処理エラー: {e}")
                                photo_row.append(
                                    Paragraph(
                                        "画像を読み込めませんでした",
                                        styles["JapaneseNormal"],
                                    )
                                )
                                caption_row.append(
                                    Paragraph(
                                        "施工後",
                                        styles["JapaneseNormal"],
                                    )
                                )
                        else:
                            photo_row.append(
                                Paragraph("画像なし", styles["JapaneseNormal"])
                            )
                            caption_row.append(
                                Paragraph("施工後", styles["JapaneseNormal"])
                            )

                        photo_data.append(photo_row)
                        photo_data.append(caption_row)

                        # 写真とキャプションのテーブルを作成（幅も調整）
                        photo_table = Table(
                            photo_data, colWidths=[270, 270]
                        )  # 幅を拡大（225→270）
                        photo_table.setStyle(
                            TableStyle(
                                [
                                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                    (
                                        "BACKGROUND",
                                        (0, 0),
                                        (-1, 0),
                                        colors.lightgrey,
                                    ),  # ヘッダー行の背景色
                                    (
                                        "TOPPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        3,
                                    ),  # 上部パディングを少し増やす
                                    (
                                        "BOTTOMPADDING",
                                        (0, 0),
                                        (-1, -1),
                                        6,
                                    ),  # 下部パディングを少し増やす
                                    (
                                        "GRID",
                                        (0, 0),
                                        (-1, -1),
                                        0.5,
                                        colors.black,
                                    ),  # 枠線を追加
                                ]
                            )
                        )

                        # 間隔を調整
                        all_elements = photo_set_elements + [
                            photo_table,
                            Spacer(1, 15),  # 間隔を増やす（3→15）
                        ]
                        photo_elements.append(KeepTogether(all_elements))

            # 写真ページを生成
            photo_doc.build(photo_elements)

            # 一時ファイルを削除
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass

            # 写真ページをメインPDFにマージ
            photo_buffer.seek(0)
            photo_reader = PdfReader(photo_buffer)
            for page in range(len(photo_reader.pages)):
                pdf_writer.add_page(photo_reader.pages[page])

            # マージしたPDFをバッファに書き込む
            buffer = BytesIO()
            pdf_writer.write(buffer)
            buffer.seek(0)
        else:
            buffer.seek(0)

        # バッファの位置をリセットして内容を返す
        buffer.seek(0)

        # ディスクに保存する場合
        if save_to_disk:
            try:
                # 顧客名と物件名を取得（sanitize_filename関数で安全なファイル名に変換）
                customer_name = sanitize_filename(
                    report.property.customer.name
                    if report.property and report.property.customer
                    else "unknown"
                )
                property_name = sanitize_filename(
                    report.property.name if report.property else "unknown"
                )

                # PDFを保存するディレクトリ構造を作成
                pdf_dir = os.path.join(
                    current_app.config["UPLOAD_FOLDER"],
                    "PDF",
                    customer_name,
                    property_name,
                )

                # ディレクトリが存在しない場合は作成
                if not os.path.exists(pdf_dir):
                    os.makedirs(pdf_dir, exist_ok=True)

                # 現在の日時を含むファイル名を生成
                date_str = (
                    report.date.strftime("%Y%m%d")
                    if report.date
                    else datetime.now().strftime("%Y%m%d")
                )
                time_str = datetime.now().strftime("%H%M%S")
                filename = f"作業完了報告書_{customer_name}_{property_name}_{date_str}_{time_str}.pdf"

                # 最終的なファイルパスを構築
                file_path = os.path.join(pdf_dir, filename)

                # PDFをファイルに保存
                with open(file_path, "wb") as f:
                    f.write(buffer.getvalue())

                print(f"PDF saved to: {file_path}")
                return buffer, file_path
            except Exception as e:
                print(f"PDF保存エラー: {e}")
                # エラーが発生しても、バッファは返す
                return buffer, None

        return buffer

    @staticmethod
    def combine_pdfs(pdf_files, output_filename):
        """
        複数のPDFファイルを1つのPDFファイルに結合する

        Args:
            pdf_files (list): PDFファイルのパスのリスト
            output_filename (str): 出力ファイル名

        Returns:
            str: 結合したPDFファイルのパス
        """
        # 実装予定
        return output_filename
