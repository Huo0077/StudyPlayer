import os
import sys
import shutil
import subprocess
import zipfile

def create_manual():
    manual_content = """=========================================
StudyPlayer v11 - 使用说明
=========================================

这是一个基于 PyQt5 和 VLC 核心的高级视频播放器，旨在为您提供最纯净、最高效的观影与学习体验。

【快速上手】
- 直接运行 StudyPlayer.exe 即可启动。
- 本压缩包已内置 VLC 解码环境，无需额外安装任何软件。

【📂 笔记与导出位置】
为了方便您整理和备份学习资料，软件的所有产出都保存在程序所在文件夹内：
1. 汇总笔记长图：存放在 notes_aggregated 文件夹下。
2. 视频截图：存放在 snapshots 文件夹下。
3. 原始数据备份：存放在 metadata 文件夹下（JSON 格式）。
4. 历史记录：存放在 progress.txt 文件中。

【核心快捷键】
- Space: 播放/暂停
- 方向左/右键: 后退/快进 10s
- 方向右键(长按): 3 倍速极速快进
- 方向上/下键: 音量控制
- Ctrl + Z / Y: 笔记撤销/重做
- Ctrl + S: 手动保存当前所有数据
- F / F11: 全屏切换
- S: 瞬间截图

=========================================
"""
    target_dir = os.path.join("dist", "StudyPlayer")
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, "使用说明.txt"), "w", encoding="utf-8") as f:
        f.write(manual_content)
    print("[1/4] 使用说明文档已生成。")

def build_exe():
    print("[2/4] 正在调用 PyInstaller 进行打包，请耐心等待...")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--name=StudyPlayer",
        "--icon=app_icon.ico",
        "--noconfirm",
        "main.py"
    ]
    subprocess.run(cmd, check=True)
    print("打包完成！")

def copy_runtime():
    print("[3/4] 正在整合 VLC 解码环境...")
    source_vlc = os.path.join(os.getcwd(), "vlc_runtime")
    target_vlc = os.path.join("dist", "StudyPlayer", "vlc_runtime")
    
    if os.path.exists(source_vlc):
        if os.path.exists(target_vlc):
            shutil.rmtree(target_vlc)
        shutil.copytree(source_vlc, target_vlc)
        print("VLC 运行库整合成功。")
    else:
        print("警告: 未在当前目录找到 vlc_runtime 文件夹！")
        print("生成的包可能无法在未安装 VLC 的电脑上运行。")
        print("建议：先运行一次程序（或运行 run.bat）以自动下载解码器。")

def create_zip():
    print("[4/4] 正在生成最终分享压缩包 (v11)...")
    
    output_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
    zip_path = os.path.join(output_dir, "StudyPlayer_v11_Portable.zip")
    
    source_dir = os.path.join("dist", "StudyPlayer")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arcname)
                
    print(f"\n=========================================")
    print(f"构建成功！最终压缩包位于:")
    print(f"   {zip_path}")
    print(f"你可以直接将此压缩包分享给他人。")
    print(f"=========================================")

if __name__ == "__main__":
    try:
        build_exe()
        create_manual()
        copy_runtime()
        create_zip()
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
