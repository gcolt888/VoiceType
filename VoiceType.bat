@echo off
chcp 65001 >nul 2>&1
title VoiceType

echo ========================================
echo        VoiceType - 语音输入工具
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python 3.8+: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER%

echo.
echo [2/3] 检查依赖...
pip show funasr >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行，正在安装依赖（约2-3分钟）...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 依赖已安装
)

echo.
echo [3/3] 启动 VoiceType...
echo ========================================
echo 提示: 按住右Ctrl说话，松开自动粘贴
echo       按 Esc 退出
echo ========================================
echo.
python voice_to_text.py

pause
