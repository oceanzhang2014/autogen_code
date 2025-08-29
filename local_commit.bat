@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    本地Git提交脚本（仅提交不推送）
echo ========================================
echo.

REM 检查是否在git仓库中
git status >nul 2>&1
if errorlevel 1 (
    echo 错误: 当前目录不是Git仓库!
    pause
    exit /b 1
)

echo 当前Git状态:
git status --short
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

echo 正在本地提交更改...
git commit -m "%msg%"

if errorlevel 1 (
    echo 提交失败! 可能没有需要提交的更改。
    pause
    exit /b 1
)

echo.
echo ========================================
echo    本地提交完成!
echo ========================================
echo 提交信息: %msg%
echo 注意: 更改仅保存在本地，未推送到远程仓库
echo 需要推送时请运行 githubupload.bat
echo.

pause