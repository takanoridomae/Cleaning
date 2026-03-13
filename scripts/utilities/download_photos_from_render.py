#!/usr/bin/env python3
"""
Renderから写真をダウンロード

photo_urls.txt に記載されたURLから写真をダウンロードします。

使用方法:
    python scripts/utilities/download_photos_from_render.py photo_urls.txt

出力先:
    downloads_from_render/before/  - 施工前写真
    downloads_from_render/after/   - 施工後写真
"""
import os
import sys
import requests
from pathlib import Path
from datetime import datetime
import time

# Windows環境での文字化け対策
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def download_photos(urls_file, output_dir="downloads_from_render"):
    """URLリストから写真をダウンロード"""

    print("=" * 70)
    print("Renderから写真をダウンロード")
    print("=" * 70)

    # URLリストファイルの確認
    if not os.path.exists(urls_file):
        print(f"\n❌ URLリストファイルが見つかりません: {urls_file}")
        print("\n使用方法:")
        print(f"  python {sys.argv[0]} photo_urls.txt")
        return False

    # ダウンロード先ディレクトリの作成
    download_base = Path(output_dir)
    download_base.mkdir(exist_ok=True)

    before_dir = download_base / "before"
    after_dir = download_base / "after"
    before_dir.mkdir(exist_ok=True)
    after_dir.mkdir(exist_ok=True)

    print(f"\n📂 ダウンロード先: {download_base.absolute()}")

    # URLリストを読み込む
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"\n❌ URLリスト読み込みエラー: {e}")
        return False

    if not lines:
        print("\n⚠️ URLリストが空です")
        return False

    total = len(lines)
    success = 0
    failed = 0
    skipped = 0
    total_bytes = 0

    print(f"\n📥 {total}個の写真をダウンロードします...\n")

    start_time = datetime.now()

    for i, line in enumerate(lines, 1):
        try:
            # パイプ区切りでデータを分割
            parts = line.split("|")
            if len(parts) < 3:
                print(f"  {i:3d}/{total} ⚠️  スキップ（形式エラー）: {line[:50]}...")
                skipped += 1
                continue

            url = parts[0]
            photo_type = parts[1]
            filename = parts[2]

            # ダウンロード先パス
            if photo_type == "before":
                dest_path = before_dir / filename
            elif photo_type == "after":
                dest_path = after_dir / filename
            else:
                print(f"  {i:3d}/{total} ⚠️  スキップ（不明なタイプ）: {photo_type}")
                skipped += 1
                continue

            # 既に存在する場合はスキップ
            if dest_path.exists():
                file_size = dest_path.stat().st_size
                size_kb = file_size / 1024
                print(
                    f"  {i:3d}/{total} ⏭️  スキップ（既存）: {filename} ({size_kb:.1f} KB)"
                )
                skipped += 1
                continue

            # ダウンロード実行
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                # ファイル保存
                with open(dest_path, "wb") as f:
                    f.write(response.content)

                file_size = len(response.content)
                size_kb = file_size / 1024
                total_bytes += file_size

                print(
                    f"  {i:3d}/{total} ✅ ダウンロード: {filename} ({size_kb:.1f} KB)"
                )
                success += 1

                # サーバーへの負荷を軽減するため少し待機
                if i % 10 == 0:
                    time.sleep(0.5)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"  {i:3d}/{total} ❌ 見つかりません: {filename}")
                else:
                    print(
                        f"  {i:3d}/{total} ❌ HTTPエラー: {filename} - {e.response.status_code}"
                    )
                failed += 1
            except requests.exceptions.Timeout:
                print(f"  {i:3d}/{total} ❌ タイムアウト: {filename}")
                failed += 1
            except requests.exceptions.ConnectionError:
                print(f"  {i:3d}/{total} ❌ 接続エラー: {filename}")
                failed += 1
            except Exception as e:
                print(
                    f"  {i:3d}/{total} ❌ エラー: {filename} - {type(e).__name__}: {e}"
                )
                failed += 1

        except Exception as e:
            print(f"  {i:3d}/{total} ❌ 処理エラー: {e}")
            failed += 1

    # 結果サマリー
    elapsed_time = (datetime.now() - start_time).total_seconds()
    total_mb = total_bytes / (1024 * 1024)

    print(f"\n{'=' * 70}")
    print("ダウンロード結果")
    print("=" * 70)
    print(f"✅ 成功: {success}個 ({total_mb:.2f} MB)")
    print(f"⏭️  スキップ: {skipped}個（既存ファイル）")
    print(f"❌ 失敗: {failed}個")
    print(f"📊 合計: {total}個")
    print(f"⏱️  処理時間: {elapsed_time:.1f}秒")

    if success > 0 and elapsed_time > 0:
        avg_speed = total_mb / elapsed_time
        print(f"📈 平均速度: {avg_speed:.2f} MB/秒")

    print(f"\n📂 保存先:")
    print(f"   施工前: {before_dir.absolute()}")
    print(f"   施工後: {after_dir.absolute()}")

    # 次のステップの案内
    if success > 0:
        print(f"\n{'=' * 70}")
        print("📝 次のステップ:")
        print("=" * 70)
        print("1. ダウンロードした写真をuploadsフォルダに移動:")
        print(f"   (Windows)")
        print(
            f"   Copy-Item -Path {output_dir}\\before\\* -Destination uploads\\before\\"
        )
        print(
            f"   Copy-Item -Path {output_dir}\\after\\* -Destination uploads\\after\\"
        )
        print(f"\n   (Linux/Mac)")
        print(f"   cp {output_dir}/before/* uploads/before/")
        print(f"   cp {output_dir}/after/* uploads/after/")
        print("\n2. NAS移行スクリプトを実行:")
        print("   python migrate_existing_photos_to_nas.py")

    print("\n" + "=" * 70)

    return success > 0 or skipped > 0


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print(f"  python {sys.argv[0]} photo_urls.txt")
        print("\nオプション:")
        print(f"  python {sys.argv[0]} photo_urls.txt custom_output_dir")
        print("\n説明:")
        print("  photo_urls.txt: generate_photo_urls.py で生成したURLリスト")
        print(
            "  custom_output_dir: ダウンロード先ディレクトリ（デフォルト: downloads_from_render）"
        )
        sys.exit(1)

    urls_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads_from_render"

    try:
        success = download_photos(urls_file, output_dir)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
