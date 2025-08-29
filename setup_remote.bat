@echo off
chcp 65001 >nul

echo ========================================
echo    Git远程仓库配置脚本
echo ========================================
echo.

echo 当前远程仓库配置:
git remote -v
echo.

echo 正在更新远程仓库配置...
echo 移除当前远程配置...
git remote remove origin

echo 添加新的远程仓库: https://github.com/oceanzhang2014/autogen_code.git
git remote add origin https://github.com/oceanzhang2014/autogen_code.git

echo.
echo 验证新的远程配置:
git remote -v
echo.

echo 设置上游分支...
git branch --set-upstream-to=origin/main main

echo.
echo ========================================
echo    远程仓库配置完成!
echo ========================================
echo 现在可以使用 githubupload.bat 推送到你的仓库
echo.

pause