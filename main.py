from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer

from omnivac.ui.views.main_window import MainWindow
from omnivac.config.ini_manager import IniManager


import sys 

if __name__ == "__main__":
    print("=== Omnivac gestartet ===")

    app = QApplication(sys.argv)

    with open ("resources/style.qss", "r") as style_file:
        app.setStyleSheet(style_file.read())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())