from PySide6.QtWidgets import QMainWindow, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import QUrl, QThread
from PySide6.QtWebEngineWidgets import QWebEngineView

from omnivac.ui.generated.sidebar import Ui_MainWindow
from omnivac.controllers.main_controller import MainController

import sys
import os
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"{QThread.currentThread()}")

        # Path for Ressources
        self.current_dir = self._get_base_path()

        # UI Setup
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Omnivac - UiRobot")
        self.setWindowIcon(QIcon(os.path.join(self.current_dir, "resources/icon/omnivac.ico")))
        
        # Initial UI State
        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.comport_btn.setChecked(True)
        
        # Help Page Setup (PDF Viewer)
        self._setup_help_page()
        
        # Controller erstellen (übernimmt Event-Handling)
        self.controller = MainController(self)


    def _get_base_path(self) -> str:
        """Return Path for Ressources"""
        if getattr(sys, 'frozen', False):
            path =  os.path.dirname(sys.executable)
        else:
            path =  os.path.dirname(os.path.abspath(__file__))

        self.logger.debug(f"Chosen path: " +  str(path))

        return path
        
    def _setup_help_page(self):
        """Sets the PDF-Viewer up"""
        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(
            self.webView.settings().WebAttribute.PluginsEnabled, True
        )
        self.webView.settings().setAttribute(
            self.webView.settings().WebAttribute.PdfViewerEnabled, True
        )
        
        layout = QVBoxLayout(self.ui.page_4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.webView)
        
        pdf_path = os.path.join(self.current_dir, "docs", "help.pdf")
        pdf_url = QUrl.fromLocalFile(pdf_path)
        self.webView.load(pdf_url)

    def closeEvent(self, event):
        """Cleanup on closing"""
        print("Programm wird geschlossen")
        self.controller.cleanup()
        event.accept()