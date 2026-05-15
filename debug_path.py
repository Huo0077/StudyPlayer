import sys
import os
import player_window
print(f"Python: {sys.executable}")
print(f"Path: {sys.path}")
print(f"PlayerWindow file: {player_window.__file__}")
from player_window import PlayerWindow
try:
    p = PlayerWindow()
    print("Instance created")
    print(f"Signal type: {type(p.video_widget.openFileRequested)}")
except Exception as e:
    import traceback
    print(traceback.format_exc())
