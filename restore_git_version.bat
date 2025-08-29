@echo off
chcp 65001
REM 显示最近的提交历史
echo.
echo ==== 最近的提交历史（版本号在最左侧） ====
git log --oneline -20
echo.
set /p ver=请输入要还原的版本号（如 abcd123）： 

REM 检查输入
if "%ver%"=="" (
    echo 请输入有效的版本号！
    pause
    exit /b
)

REM 确认操作
echo.
echo 即将还原到版本 %ver%，本地未提交的更改将会丢失！
set /p confirm=是否继续？(y/n): 
if /i not "%confirm%"=="y" (
    echo 已取消操作。
    pause
    exit /b
)

REM 强制还原到指定版本
git reset --hard %ver%

echo.
echo 已还原到版本 %ver%！

REM 询问是否强制推送到远程
set /p pushconfirm=是否将该版本强制推送到远程仓库？(y/n): 
if /i "%pushconfirm%"=="y" (
    git push origin master --force
    echo 已强制推送到远程 master 分支！
) else (
    echo 未推送到远程。
)

pause