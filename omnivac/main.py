import sys
import comports_manager
import os
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, 
    QHBoxLayout, QLabel, QLineEdit,
    QSizePolicy, QVBoxLayout, QComboBox,
    QWidget, QSpacerItem
)
from PySide6.QtCore import (
    QRegularExpression, QTimer, Qt, 
    QPoint, QUrl, QThread
)
from PySide6.QtGui import QRegularExpressionValidator, QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from sidebar import Ui_MainWindow
from motor_manager import MotorManager
from ini_manager import IniManager
from controller import ControllerManager
from worker import Worker
from toast import Toast
from pop_up import PopUp

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        if getattr(sys, 'frozen', False):
            # Path for .exe execution
            self.current_dir = os.path.dirname(sys.executable)
        else:
            # Path for .py execution
            self.current_dir = os.path.dirname(os.path.abspath(__file__)) 
            
        self.setWindowIcon(QIcon(self.current_dir + "/icon/omnivac.ico"))

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Omnivac - UiRobot")

        self.ui.icon_only_widget.hide()
        self.ui.stackedWidget.setCurrentIndex(0)

        self.pop_up = PopUp()
        self.ini_manager = IniManager()
        self.motor_manager = None # dummyport
        self.controller_manager = None
        
        self.input_reset: dict[int, QLineEdit] = {}
        self.input_position: dict[int, QLineEdit] = {}
        self.label_dict: dict[int, QLabel] = {}             # Position label
        self.duplicate_label_dict: dict[int, list[QLabel]] = {}
        self.label_name_dict: dict[int, QLabel] = {}
        self.motors = {}
    
        self.timer2 = None

        regex = QRegularExpression(r"^-?[0-9.]*$")
        self.validator = QRegularExpressionValidator(regex)

        self.worker_thread = QThread()
        self.worker = Worker(self.motor_manager, self.motors)
        self.worker.moveToThread(self.worker_thread)

        self.worker.update_signal.connect(self.on_update_label_degree, Qt.QueuedConnection)
        self.worker.popup_signal.connect(self.show_popup)
        self.worker.stop_motor_signal.connect(self.stop_motor)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

        # --- Logic for the Comport Page ---

        self.ui.combo_port.addItems(comports_manager.getActivePorts())
        self.ui.combo_baud.addItems(['9600', '14400', '19200', '38400', '57600', '115200'])
        self.ui.combo_byte.addItems(['8', '7', '6', '5'])
        self.ui.combo_parity.addItems(["None", 'Odd', 'Even', 'Mark', 'Space'])
        self.ui.combo_stop.addItems(['1', '1.5', '2'])

        self.ui.btn_connect.clicked.connect(self.on_btn_connect_clicked)

        
        # --- Logic for Sidbars + misc ---
        
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

        self.ui.enable_all_btn.clicked.connect(self.on_enable_all_clicked)
        self.ui.enable_all_btn2.clicked.connect(self.on_enable_all_clicked)
        self.ui.disable_all_btn.clicked.connect(self.on_disable_all_clicked)
        self.ui.disable_all_btn2.clicked.connect(self.on_disable_all_clicked)
        self.ui.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        self.ui.stop_btn2.clicked.connect(self.on_stop_btn_clicked)
        self.ui.reset_btn.clicked.connect(self.on_reset_btn_clicked)
        self.ui.reset_btn2.clicked.connect(self.on_reset_btn_clicked)

        
        # --- Logic for info page ---
        
        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)

        layout = QVBoxLayout(self.ui.page_4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.webView)

        if getattr(sys, 'frozen', False):
            # Path for execution as .exe
            base_path = os.path.dirname(sys.executable)
        else:
            # Path for execution as .py
            base_path = os.path.dirname(os.path.abspath(__file__))

        base_path = base_path.replace("\\omnivac", "")

        pdf_full_path = os.path.join(base_path, "docs", "help.pdf")
        pdf_url = QUrl.fromLocalFile(pdf_full_path)
        
        self.webView.load(pdf_url)
    
    # --- Functions for Sidbars + misc ---
    
    def show_toast(self, text: str) -> None:
        toast = Toast(f'{text}', self)

        toast.adjustSize()

        margin = 20
        parent_rect = self.rect()
        toast_size = toast.size()

        x = parent_rect.width() - toast_size.width() - margin
        y = parent_rect.height() - toast_size.height() - margin

        global_pos = self.mapToGlobal(QPoint(x, y))

        toast.show_at(global_pos)

    def on_stackedWidget_changed(self, index):
        '''Change QPushButton checkable status when stackedWidget index changed'''
        btn_list = self.ui.icon_only_widget.findChildren(QPushButton) \
                    + self.ui.full_menu_widget.findChildren(QPushButton)

        for btn in btn_list:
            if index in [4, 6]:
                btn.setAutoExclusive(False)
                btn.setChecked(False)
            else:
                btn.setAutoExclusive(True)

    # --- function for changing menu page ---
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

    def closeEvent(self, event):
        print("Programm wird geschlossen.")
    
        self.motor_manager.disable_motors()

        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()

        event.accept()

    # --- functions for motors ---
    def on_enable_all_clicked(self):
        self.motor_manager.enable_motors()

    def on_disable_all_clicked(self):
        self.motor_manager.disable_motors()

    def on_stop_btn_clicked(self):
        self.motor_manager.stop_motors()

    def on_reset_btn_clicked(self) -> None:
        for id, widget in self.input_reset.items():
            input = widget.text()

            if input != "":
                self.motor_manager.send_ORG(id, input)

            widget.setText("")
    
    # --- Functions for Comport Page ---

    def on_btn_connect_clicked(self):
        self.ui.btn_connect.setEnabled(False)
        QTimer.singleShot(3000, lambda: self.ui.btn_connect.setEnabled(True))
        # Current connection closes if existing
        if hasattr(self, 'motor_manager') and self.motor_manager is not None:
                self.motor_manager.transport.close()
                self.motor_manager = None
                print("closed prior connection")

        # Actual port connection
        port = self.ui.combo_port.currentText()
        baud = self.ui.combo_baud.currentText()
        byte = self.ui.combo_byte.currentText()
        parity = self.ui.combo_parity.currentText()
        stop = self.ui.combo_stop.currentText()

        transport = comports_manager.initializePort(port, baud, parity, stop, byte)
        self.motor_manager = MotorManager(transport)
        self.worker.motor_manager = self.motor_manager
        self.motors = self.motor_manager.check_feedback_addresses()
        self.worker.motors = self.motors

        # Creates motor + reset page with found motors and connects controller
        self.duplicate_label_dict.clear()
        self.input_position.clear()
        self.input_reset.clear()
        self.label_dict.clear()
        self.populate_widget(self.ui.scrollAreaWidgetContents, len(self.motors))
        self.populate_widget(self.ui.scrollAreaWidgetContents_2, len(self.motors))
        self.controller_manager = ControllerManager(self.motor_manager, self.ini_manager, self.label_name_dict, self.pop_up)
        self.start_controller_loop()
        self.show_toast("Connected to Comport")

        for id in self.motors.keys():
            self.motor_manager.start_config_motor(id)
            time.sleep(0.1)

    # --- Layout for motor Page + reset page ---

    def populate_widget(self, scroll_widget, motor_rows: int):
        old_layout = scroll_widget.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        # new layout
        layout = QVBoxLayout(scroll_widget)

        # 1. Add Header
        if scroll_widget == self.ui.scrollAreaWidgetContents:
            headers = ["Name", "Target Pos", "Current Pos", "Preset"] 
        else:
            headers = ["Name", "Reset Pos", "Current Pos"]

        header_layout = self.create_header_row_layout(scroll_widget, headers)
        layout.addLayout(header_layout)
        layout.addSpacing(10)

        column_count = len(headers)

        #2. Add all motors
        for row in range(motor_rows):
            h_layout = self.create_motor_info_layout(scroll_widget, row, column_count)
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

        if scroll_widget == self.ui.scrollAreaWidgetContents:
            confirm_btn.clicked.connect(self.on_confirm_btn_clicked)
        else:
            confirm_btn.clicked.connect(self.on_reset_btn_clicked)

        layout.addWidget(confirm_btn, alignment=Qt.AlignHCenter)

        v_spacer = QSpacerItem(20, 200, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout.addItem(v_spacer)


        return layout 

    def create_header_row_layout(self, parent_widget, headers: list[str]) -> QHBoxLayout:
        '''Creates the header row in a widget'''
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

            layout.addWidget(label)

        return layout   

    def create_motor_info_layout(self, parent_widget, row: int, column_count: int) -> QHBoxLayout:
        '''Creates a QHBoxLayout with fixed spacer'''
        layout = QHBoxLayout()
        layout.setObjectName("motor_info_layout")

        # To get the first motor, id from self.motors
        tuple_list = list(self.motors.items())
        motor_tuple = tuple_list[row]

        if parent_widget == self.ui.scrollAreaWidgetContents:
            # Creates widgets for motor page
            for i in range(column_count):
                if i == 0:
                    label = QLabel(parent_widget)
                    label.setObjectName("name_label")
                    label.setText(f"{self.ini_manager.get_value(motor_tuple[0], "Soft_Basic", "Device_Name")}")
                    label.setMinimumWidth(75)
                    label.setMaximumWidth(200)
                    layout.addWidget(label)
                    self.label_name_dict[motor_tuple[0]] = label
                elif i == 1:
                    input = QLineEdit(parent_widget)

                    # settings for widget
                    max_pos = float(motor_tuple[1].max_position)
                    min_pos = float(motor_tuple[1].min_position)
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
                    first_pos = motor_tuple[1].get_motor_pos()
                    label.setText(f"{first_pos} {motor_tuple[1].positon_unit}")
                    label.setMinimumWidth(100)
                    label.setMaximumWidth(300)
                    layout.addWidget(label)
                    self.label_dict[motor_tuple[0]] = label
                elif i == 3:
                    combo_box = QComboBox(parent_widget)
                    combo_box.setObjectName("preset_combo_box")
                    id = motor_tuple[0]
                    presets = self.ini_manager.get_preset_positions_from_motor(id)
                    preset_names = list(presets.keys())
                    preset_names.insert(0, "None")
                    combo_box.addItems(preset_names)
                    combo_box.setMinimumWidth(100)
                    combo_box.setMaximumWidth(300)
                    combo_box.setMinimumHeight(50)
                    combo_box.currentTextChanged.connect(
                        lambda: self.on_combo_selection_changed(motor_tuple[0], combo_box.currentIndex())
                        )
                    layout.addWidget(combo_box)
        else:
            # Creates widget for reset page
            for i in range(column_count):
                if i == 0:
                    label = QLabel(parent_widget)
                    label.setObjectName("name_label")
                    label.setText(f"{self.ini_manager.get_value(motor_tuple[0], "Soft_Basic", "Device_Name")}")
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
                        text = f"{first_pos} {motor_tuple[1].positon_unit}"
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

                        # saving for sync
                        if motor_tuple[0] not in self.duplicate_label_dict:
                            self.duplicate_label_dict[motor_tuple[0]] = []
                        self.duplicate_label_dict[motor_tuple[0]].append(duplicate_label)

        return layout
    
    # --- Functions for Motor Page ---

    def steps_to_unit(self, motor_Id, steps) -> float:
        ''' Connverts steps to mm/degree'''
        encoder: str = self.ini_manager.get_value(motor_Id, 'Hard_Info', 'Ava_Encoder') # the string will be "1" or "0"
        pos_factor = float(self.ini_manager.get_value(motor_Id, 'Soft_Basic', 'Position_Factor'))

        if encoder == "1":
            unit = float((steps / 2000) * 360 * pos_factor)
        else:
            unit = float((steps / 3200) * 360 * pos_factor)

        return  unit

    def on_confirm_btn_clicked(self) -> None:
        input_list: list[tuple[int, float]] = []

        for id, widget in self.input_position.items():                
            input = widget.text()

            if input == "":
                continue
            
            motor = self.motors.get(id)
            input = float(input)

            if self.motor_manager.range_check(motor, input):
                input_list.append((id, input))
            else:
                self.show_toast(f"Value out of range at motor {motor}")
                return

            if id in [74,75]:
                other_id = 75 if id == 74 else 74
                other_widget = self.input_position.get(other_id)
                other_input = other_widget.text()

                if self.motor_manager.x_y_movement_check(motor, input, other_id, other_input):
                    self.show_toast("x and y out of range")
                    return
                
            #if id in [5,6,7]: # collision check for x,y,z
                #self.ccd_check(self.input_position) muss noch getestet werden -todo
                    
        for input in input_list:
            self.motor_manager.move_motor(input[0], input[1])

    def on_combo_selection_changed(self, id: int, selected_index: int) -> None:
        if selected_index == 0:
            widget = self.input_position.get(id)
            widget.setText("")
        else:
            value = self.ini_manager.get_value(id, "Preset_Position", f"Value{selected_index}")
            widget = self.input_position.get(id)
            widget.setText(value)

    def truncate(self, f: float, n: int) -> float:
        truncated = int(f * 10**n) / 10**n
        return f"{truncated:.3f}"

    def start_controller_loop(self) -> None:
        if self.timer2 is not None:
            if self.timer2.isActive():
                self.timer2.stop()
            self.timer2.deleteLater()
            self.timer2 = None

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.controller_manager.controller)
        self.timer2.start(50)

    def clear_layout(self, container_widget) -> None:
        layout = container_widget.layout()
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
            else:
                del item

        layout.deleteLater()

    # --- Signals for thread ---

    def on_update_label_degree(self, motor_id: int, text: str):
        # Original-Label updaten
        label = self.label_dict.get(motor_id)

        if label is not None:
            label.setText(text)

        # Duplicate Labels updaten
        duplicate_labels = self.duplicate_label_dict.get(motor_id, [])
        for dup_label in duplicate_labels:
            dup_label.setText(text)

    def stop_motor(self, motor_id):
        self.motor_manager.stop_motors()

    def show_popup(self, message):
        self.pop_up.show_popup(message)

if __name__ == "__main__":
    # Path for exe or script
    if getattr(sys, 'frozen', False):
        log_path = os.path.join(os.path.dirname(sys.executable), "log.txt")
    else:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
    
    print("=== Omnivac gestartet ===")

    app = QApplication(sys.argv)

    # loading style file
    with open("resources/style.qss", "r") as style_file:
        style_str = style_file.read()
    app.setStyleSheet(style_str)
 
    window = MainWindow()
    window.show()

    sys.exit(app.exec())