@echo off
setlocal enabledelayedexpansion

set "VERSION=202606121"

set "ISS_FILE_PATH=build_scripts\script.iss"
set "CLIENT_FILE_PATH=src\config_manager.py"
@REM set "SERVER_FILE_PATH=..\LocalProxyServer\src\Main.py"
@REM set "JSON_FILE_PATH=..\LocalProxyServer54188\config_client_old.jsonc"

powershell -Command "(Get-Content '%ISS_FILE_PATH%' -Encoding UTF8) | ForEach-Object { if ($_ -match '#define MyAppVersion') { '#define MyAppVersion \"%VERSION%\"' } else { $_ } } | Set-Content '%ISS_FILE_PATH%' -Encoding UTF8"
powershell -Command "(Get-Content '%CLIENT_FILE_PATH%' -Encoding UTF8) | ForEach-Object { if ($_ -match 'VERSION_CODE = ') { 'VERSION_CODE = %VERSION%' } else { $_ } } | Set-Content '%CLIENT_FILE_PATH%' -Encoding UTF8"
@REM powershell -Command "(Get-Content '%SERVER_FILE_PATH%' -Encoding UTF8) | ForEach-Object { if ($_ -match 'VERSION_CODE = ') { 'VERSION_CODE = %VERSION%' } else { $_ } } | Set-Content '%SERVER_FILE_PATH%' -Encoding UTF8"
@REM powershell -Command "(Get-Content '%JSON_FILE_PATH%' -Encoding UTF8) | ForEach-Object { if ($_ -match '        \"latest_vercode\": ') { '        \"latest_vercode\": %VERSION%, // ���°汾��' } else { $_ } } | Set-Content '%JSON_FILE_PATH%' -Encoding UTF8"

taskkill /im LocalProxy.exe /f >nul 2>&1
if exist "build\LocalProxy" (
    rd /s /q "build\LocalProxy" >nul
)

REM pyinstaller --onefile -w --distpath build --workpath %PYINSTALLER_CACHE_DIR% -i assets\icon.ico -n Updater --noconfirm src/Updater.py
pyinstaller -D -w --distpath build --workpath %PYINSTALLER_CACHE_DIR% -i assets\icon.ico -n LocalProxy --noconfirm src/main.py

copy /y build\Updater.exe build\LocalProxy\Updater.exe
REM mkdir build\LocalProxy\logs
REM attrib +h +s build\LocalProxy\logs
echo > build\LocalProxy\config.json

cd build
bz c -l:9 LocalProxyPortable.zip "LocalProxy"

cd ..
"build_scripts\Inno Setup 6\iscc.exe" "build_scripts\script.iss"
move build_scripts\LocalProxySetup.exe build

cd build
bz c -l:9 LocalProxySetup.zip "LocalProxySetup.exe"

@REM copy /y LocalProxySetup.zip ..\..\LocalProxyServer\assets\web\downloads
@REM copy /y LocalProxyPortable.zip ..\..\LocalProxyServer\assets\web\downloads

cd ..
