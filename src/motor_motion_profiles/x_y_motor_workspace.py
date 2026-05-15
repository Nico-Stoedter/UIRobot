from PySide6.QtCore import QObject, Signal

import math

class XYMotorWorkspace(QObject):

    out_of_range = Signal(list)
    
    def __init__(self, x_id, y_id, parent=None):
        super().__init__(parent)
        self.motor_manager = parent

        self.x_motor_id = x_id  # id -> 74
        self.y_motor_id = y_id  # id -> 75

        self.out_of_range.connect(self.motor_manager.x_y_out_of_range)

    def move_motor(self, x_target_stp, y_target_stp):
        """
        Moves motor_ids 74,75 with consideration of there Workspace sqrt(x**2 + y**2)
        """
        x_motor = self.motor_manager.motors.get(self.x_motor_id)
        y_motor = self.motor_manager.motors.get(self.y_motor_id)
        x_cur_pos_stp = x_motor.status["rEncoder"]
        y_cur_pos_stp = y_motor.status["rEncoder"]
        x_y_max_pos_stp = x_motor.max_pos_stp

        x_target_stp = x_cur_pos_stp if x_target_stp is None else x_target_stp
        y_target_stp = y_cur_pos_stp if y_target_stp is None else y_target_stp

        combined_target_stp = math.sqrt(x_target_stp**2 + y_target_stp**2)
        print(x_target_stp, y_target_stp)
        print(combined_target_stp)
        print(x_y_max_pos_stp)

        if combined_target_stp > x_y_max_pos_stp + 0.01:    # With some tolerance
            error_msg = ["Motor IDs: 74,75 moved out of range"]
            self.out_of_range.emit(error_msg)
        else:
            self.motor_manager.move(self.x_motor_id, x_target_stp)
            self.motor_manager.move(self.y_motor_id, y_target_stp)
