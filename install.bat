@echo off
chcp 65001 >nul
title M.A.S.T.E.R. 安装程序

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║          M.A.S.T.E.R. 安装向导                         ║
echo  ║          Multi-Agent Task Execution System            ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] 错误：未检测到 Python
    echo.
    echo 请先安装 Python:
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载 Python 3.11 或更高版本
    echo   3. 勾选 "Add Python to PATH"
    echo   4. 运行安装程序
    echo.
    pause
    exit /b 1
)

echo [√] 检测到 Python 环境

:: 安装依赖
echo.
echo [*] 正在安装依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [!] 依赖安装失败
    pause
    exit /b 1
)

echo [√] 依赖安装完成

:: 创建数据目录
if not exist "data" mkdir data
if not exist "data\memory" mkdir data\memory

:: 创建启动脚本
echo.
echo [*] 正在配置...

:: 检查并启动 Qdrant（可选）
echo.
echo [*] 正在启动服务...
echo.
echo 安装完成！
echo.
echo ─────────────────────────────────────────────────────────
echo.
echo  启动方式：
echo    双击 "启动 MASTER.bat" 即可运行
echo.
echo  首次使用需要：
echo    1. 配置 AI API Key（可选）
echo    2. 如需向量搜索，启动 Qdrant
echo.
echo ─────────────────────────────────────────────────────────
echo.

:: 启动主程序
call start.bat

pause