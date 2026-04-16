from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QSizePolicy, QSpacerItem, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator

if TYPE_CHECKING:
    from omnivac.core.motor import Motor
    from omnivac.config.ini_manager import IniManager

class MotorWidgetFactory:
    """Factory für Motor-UI-Widgets"""
    
    def __init__(self, ini_manager: "IniManager", validator: QRegularExpressionValidator):
        self.ini_manager = ini_manager
        self.validator = validator
    
    def create_motor_page_layout(
        self, 
        parent_widget: QWidget,
        motors: dict[int, "Motor"],
        label_dict: dict,
        input_position: dict,
        label_name_dict: dict,
        on_confirm_callback
    ) -> QVBoxLayout:
        """Erstellt das komplette Layout für die Motor-Page"""
        
        layout = QVBoxLayout(parent_widget)
        
        # 1. Header
        headers = ["Name", "Target Pos", "Current Pos", "Preset"]
        header_layout = self._create_header_row(parent_widget, headers)
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # 2. Motor Rows
        for row, (motor_id, motor) in enumerate(motors.items()):
            motor_layout = self._create_motor_row(
                parent_widget, motor_id, motor, 
                label_dict, input_position, label_name_dict
            )
            layout.addLayout(motor_layout)
            
            if row < len(motors) - 1:
                layout.addSpacing(10)
        
        # 3. Confirm Button
        confirm_btn = self._create_confirm_button(parent_widget, on_confirm_callback)
        layout.addWidget(confirm_btn, alignment=Qt.AlignHCenter)
        
        # 4. Spacer
        v_spacer = QSpacerItem(20, 200, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout.addItem(v_spacer)
        
        return layout
    
    def create_reset_page_layout(
        self,
        parent_widget: QWidget,
        motors: dict[int, "Motor"],
        label_dict: dict,
        input_reset: dict,
        duplicate_label_dict: dict,
        on_reset_callback
    ) -> QVBoxLayout:
        """Erstellt das komplette Layout für die Reset-Page"""
        
        layout = QVBoxLayout(parent_widget)
        
        # 1. Header
        headers = ["Name", "Reset Pos", "Current Pos"]
        header_layout = self._create_header_row(parent_widget, headers)
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # 2. Motor Rows
        for row, (motor_id, motor) in enumerate(motors.items()):
            motor_layout = self._create_reset_row(
                parent_widget, motor_id, motor,
                label_dict, input_reset, duplicate_label_dict
            )
            layout.addLayout(motor_layout)
            
            if row < len(motors) - 1:
                layout.addSpacing(10)
        
        # 3. Reset Button
        reset_btn = self._create_confirm_button(parent_widget, on_reset_callback)
        reset_btn.setText("Reset")
        layout.addWidget(reset_btn, alignment=Qt.AlignHCenter)
        
        # 4. Spacer
        v_spacer = QSpacerItem(20, 200, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout.addItem(v_spacer)
        
        return layout
    
    def _create_header_row(self, parent: QWidget, headers: list[str]) -> QHBoxLayout:
        """Erstellt die Header-Zeile"""
        layout = QHBoxLayout()
        
        for i, title in enumerate(headers):
            label = QLabel(title, parent)
            label.setObjectName(f"header_label_{i}")
            label.setStyleSheet("font-weight: bold;")
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.setMaximumHeight(50)
            
            # Spaltenbreiten
            if i == 0:  # Name
                label.setMinimumWidth(75)
                label.setMaximumWidth(200)
            elif i == 1:  # Input/Reset
                label.setMinimumWidth(100)
                label.setMaximumWidth(350)
            elif i == 2:  # Position
                label.setMinimumWidth(100)
                label.setMaximumWidth(300)
            elif i == 3:  # Preset
                label.setMinimumWidth(100)
                label.setMaximumWidth(300)
            
            layout.addWidget(label)
        
        return layout
    
    def _create_motor_row(
        self,
        parent: QWidget,
        motor_id: int,
        motor: "Motor",
        label_dict: dict,
        input_position: dict,
        label_name_dict: dict
    ) -> QHBoxLayout:
        """Erstellt eine Motor-Zeile für die Motor-Page"""
        layout = QHBoxLayout()
        
        # 1. Name Label
        name_label = QLabel(parent)
        name_label.setObjectName("name_label")
        name_label.setText(self.ini_manager.get_value(motor_id, "Soft_Basic", "Device_Name"))
        name_label.setMinimumWidth(75)
        name_label.setMaximumWidth(200)
        layout.addWidget(name_label)
        label_name_dict[motor_id] = name_label
        
        # 2. Input Field
        input_field = QLineEdit(parent)
        input_field.setPlaceholderText(f"∈[{motor.min_position}, {motor.max_position}]")
        input_field.setValidator(self.validator)
        input_field.setMinimumWidth(100)
        input_field.setMaximumWidth(350)
        input_field.setMinimumHeight(50)
        layout.addWidget(input_field)
        input_position[motor_id] = input_field
        
        # 3. Position Label
        pos_label = QLabel(parent)
        pos_label.setObjectName("position_label")
        first_pos = motor.get_motor_pos()
        pos_label.setText(f"{first_pos} {motor.position_unit}")
        pos_label.setMinimumWidth(100)
        pos_label.setMaximumWidth(300)
        layout.addWidget(pos_label)
        label_dict[motor_id] = pos_label
        
        # 4. Preset ComboBox
        combo_box = QComboBox(parent)
        combo_box.setObjectName("preset_combo_box")
        presets = self.ini_manager.get_preset_positions_from_motor(motor_id)
        preset_names = ["None"] + list(presets.keys())
        combo_box.addItems(preset_names)
        combo_box.setMinimumWidth(100)
        combo_box.setMaximumWidth(300)
        combo_box.setMinimumHeight(50)
        layout.addWidget(combo_box)
        
        return layout
    
    def _create_reset_row(
        self,
        parent: QWidget,
        motor_id: int,
        motor: "Motor",
        label_dict: dict,
        input_reset: dict,
        duplicate_label_dict: dict
    ) -> QHBoxLayout:
        """Erstellt eine Motor-Zeile für die Reset-Page"""
        layout = QHBoxLayout()
        
        # 1. Name Label
        name_label = QLabel(parent)
        name_label.setText(self.ini_manager.get_value(motor_id, "Soft_Basic", "Device_Name"))
        name_label.setMaximumHeight(50)
        name_label.setMinimumWidth(75)
        name_label.setMaximumWidth(200)
        layout.addWidget(name_label)
        
        # 2. Input Field
        input_field = QLineEdit(parent)
        input_field.setPlaceholderText("Number")
        input_field.setValidator(self.validator)
        input_field.setMaximumHeight(50)
        input_field.setMinimumWidth(100)
        input_field.setMaximumWidth(350)
        layout.addWidget(input_field)
        input_reset[motor_id] = input_field
        
        # 3. Duplicate Position Label
        original_label = label_dict.get(motor_id)
        text = original_label.text() if original_label else f"{motor.get_motor_pos()} {motor.position_unit}"
        
        duplicate_label = QLabel(parent)
        duplicate_label.setObjectName("position_label_clone")
        duplicate_label.setText(text)
        duplicate_label.setMaximumHeight(50)
        duplicate_label.setMinimumWidth(100)
        duplicate_label.setMaximumWidth(300)
        layout.addWidget(duplicate_label)
        
        # Speichern für Sync
        if motor_id not in duplicate_label_dict:
            duplicate_label_dict[motor_id] = []
        duplicate_label_dict[motor_id].append(duplicate_label)
        
        return layout
    
    def _create_confirm_button(self, parent: QWidget, callback) -> QPushButton:
        """Erstellt den Confirm/Reset Button"""
        btn = QPushButton("Confirm", parent)
        btn.setObjectName("confirm_button")
        btn.setStyleSheet("margin-top: 20px; font-size: 18px;")
        btn.setMinimumWidth(200)
        btn.setMaximumWidth(400)
        btn.setMinimumHeight(50)
        btn.setMaximumHeight(80)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.clicked.connect(callback)
        return btn