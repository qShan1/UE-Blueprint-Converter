@echo off
chcp 65001 >nul
title UE Blueprint Visualizer - 打包脚本
echo ========================================
echo UE Blueprint Visualizer - 打包脚本
echo ========================================
echo.
echo 本工具无需后端，纯前端运行。
echo 打包后只需打开 index.html 即可使用。
echo.

if not exist "web\node_modules" (
    echo [1/3] 正在安装 npm 依赖...
    cd web
    call npm install
    if errorlevel 1 (
        echo 错误: npm install 失败，请检查 Node.js 是否安装正确
        pause
        exit /b 1
    )
    cd ..
    echo.
)

echo [2/3] 正在构建前端...
cd web
call npm run build
if errorlevel 1 (
    echo 错误: 前端构建失败
    pause
    exit /b 1
)
cd ..
echo.

echo [3/3] 正在创建便携包...

if exist "UE-Blueprint-Visualizer-Portable" rmdir /s /q "UE-Blueprint-Visualizer-Portable"

mkdir "UE-Blueprint-Visualizer-Portable"

xcopy /e /i /q "web\dist" "UE-Blueprint-Visualizer-Portable"

echo @echo off > "UE-Blueprint-Visualizer-Portable\启动.bat"
echo start "" "index.html" >> "UE-Blueprint-Visualizer-Portable\启动.bat"
echo exit >> "UE-Blueprint-Visualizer-Portable\启动.bat"

echo.
echo ========================================
echo 打包完成！
echo 位置: %cd%\UE-Blueprint-Visualizer-Portable\
echo 使用方式: 打开 UE-Blueprint-Visualizer-Portable 文件夹，
echo           双击 "启动.bat" 或直接双击 "index.html"
echo.
echo 总大小约 300KB，无需安装任何软件。
echo ========================================
echo.
pause