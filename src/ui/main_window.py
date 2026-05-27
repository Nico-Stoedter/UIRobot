from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QSpacerItem, 
    QSizePolicy, QLabel, QLineEdit, 
    QComboBox
)

from PySide6.QtGui import (
    QIcon, Qt, QRegularExpressionValidator, 
    QPixmap
)
from PySide6.QtCore import (
    QUrl, QTimer, Slot, 
    QRegularExpression, Signal
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.ui.sidebar import Ui_MainWindow
from src.config_manager import ConfigManager

import serial.tools.list_ports
import sys
import os

class MainWindow(QMainWindow):

    motor_page_created = Signal(QPushButton)
    reset_page_created = Signal(QPushButton)

    def __init__(self):
        super().__init__()
        # Path for Ressources
        self.current_dir = self._get_base_path()
        self.config_manager = ConfigManager()

        # UI Setup
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Omnivac - UiRobot")
        self.setWindowIcon(QIcon(os.path.join(self.current_dir, "resources/icon/omnivac.ico")))

        self.input_position: dict[int, QLineEdit] = {}  # References for User Input UI in Motor Page
        self.input_reset: dict[int, QLineEdit] = {}     #                              in Reset Page        
        self.label_dict: dict[int, QLabel] = {}                 # Motor Position Label References in Motor Page
        self.duplicate_label_dict: dict[int, QLabel] = {} #                                 in Reset Page
        self.label_name_dict: dict[int, QLabel] = {}
        self.png_label_dict: dict[int, QLabel] = {}

        regex = QRegularExpression(r"^-?[0-9.]*$")
        self.validator = QRegularExpressionValidator(regex)
        
        # Initial UI State
        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)
        self.ui.comport_btn.setChecked(True)
        
        # Help Page Setup (PDF Viewer)
        self._setup_comport_page()
        self._setup_help_page()
        self._setup_motor_page()

        # --- Signale für Sidebar ---
        self.ui.comport_btn.toggled.connect(self.on_comport_toggled)
        self.ui.comport_btn2.toggled.connect(self.on_comport_toggled)
        self.ui.motor_btn.toggled.connect(self.on_motor_toggled)
        self.ui.motor_btn2.toggled.connect(self.on_motor_toggled)
        self.ui.help_btn.toggled.connect(self.on_help_toggled)
        self.ui.help_btn2.toggled.connect(self.on_help_toggled)
        self.ui.reset_btn.toggled.connect(self.on_reset_toggled)
        self.ui.reset_btn2.toggled.connect(self.on_reset_toggled)
        self.ui.stackedWidget.setCurrentIndex(0)  # Comport-Seite anzeigen
        self.ui.comport_btn.setChecked(True)

        #self.ui.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        #self.ui.stop_btn2.clicked.connect(self.on_stop_btn_clicked)
        #self.ui.reset_btn.clicked.connect(self.on_reset_btn_clicked)
        #self.ui.reset_btn2.clicked.connect(self.on_reset_btn_clicked)

    def _get_base_path(self) -> str:
        """Return Path for Ressources"""
        if getattr(sys, 'frozen', False):
            path =  os.path.dirname(sys.executable)
        else:
            path =  os.path.dirname(os.path.abspath(__file__))

        return path

    # --- Sidebar Button Function for Changing Page ---

    def on_comport_toggled(self, checked):
        if checked:
            self.ui.stackedWidget.setCurrentIndex(0)

    def on_motor_toggled(self, checked):
        if checked:
            self.ui.stackedWidget.setCurrentIndex(1)

    def on_reset_toggled(self, checked):
        if checked:
            self.ui.stackedWidget.setCurrentIndex(3)

    def on_help_toggled(self, checked):
        if checked:
            self.ui.stackedWidget.setCurrentIndex(2)
    
    # --- Comport Page Setup --- 

    def _setup_comport_page(self):
        """Initialisiert die UI-Komponenten"""
        
        self.ui.combo_port.addItems(self.getActivePorts())
        self.ui.combo_baud.addItems(['9600', '14400', '19200', '38400', '57600', '115200'])
        self.ui.combo_byte.addItems(['8', '7', '6', '5'])
        self.ui.combo_parity.addItems(["None", 'Odd', 'Even', 'Mark', 'Space'])
        self.ui.combo_stop.addItems(['1', '1.5', '2'])

    def getActivePorts(self) -> list:
        '''Gets all comports found and returns a list'''
        comport_list = []
        for i in serial.tools.list_ports.comports():
            i = str(i)[0:5] #Wählt die Zeichen im String die die Comportbezeichnung enthalten
            comport_list.append(i)
        if comport_list == []:
            return ["No comport found"]
        else:
            return comport_list
    
    def get_connection_settings(self) -> dict:
        """Gibt die aktuellen Connection-Einstellungen zurück"""
        return {
            'port': self.ui.combo_port.currentText(),
            'baud': self.ui.combo_baud.currentText(),
            'byte': self.ui.combo_byte.currentText(),
            'parity': self.ui.combo_parity.currentText(),
            'stop': self.ui.combo_stop.currentText()
        }
    
    def disable_connect_button_temporarily(self, milliseconds: int = 3000):
        """Deaktiviert den Connect-Button temporär"""
        self.ui.btn_connect.setEnabled(False)
        QTimer.singleShot(milliseconds, lambda: self.ui.btn_connect.setEnabled(True))
        
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

    # --- Setup for Motor Page + Reset Page---
    @Slot(int)
    def _setup_motor_page(self, motor_dict={}):
        motor_page_widget = self.ui.scrollAreaWidgetContents
        reset_page_widget = self.ui.scrollAreaWidgetContents_2
        self.create_motor_page_widgets(motor_page_widget, len(motor_dict), motor_dict)

        self.create_motor_page_widgets(reset_page_widget, len(motor_dict), motor_dict)
        

    def create_motor_page_widgets(self, scroll_widget, motor_rows: int, motor_dict):
        old_layout = scroll_widget.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        # new layout
        layout = QVBoxLayout(scroll_widget)

        # 1. Add Header
        if scroll_widget == self.ui.scrollAreaWidgetContents:
            headers = ["Name", "Target Pos", "Current Pos", "Preset", "Status"] 
        else:
            headers = ["Name", "Reset Pos", "Current Pos"]

        header_layout = self.create_header_row_layout(scroll_widget, headers)
        layout.addLayout(header_layout)
        layout.addSpacing(10)

        column_count = len(headers)

        #2. Add all motors
        for row in range(motor_rows):
            h_layout = self.create_motor_info_layout(scroll_widget, row, column_count, motor_dict)
            layout.addLayout(h_layout)

            # Vertical Spacer (except last row)
            if row < motor_rows:
                layout.addSpacing(10)

        # 3. Add bottom button
        confirm_btn = QPushButton("Confirm", scroll_widget)
        confirm_btn.setObjectName("confirm_button")
        confirm_btn.setStyleSheet("margin-top: 20px; font-size: 18px;")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        confirm_btn.setMinimumWidth(200)
        confirm_btn.setMaximumWidth(400)
        confirm_btn.setMinimumHeight(50)
        confirm_btn.setMaximumHeight(80)
        confirm_btn.setSizePolicy(sizePolicy)

        # Connect Btn to its Corresponding Function
        if scroll_widget == self.ui.scrollAreaWidgetContents:
            self.motor_page_created.emit(confirm_btn)
        else:
            self.reset_page_created.emit(confirm_btn)

        layout.addWidget(confirm_btn, alignment=Qt.AlignHCenter)

        v_spacer = QSpacerItem(20, 200, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout.addItem(v_spacer)

        return layout 

    def create_header_row_layout(self, parent_widget, headers: list[str]) -> QHBoxLayout:
        '''Creates the header row in the ScrollAreaWidget'''
        layout = QHBoxLayout()
        layout.setObjectName("header_row_layout")

        for i, title in enumerate(headers):
            label = QLabel(parent_widget)
            label.setText(title)
            label.setObjectName(f"header_label_{i}")
            label.setStyleSheet("font-weight: bold;")
            size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setSizePolicy(size_policy)

            label.setMaximumHeight(50)

            #QLabel(name)
            if i == 0:
                label.setMinimumWidth(75)
                label.setMaximumWidth(200)

            #QLineInput
            if i == 1:
                label.setMinimumWidth(100)
                label.setMaximumWidth(350)

            #QLabel(position); 
            if i == 2:
                label.setMinimumWidth(100)
                label.setMaximumWidth(300)

            #QComboBox
            if i == 3:
                label.setMinimumWidth(100)
                label.setMaximumWidth(300)

            # HAbe noch keinen Namen für den Scheiß
            if i ==4:
                label.setMinimumWidth(50)
                label.setMaximumWidth(100)

            layout.addWidget(label)

        return layout   

    def create_motor_info_layout(self, parent_widget, row: int, column_count: int, motor_dict) -> QHBoxLayout:
        '''Creates a QHBoxLayout with fixed spacer'''
        layout = QHBoxLayout()
        layout.setObjectName("motor_info_layout")

        # To get the first motor, id from self.motors
        tuple_list = list(motor_dict.items())
        motor_tuple = tuple_list[row]

        if parent_widget == self.ui.scrollAreaWidgetContents:
            # Creates widgets for motor page
            for i in range(column_count):
                if i == 0:
                    label = QLabel(parent_widget)
                    label.setObjectName("name_label")
                    label.setText(f"{motor_tuple[1].device_name}")
                    label.setMinimumWidth(75)
                    label.setMaximumWidth(200)
                    layout.addWidget(label)
                    self.label_name_dict[motor_tuple[0]] = label
                elif i == 1:
                    input = QLineEdit(parent_widget)

                    # settings for widget
                    max_pos = float(motor_tuple[1].max_pos_unit)
                    min_pos = float(motor_tuple[1].min_pos_unit)
                    input.setPlaceholderText(f"∈[{min_pos}, {max_pos}]")

                    self.input_position[motor_tuple[0]] = input
                    input.setObjectName("input_widget")
                    input.setValidator(self.validator)
                    input.setMinimumWidth(100)
                    input.setMaximumWidth(350)
                    input.setMinimumHeight(50)
                    layout.addWidget(input)
                elif i == 2:
                    label = QLabel(parent_widget)
                    label.setObjectName("position_label")
                    first_pos = motor_tuple[1].status.get("rEncoder") # Mögliche Thread Probleme
                    label.setText(f"{first_pos} {motor_tuple[1].unit}")
                    label.setMinimumWidth(100)
                    label.setMaximumWidth(300)
                    label.setMaximumHeight(50)
                    layout.addWidget(label)
                    self.label_dict[motor_tuple[0]] = label
                elif i == 3:
                    combo_box = QComboBox(parent_widget)
                    combo_box.setObjectName("preset_combo_box")
                    id = motor_tuple[0]
                    presets = self.config_manager.get_preset_positions(id)
                    preset_names = list(presets.keys())
                    combo_box.addItems(preset_names)
                    combo_box.setMinimumWidth(100)
                    combo_box.setMaximumWidth(300)
                    combo_box.setMaximumHeight(50)
                    combo_box.currentTextChanged.connect(
                        lambda: self.on_combo_selection_changed(motor_tuple[0], combo_box.currentText())
                        )
                    layout.addWidget(combo_box)
                elif i == 4:
                    png_label = QLabel(parent_widget)
                    png_label.setObjectName("PNG_Lable")
                    
                    pixmap = QPixmap("resources/icon/rot.png")
                    scaled_pixmap = pixmap.scaled(
                        20, 20,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    png_label.setPixmap(scaled_pixmap)
                    png_label.setMinimumWidth(50)
                    png_label.setMaximumWidth(100)
                    png_label.setMinimumHeight(50)
                    png_label.setMaximumHeight(50)
                    png_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.png_label_dict[motor_tuple[0]] = png_label
                    layout.addWidget(png_label)
        else:
            # Creates widget for reset page
            for i in range(column_count):
                if i == 0:
                    label = QLabel(parent_widget)
                    label.setObjectName("name_label")
                    label.setText(f"{motor_tuple[1].device_name}")
                    label.setMaximumHeight(50)
                    label.setMinimumWidth(75)
                    label.setMaximumWidth(200)
                    layout.addWidget(label)
                elif i == 1:
                    input = QLineEdit(parent_widget)

                    # settings for widget
                    input.setPlaceholderText(f"Number")
                    self.input_reset[motor_tuple[0]] = input
                    input.setObjectName("input_widget")
                    input.setValidator(self.validator)
                    input.setMaximumHeight(50)
                    label.setMinimumHeight(50)
                    input.setMinimumWidth(100)
                    input.setMaximumWidth(350)
                    layout.addWidget(input)
                elif i == 2:
                    original_label = self.label_dict.get(motor_tuple[0])

                    if original_label is None:
                        # Fallback (shouldn't happen normally)
                        first_pos = motor_tuple[1].get_motor_pos()
                        text = f"{first_pos} {motor_tuple[1].position_unit}"
                    else:
                        text = original_label.text()

                        # create a new label similar to original
                        duplicate_label = QLabel(parent_widget)
                        duplicate_label.setObjectName("position_label_clone")
                        duplicate_label.setText("Label kaputt")
                        duplicate_label.setText(text)
                        duplicate_label.setMaximumHeight(50)
                        duplicate_label.setMinimumWidth(100)
                        duplicate_label.setMaximumWidth(300)
                        layout.addWidget(duplicate_label)

                        self.duplicate_label_dict[motor_tuple[0]] = duplicate_label

        return layout
    
    def change_pixmap(self, controller_id, png_name) -> None:
        "Changes the Icon displayed on the motor Page"
        png_label = self.png_label_dict.get(controller_id)
        pixmap = QPixmap(f"resources/icon/{png_name}")
        scaled_pixmap = pixmap.scaled(
            20, 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        png_label.setPixmap(scaled_pixmap)

    def on_combo_selection_changed(self, id: int, preset_name: str) -> None:
        print(preset_name)
        value = self.config_manager.get_value(id, "Preset_Positions", f"{preset_name}")
        print(value)
        widget = self.input_position.get(id)
        widget.setText(value)