"""工具函数模块"""

import os
import sys

# 支持的视频文件扩展名
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.3gp', '.ts', '.vob', '.rmvb', '.rm'
}


def format_time(ms):
    """将毫秒转换为 HH:MM:SS 格式的字符串"""
    if ms < 0:
        ms = 0
    seconds = int(ms / 1000)
    minutes = seconds // 60
    hours = minutes // 60
    seconds = seconds % 60
    minutes = minutes % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def is_video_file(filepath):
    """判断文件是否为视频文件"""
    _, ext = os.path.splitext(filepath)
    return ext.lower() in VIDEO_EXTENSIONS


def get_video_files_from_dir(directory):
    """从目录中获取所有视频文件"""
    video_files = []
    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and is_video_file(filepath):
            video_files.append(filepath)
    return video_files


def get_filename(filepath):
    """获取文件名（不含路径）"""
    return os.path.basename(filepath)


def get_app_root():
    """获取程序运行根目录（兼容 PyInstaller 打包后的路径）"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe 运行
        return os.path.dirname(sys.executable)
    else:
        # 如果是脚本直接运行
        return os.path.dirname(os.path.abspath(__file__))


def register_file_association():
    """将程序自动注册到 Windows '打开方式' (免管理员权限)"""
    if sys.platform != 'win32' or not getattr(sys, 'frozen', False):
        return
        
    try:
        import winreg
        exe_path = os.path.abspath(sys.executable)
        
        # 打开 HKCU\Software\Classes
        classes_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes", 0, winreg.KEY_ALL_ACCESS)
        
        # 1. 注册应用到 Applications
        app_key = winreg.CreateKey(classes_key, r"Applications\StudyPlayer.exe")
        winreg.SetValueEx(app_key, "FriendlyAppName", 0, winreg.REG_SZ, "StudyPlayer")
        
        supported_types = winreg.CreateKey(app_key, "SupportedTypes")
        winreg.SetValueEx(supported_types, ".mp4", 0, winreg.REG_SZ, "")
        
        command_key = winreg.CreateKey(app_key, r"shell\open\command")
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        # 2. 关联 .mp4 的 OpenWithProgids
        mp4_key = winreg.CreateKey(classes_key, r".mp4\OpenWithProgids")
        winreg.SetValueEx(mp4_key, "StudyPlayer.mp4", 0, winreg.REG_SZ, "")
        
        progid_key = winreg.CreateKey(classes_key, "StudyPlayer.mp4")
        winreg.SetValueEx(progid_key, "", 0, winreg.REG_SZ, "StudyPlayer Media File")
        
        icon_key = winreg.CreateKey(progid_key, "DefaultIcon")
        winreg.SetValueEx(icon_key, "", 0, winreg.REG_SZ, f'{exe_path},0')
        
        progid_cmd_key = winreg.CreateKey(progid_key, r"shell\open\command")
        winreg.SetValueEx(progid_cmd_key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        
    except Exception as e:
        print(f"自动注册文件关联失败: {e}")
