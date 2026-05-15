@echo off
setlocal enabledelayedexpansion

echo 正在检查播放环境...

:: 检查是否已经有 VLC 运行时
if not exist "vlc_runtime\libvlc.dll" (
    echo [提示] 未检测到解码器环境，正在启动安装向导...
    python setup_wizard.py
    exit
)

:: 启动播放器
echo 正在启动视频播放器...
python main.py
if %errorlevel% neq 0 (
    echo 启动失败，正在尝试修复依赖...
    pip install -r requirements.txt
    python main.py
)
pause
