import sys
import os
from ui_login import LoginUI



if __name__ == '__main__':

    # Ensure executable directory is in sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    logged_in = LoginUI()
    logged_in.run()