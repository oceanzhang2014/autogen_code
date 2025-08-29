@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    快速Git提交脚本
echo ========================================
echo.

REM 检查是否在git仓库中
git status >nul 2>&1
if errorlevel 1 (
    echo 错误: 当前目录不是Git仓库!
    pause
    exit /b 1
)

REM 生成默认提交信息（基于当前时间）
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set datestr=%%a-%%b-%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set timestr=%%a:%%b
)

set default_msg=Auto commit on %datestr% %timestr%

echo 当前Git状态:
git status --short
echo.

REM 询问是否使用默认提交信息
echo 默认提交信息: %default_msg%
echo.
set /p use_default=使用默认提交信息吗？(y/n, 默认y): 

if "%use_default%"=="" set use_default=y
if /i "%use_default%"=="y" (
    set msg=%default_msg%
) else (
    set /p msg=请输入自定义提交说明: 
    if "!msg!"=="" (
        echo 错误: 提交说明不能为空!
        pause
        exit /b 1
    )
)

echo.
echo 提交信息: !msg!
echo 正在执行git操作...
echo.

REM 添加所有文件
git add .

REM 提交更改
git commit -m "!msg!"

if errorlevel 1 (
    echo 提交失败! 可能没有需要提交的更改。
    pause
    exit /b 1
)

REM 拉取并rebase
git pull --rebase origin main

if errorlevel 1 (
    echo 注意: 可能是首次推送或有冲突，将尝试直接推送...
)

REM 推送到远程
git push -u origin main

if errorlevel 1 (
    echo 推送失败! 请检查网络连接和权限。
    pause
    exit /b 1
)

echo.
echo ========================================
echo    快速提交完成!
echo ========================================
echo.

pause