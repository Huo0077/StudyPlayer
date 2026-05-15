import sys
import os
import traceback

def main():
    try:
        # 确保当前目录在 Python 路径中
        basedir = os.path.dirname(os.path.abspath(__file__))
        if basedir not in sys.path:
            sys.path.insert(0, basedir)
            
        # 强制将工作目录切换到程序所在目录，防止右键打开时报 PermissionError
        os.chdir(basedir)

        from utils import register_file_association
        register_file_association()

        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        import faulthandler
        
        # 启用故障处理程序，捕捉段错误
        f = open("faulthandler_log.txt", "w", encoding="utf-8")
        faulthandler.enable(f)
        
        # 高 DPI 支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        app = QApplication(sys.argv)
        
        # 捕捉在 Qt 事件循环中发生的未处理异常
        def my_excepthook(type, value, tback):
            import traceback
            err_msg = "".join(traceback.format_exception(type, value, tback))
            print("QT CRASH DETECTED!")
            print(err_msg)
            with open("crash_report_v2.txt", "w", encoding="utf-8") as f:
                f.write(err_msg)
            sys.__excepthook__(type, value, tback)
            sys.exit(1)
        sys.excepthook = my_excepthook
        
        # 此时才导入可能失败的模块
        import main_logic
        from video_widget import VLC_AVAILABLE
        
        if not VLC_AVAILABLE:
            QMessageBox.critical(
                None, 
                "环境错误", 
                "未检测到 VLC 播放环境！\n\n"
                "请确保程序目录下存在 vlc_runtime 文件夹，\n"
                "或者您的系统中已安装 64 位 VLC 播放器。"
            )
            sys.exit(1)
            
        main_logic.run_app(app)
        
    except Exception as e:
        print("CRASH DETECTED!")
        print(traceback.format_exc())
        with open("crash_report_v2.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
