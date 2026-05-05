from PySide6.QtCore import QObject

class XYMotorWorkspace(QObject):
    
    def __init__(self):
        super().__init__(parent=None)
        self.x_motor_id = 74
        self.y_motor_id = 75

    def move_motor(self):
        print("ToDO")
