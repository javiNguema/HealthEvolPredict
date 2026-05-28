import sys
import os
from ui_login import LoginUI
from utils import kill_ollama_process


if __name__ == '__main__':

    # Ensure executable directory is in sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    kill_ollama_process()
    app = LoginUI()
    app.mainloop()