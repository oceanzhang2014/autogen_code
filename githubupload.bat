@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    Git版本保存和推送脚本
echo ========================================
echo.

REM 检查是否在git仓库中
git status >nul 2>&1
if errorlevel 1 (
    echo 错误: 当前目录不是Git仓库!
    pause
    exit /b 1
)

REM 显示当前状态
echo 当前Git状态:
git status --short

echo.
echo 将要提交的文件:
git diff --cached --name-only
git diff --name-only

echo.

REM 询问用户输入提交说明
set /p msg=请输入本次提交说明: 

REM 检查提交说明是否为空
if "%msg%"=="" (
    echo 错误: 提交说明不能为空!
    pause
    exit /b 1
)

echo.
echo 正在添加所有文件...
git add .

echo 正在提交更改...
git commit -m "%msg%"

if errorlevel 1 (
    echo 提交失败! 可能没有需要提交的更改。
    pause
    exit /b 1
)

echo.
echo 正在获取远程最新更改并rebase...
git pull --rebase origin main

if errorlevel 1 (
    echo 注意: 可能是首次推送或有冲突，将尝试直接推送...
)

echo.
echo 正在推送到GitHub...
git push -u origin main

if errorlevel 1 (
    echo 推送失败! 请检查网络连接和权限。
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Git操作完成成功!
echo ========================================
echo 提交信息: %msg%
echo 推送分支: main
echo.

pause