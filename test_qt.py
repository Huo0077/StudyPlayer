import sys
from PyQt5.QtWidgets import QApplication, QLabel
try:
    app = QApplication(sys.argv)
    label = QLabel("Hello World")
    label.show()
    print("Window shown")
    # 不要调用 exec_，直接退出
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
