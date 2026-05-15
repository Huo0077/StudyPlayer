@echo off
echo =========================================
echo 极简视频播放器 - 一键打包构建脚本
echo =========================================

REM 清理旧的构建文件
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo 正在使用 PyInstaller 打包程序 (不显示控制台窗口)...
pyinstaller --noconsole --name "StudyPlayer" --icon="app_icon.ico" main.py

echo =========================================
echo 打包完成！生成的文件位于 dist\StudyPlayer 目录下。
echo 注意：如果在其他电脑上运行，目标电脑必须安装 VLC 播放器，
echo 或者您需要将 VLC 的 libvlc.dll, libvlccore.dll 以及 plugins 文件夹
echo 拷贝到 dist\StudyPlayer 目录中。
echo =========================================
pause
