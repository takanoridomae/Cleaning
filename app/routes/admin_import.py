from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
import os
import json
from datetime import datetime

# インポート用関数
from scripts.db_tools.import_to_render import import_data_to_render

bp = Blueprint("admin_import", __name__, url_prefix="/admin")


@bp.route("/import-data", methods=["GET", "POST"])
@login_required
def import_data():
    """管理者専用のデータインポート"""

    # 管理者権限チェック
    if not current_user.role == "admin":
        flash("管理者権限が必要です", "error")
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return """
        <html>
        <head><title>データインポート</title></head>
        <body>
            <h1>データインポート（管理者専用）</h1>
            <form method="POST">
                <p>
                    <label>インポートファイル名:</label><br>
                    <input type="text" name="filename" value="simple_export_20250624_185754.json" style="width: 400px;">
                </p>
                <p>
                    <input type="submit" value="インポート実行" style="padding: 10px 20px; background: #ff4444; color: white; border: none;">
                </p>
                <p style="color: red;">
                    ⚠️ 注意: この操作は既存データに追加されます。実行前に必ずバックアップを確認してください。
                </p>
            </form>
            <p><a href="/">トップページに戻る</a></p>
        </body>
        </html>
        """

    if request.method == "POST":
        filename = request.form.get("filename", "").strip()

        if not filename:
            return jsonify({"error": "ファイル名が指定されていません"}), 400

        # ファイルの存在確認
        if not os.path.exists(filename):
            return jsonify({"error": f"ファイルが見つかりません: {filename}"}), 404

        try:
            # インポート実行
            result = import_data_to_render(filename)

            if result:
                return (
                    """
                <html>
                <head><title>インポート完了</title></head>
                <body>
                    <h1>✅ データインポート完了</h1>
                    <p>ファイル: """
                    + filename
                    + """</p>
                    <p>インポートが正常に完了しました。</p>
                    <p><a href="/">トップページで確認する</a></p>
                </body>
                </html>
                """
                )
            else:
                return """
                <html>
                <head><title>インポート失敗</title></head>
                <body>
                    <h1>❌ データインポート失敗</h1>
                    <p>インポート処理でエラーが発生しました。</p>
                    <p>ログを確認してください。</p>
                    <p><a href="/admin/import-data">戻る</a></p>
                </body>
                </html>
                """

        except Exception as e:
            return jsonify({"error": f"インポートエラー: {str(e)}"}), 500
