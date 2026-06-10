from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer

from src.ui.main_window import MainWindow
from application_manager import ApplicationManager

import sys 

if __name__ == "__main__":
    print("=== Omnivac gestartet ===")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    with open ("resources/style.qss", "r") as style_file:
        app.setStyleSheet(style_file.read())
    
    window = MainWindow()
    window.show()

    # Initialize application manager
    app_manager = ApplicationManager(window)

    # Ensure worker threads are stopped before Qt tears objects down
    app.aboutToQuit.connect(app_manager.shutdown)
    
    sys.exit(app.exec())