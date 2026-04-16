from typing import TYPE_CHECKING, Dict

from PySide6.QtCore import QTimer, QThread, Qt, QRegularExpression, Slot
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QMessageBox
from serial import SerialException

from omnivac.config.ini_manager import IniManager
from omnivac.ui.widgets.pop_up import PopUp
from omnivac.ui.widgets.toast import Toast
from omnivac.ui.views.connection_view import ConnectionView
from omnivac.ui.views.motor_view import MotorView
from omnivac.ui.views.reset_view import ResetView
from omnivac.ui.widgets.motor_widgets_factory import MotorWidgetFactory
from omnivac.controllers.gamepad_controller import ControllerManager
from omnivac.workers.worker import Worker

import time
import logging

if TYPE_CHECKING:
    from omnivac.ui.views.main_window import MainWindow
    from omnivac.core.motor_manager import MotorManager
    from omnivac.controllers.gamepad_controller import ControllerManager

class MainController:
    def __init__(self, view: "MainWindow"):
        super().__init__()
        self.view = view

        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"{QThread.currentThread()}")
        # Models/Managers
        self.motor_manager: "MotorManager | None" = None
        self.controller_manager: "ControllerManager | None" = None
        self.ini_manager = IniManager()
        self.pop_up = PopUp()
        
        # Views
        self.connection_view = ConnectionView(self.view.ui)
        self.motor_view = MotorView(self.view.ui)
        self.reset_view = ResetView(self.view.ui)
        
        # Widget Factory
        self.widget_factory = MotorWidgetFactory(self.ini_manager, self.motor_view.validator)
        
        # Worker Thread
        self.worker_thread = QThread()
        self.worker: Worker | None = None
        
        # Timers
        self.controller_timer: QTimer | None = None
        
        # Motors
        self.motors = {}
        
        # Setup
        self._connect_signals()
    
    def _connect_signals(self):
        """Verbindet alle UI-Signale"""
        # Sidebar Navigation
        self.view.ui.comport_btn.toggled.connect(self.on_comport_toggled)
        self.view.ui.comport_btn2.toggled.connect(self.on_comport_toggled)
        self.view.ui.motor_btn.toggled.connect(self.on_motor_toggled)
        self.view.ui.motor_btn2.toggled.connect(self.on_motor_toggled)
        self.view.ui.help_btn.toggled.connect(self.on_help_toggled)
        self.view.ui.help_btn2.toggled.connect(self.on_help_toggled)
        self.view.ui.reset_btn.toggled.connect(self.on_reset_toggled)
        self.view.ui.reset_btn2.toggled.connect(self.on_reset_toggled)
        
        # Motor Controls
        self.view.ui.enable_all_btn.clicked.connect(self.on_enable_all_clicked)
        self.view.ui.enable_all_btn2.clicked.connect(self.on_enable_all_clicked)
        self.view.ui.disable_all_btn.clicked.connect(self.on_disable_all_clicked)
        self.view.ui.disable_all_btn2.clicked.connect(self.on_disable_all_clicked)
        self.view.ui.stop_btn.clicked.connect(self.on_stop_btn_clicked)
        self.view.ui.stop_btn2.clicked.connect(self.on_stop_btn_clicked)
        
        # Connection
        self.view.ui.btn_connect.clicked.connect(self.on_btn_connect_clicked)
    
    # --- Navigation ---
    def on_comport_toggled(self, checked: bool):
        if checked:
            self.view.ui.stackedWidget.setCurrentIndex(0)
    
    def on_motor_toggled(self, checked: bool):
        if checked:
            self.view.ui.stackedWidget.setCurrentIndex(1)
    
    def on_help_toggled(self, checked: bool):
        if checked:
            self.view.ui.stackedWidget.setCurrentIndex(2)
    
    def on_reset_toggled(self, checked: bool):
        if checked:
            self.view.ui.stackedWidget.setCurrentIndex(3)
    
    # --- Motor Controls ---
    def on_enable_all_clicked(self):
        if self.motor_manager:
            self.motor_manager.enable_motors()
    
    def on_disable_all_clicked(self):
        if self.motor_manager:
            self.motor_manager.disable_motors()
    
    def on_stop_btn_clicked(self):
        if self.motor_manager:
            self.motor_manager.stop_motors()
    
    # --- Connection ---
    def on_btn_connect_clicked(self):
        self.connection_view.disable_connect_button_temporarily()
        
        # Close existing connection
        if self.motor_manager is not None:
            self.motor_manager.transport.close()
            self.motor_manager = None
            print("Closed prior connection")
        
        # Get settings and connect
        settings = self.connection_view.get_connection_settings()
        
        try:
            from omnivac.hardware import comports_manager
            from omnivac.core.motor_manager import MotorManager
            
            transport = comports_manager.initializePort(
                settings['port'], settings['baud'], 
                settings['parity'], settings['stop'], settings['byte']
            )
            
            self.motor_manager = MotorManager(transport)
            self.motors = self.motor_manager.check_feedback_addresses()
            
            # Update views
            self._populate_motor_pages()
            
            # Setup controller
            self.controller_manager = ControllerManager(
                self.motor_manager, self.ini_manager, 
                self.motor_view.label_name_dict, self.pop_up
            )
            self._start_controller_loop()
            
            # Start motors
            for motor_id in self.motors.keys():
                self.motor_manager.start_config_motor(motor_id)
                time.sleep(0.1)
            
            # Start worker thread
            self._setup_worker()
            
            self.show_toast("Connected to Comport")
            
        except SerialException:
            self.show_toast("Selected port is already in use")
    
    def _populate_motor_pages(self):
        """Erstellt die Motor- und Reset-Seiten"""
        # Clear old
        self.motor_view.clear()
        self.reset_view.clear()
        
        # Motor Page
        self.widget_factory.create_motor_page_layout(
            self.view.ui.scrollAreaWidgetContents,
            self.motors,
            self.motor_view.label_dict,
            self.motor_view.input_position,
            self.motor_view.label_name_dict,
            self.on_confirm_btn_clicked
        )
        
        # Reset Page
        self.widget_factory.create_reset_page_layout(
            self.view.ui.scrollAreaWidgetContents_2,
            self.motors,
            self.motor_view.label_dict,
            self.reset_view.input_reset,
            self.reset_view.duplicate_label_dict,
            self.on_reset_btn_clicked
        )
    
    def _setup_worker(self):
        """Richtet den Worker-Thread ein"""
        self.worker = Worker(self.motor_manager, self.motors)

        # DEBUG: Thread-Affinity prüfen VORHER
        self.logger.debug(f"Worker thread affinity BEFORE: {self.worker.thread()}")
        self.logger.debug(f"Controller thread affinity: {QThread()}")

        self.worker.moveToThread(self.worker_thread)

        # DEBUG: Thread-Affinity prüfen NACHHER
        self.logger.debug(f"Worker thread affinity AFTER: {self.worker.thread()}")

        self.worker_thread.started.connect(self.worker.run)

        # Connections mit Lambda zum Debuggen
        self.worker.update_signal.connect(
            lambda motor_id, text: self.logger.debug(f"update_signal received: {motor_id}, {text}"),
        )
        self.worker.popup_signal.connect(
            lambda msg: self.logger.debug(f"popup_signal received: {msg}"),
            Qt.QueuedConnection
        )
        self.worker.update_signal.connect(self.on_update_label)
        self.worker.popup_signal.connect(self.show_popup, Qt.QueuedConnection)
        self.worker.stop_motor_signal.connect(self.stop_motor)

        self.logger.info("Worker Thread has been setup")

        # DEBUG: Ist der Thread schon gestartet?
        self.logger.debug(f"Worker thread running: {self.worker_thread.isRunning()}")

        self.worker_thread.start()
    
        # Warte kurz
        QThread.msleep(100)
        self.logger.debug(f"Worker thread running after start: {self.worker_thread.isRunning()}")
    
    def _start_controller_loop(self):
        """Startet den Controller-Loop"""
        if self.controller_timer is not None:
            if self.controller_timer.isActive():
                self.controller_timer.stop()
            self.controller_timer.deleteLater()
        
        self.controller_timer = QTimer(self.view)
        self.controller_timer.timeout.connect(self.controller_manager.controller)
        self.controller_timer.start(20)
    
    # --- Callbacks ---
    def on_confirm_btn_clicked(self):
        """Motor Movement bestätigen"""
        input_values = self.motor_view.get_input_values()
        input_list = []
        
        for motor_id, value in input_values.items():
            if value == "":
                continue
            
            motor = self.motors.get(motor_id)
            value_float = float(value)
            
            if not self.motor_manager.range_check(motor, value_float):
                self.show_toast(f"Value out of range at motor {motor}")
                return
            
            if motor_id in [74, 75]:
                other_id = 75 if motor_id == 74 else 74
                other_value = input_values.get(other_id, "")
                if self.motor_manager.x_y_movement_check(motor, value_float, other_id, other_value):
                    self.show_toast("x and y out of range")
                    return
            
            input_list.append((motor_id, value_float))
        
        for motor_id, value in input_list:
            self.motor_manager.move_motor(motor_id, value)
    
    def on_reset_btn_clicked(self):
        """Reset durchführen"""
        reset_values = self.reset_view.get_reset_values()
        
        for motor_id, value in reset_values.items():
            self.motor_manager.send_ORG(motor_id, value)
        
        self.reset_view.clear_inputs()
    
    # --- Signals from Worker ---
    @Slot(int, str)
    def on_update_label(self, motor_id: int, text: str):
        """Update Position Labels"""
        self.motor_view.update_position_label(motor_id, text)
        self.reset_view.update_position_labels(motor_id, text)
    
    def stop_motor(self, motor_id: int):
        if self.motor_manager:
            self.motor_manager.stop_motors()
    
    @Slot(str)
    def show_popup(self, message):
        self.logger.debug(f"show_popup CALLED with message: {message}")
        self.logger.debug(f"show_popup thread: {QThread.currentThread()}")
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        QMessageBox.information(self.view, "Info", message)
     
    
    # --- Helpers ---
    def show_toast(self, message: str):
        toast = Toast(message, self.view)
        toast.adjustSize()
        
        margin = 20
        parent_rect = self.view.rect()
        toast_size = toast.size()
        
        x = parent_rect.width() - toast_size.width() - margin
        y = parent_rect.height() - toast_size.height() - margin
        
        from PySide6.QtCore import QPoint
        global_pos = self.view.mapToGlobal(QPoint(x, y))
        toast.show_at(global_pos)
    
    def cleanup(self):
        """Cleanup beim Schließen"""
        if self.motor_manager:
            self.motor_manager.disable_motors()
        
        if self.worker:
            self.worker.stop()
            self.worker_thread.quit()
            self.worker_thread.wait()