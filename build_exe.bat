@echo off
echo ========================================
echo UE Blueprint Visualizer - 打包脚本
echo ========================================
echo.

REM 检查是否在 web 目录下执行了 npm install
if not exist "web\node_modules" (
    echo [1/4] 正在安装 npm 依赖...
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

REM 检查是否已经构建了前端
if not exist "web\dist" (
    echo [2/4] 正在构建前端...
    cd web
    call npm run build
    if errorlevel 1 (
        echo 错误: 前端构建失败
        pause
        exit /b 1
    )
    cd ..
    echo.
)

REM 安装 PyInstaller
echo [3/4] 正在检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误: PyInstaller 安装失败
        pause
        exit /b 1
    )
    echo.
)

REM 开始打包
echo [4/4] 正在使用 PyInstaller 打包...
pyinstaller --clean ue_blueprint_visualizer.spec
if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位置: dist\UE-Blueprint-Visualizer.exe
echo ========================================
echo.
pause
