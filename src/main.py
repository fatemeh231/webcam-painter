import os
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from app.window import PainterApp


if __name__ == "__main__":
    app = PainterApp()
    app.mainloop()