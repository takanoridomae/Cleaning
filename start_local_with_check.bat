@echo off
REM ========================================================================
REM エアコンクリーニング報告書システム - ローカル起動スクリプト (詳細版)
REM ========================================================================
REM 
REM このスクリプトは、以下の処理を実行してFlaskアプリケーションを起動します:
REM   - 仮想環境のアクティベート
REM   - データベースの確認とバックアップ
REM   - Tailscale VPN接続の確認
REM   - NAS接続テスト（NAS使用の場合）
REM   - Flaskアプリケーションの起動
REM 
REM ========================================================================

echo.
echo ========================================================================
echo エアコンクリーニング報告書システム - ローカル起動 (詳細版)
echo ========================================================================
echo.

REM カレントディレクトリをスクリプトのディレクトリに変更
cd /d "%~dp0"

REM ========================================================================
REM 1. 仮想環境の確認とアクティベート
REM ========================================================================
echo [1/6] 仮想環境の確認...
echo.

if not exist "venv\Scripts\activate.bat" (
    echo ❌ エラー: 仮想環境が見つかりません。
    echo.
    echo 仮想環境を作成しますか？ (Y/N)
    set /p CREATE_VENV=
    if /i "%CREATE_VENV%"=="Y" (
        echo.
        echo 仮想環境を作成しています...
        python -m venv venv
        if %errorlevel% neq 0 (
            echo ❌ エラー: 仮想環境の作成に失敗しました。
            pause
            exit /b 1
        )
        echo ✅ 仮想環境を作成しました
        echo.
        echo 必要なパッケージをインストールしています...
        call venv\Scripts\activate.bat
        pip install -r requirements.txt
        if %errorlevel% neq 0 (
            echo ❌ エラー: パッケージのインストールに失敗しました。
            pause
            exit /b 1
        )
        echo ✅ パッケージをインストールしました
    ) else (
        echo 仮想環境を作成せずに終了します。
        pause
        exit /b 1
    )
) else (
    echo ✅ 仮想環境が見つかりました
    call venv\Scripts\activate.bat
    echo ✅ 仮想環境をアクティベートしました
)
echo.

REM ========================================================================
REM 2. データベースの確認とバックアップ
REM ========================================================================
echo [2/6] データベースの確認とバックアップ...
echo.

if not exist "instance" (
    mkdir instance
    echo ✅ instanceディレクトリを作成しました
)

if not exist "instance\aircon_report.db" (
    echo ⚠️  警告: データベースファイルが見つかりません。
    echo 初回起動時にデータベースが作成されます。
    echo.
) else (
    echo ✅ データベースファイルを確認しました (instance\aircon_report.db)
    
    REM データベースバックアップディレクトリの作成
    if not exist "db_backups\startup" (
        mkdir db_backups\startup
    )
    
    REM バックアップの作成（タイムスタンプ付き）
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
    set timestamp=%mydate%_%mytime%
    
    echo データベースバックアップを作成しています...
    copy "instance\aircon_report.db" "db_backups\startup\aircon_report_%timestamp%.db" >nul
    echo ✅ バックアップを作成しました: db_backups\startup\aircon_report_%timestamp%.db
    echo.
)

REM ========================================================================
REM 3. 環境変数の確認
REM ========================================================================
echo [3/6] 環境変数の確認...
echo.

if not exist ".env" (
    echo ⚠️  警告: .env ファイルが見つかりません。
    echo.
    echo .env ファイルのサンプルを表示しますか？ (Y/N)
    set /p SHOW_SAMPLE=
    if /i "%SHOW_SAMPLE%"=="Y" (
        echo.
        echo ========================================================================
        echo .env ファイルのサンプル
        echo ========================================================================
        echo.
        echo # NAS機能を有効化
        echo NAS_ENABLED=True
        echo.
        echo # NAS WebDAV URL
        echo NAS_WEBDAV_URL=http://100.69.218.15:5005
        echo.
        echo # NASログイン情報
        echo NAS_USERNAME=Takanori
        echo NAS_PASSWORD=your-password-here
        echo.
        echo # NAS保存先ベースパス
        echo NAS_BASE_PATH=/home/eacon_keep_pict
        echo.
        echo ========================================================================
        echo.
        echo 詳細は ENV_SETUP_INSTRUCTIONS.md を参照してください。
        echo.
    )
    echo ローカルストレージのみで起動を続けます...
    echo.
) else (
    echo ✅ .env ファイルを確認しました
    echo.
    
    REM .envファイルから設定を読み込んで表示
    findstr /i "NAS_ENABLED" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo 検出された設定:
        findstr /i /c:"NAS_ENABLED" .env
        findstr /i /c:"NAS_WEBDAV_URL" .env 2>nul
        echo.
    )
)

REM ========================================================================
REM 4. Tailscale VPN接続の確認（NAS使用の場合）
REM ========================================================================
echo [4/6] Tailscale VPN接続の確認...
echo.

where tailscale >nul 2>&1
if %errorlevel% equ 0 (
    echo Tailscale接続状態を確認しています...
    echo.
    tailscale status
    echo.
    
    tailscale status | findstr "100.69.218.15" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Tailscale VPNが接続されています
        echo ✅ NASにアクセス可能です (100.69.218.15)
    ) else (
        echo ⚠️  NASが見つかりません (100.69.218.15)
        echo    Tailscale VPNが完全に接続されていない可能性があります
    )
) else (
    echo ℹ️  Tailscaleがインストールされていないか、パスが通っていません
    echo    NASを使用する場合は、Tailscaleを起動してください
)
echo.

REM ========================================================================
REM 5. NAS接続テスト（オプション）
REM ========================================================================
echo [5/6] NAS接続テスト...
echo.

if exist ".env" (
    findstr /i "NAS_ENABLED=True" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo NASが有効になっています。接続テストを実行しますか？ (Y/N)
        set /p RUN_TEST=
        if /i "%RUN_TEST%"=="Y" (
            echo.
            echo NAS接続テストを実行しています...
            echo.
            python scripts\utilities\test_nas_connection.py
            echo.
            if %errorlevel% neq 0 (
                echo ⚠️  NAS接続テストに失敗しました
                echo    ローカルストレージにフォールバックします
                echo.
                echo このまま起動を続けますか？ (Y/N)
                set /p CONTINUE=
                if /i not "%CONTINUE%"=="Y" (
                    echo 起動を中止しました。
                    pause
                    exit /b 1
                )
            )
        ) else (
            echo NAS接続テストをスキップしました
        )
    ) else (
        echo NASは無効になっています (ローカルストレージのみ使用)
    )
) else (
    echo .env ファイルがないため、NAS接続テストをスキップしました
)
echo.

REM ========================================================================
REM 6. Flaskアプリケーションの起動
REM ========================================================================
echo [6/6] Flaskアプリケーションを起動しています...
echo.
echo ========================================================================
echo アプリケーション起動中...
echo ========================================================================
echo.
echo アクセスURL: http://localhost:5000
echo または:      http://127.0.0.1:5000
echo.
echo ネットワーク上の他のデバイスからアクセスする場合:
echo   http://[このPCのIPアドレス]:5000
echo.
echo 停止するには: Ctrl + C を押してください
echo.
echo ========================================================================
echo.

REM Flaskアプリケーションを起動
python run.py

REM エラーが発生した場合
if %errorlevel% neq 0 (
    echo.
    echo ❌ エラー: アプリケーションの起動に失敗しました。
    echo.
    echo 以下を確認してください:
    echo   1. 仮想環境が正しくアクティベートされているか
    echo   2. 必要なパッケージがインストールされているか
    echo   3. ポート5000が他のアプリケーションで使用されていないか
    echo   4. データベースファイルが破損していないか
    echo.
    pause
    exit /b 1
)

pause

