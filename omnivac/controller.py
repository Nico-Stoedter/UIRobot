import pygame

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor
    from motor_manager import MotorManager

pygame.init()
pygame.joystick.init()

class ControllerManager:

    def __init__(self, motor_manager: "MotorManager", ini_manager, label_name_list, pop_up, **kwargs):      
        self.setting = False            # If false controller has axis 1-5 and 6-10 otherwise
        self.double_speed = False

        self.pop_up = pop_up
        self.ini_manager = ini_manager
        self.motor_manager = motor_manager
        self.label_name_list = label_name_list
        self.joystick = None
        self.motors: dict[int, "Motor"] = self.motor_manager.motors
        self.moving_motor: dict[int, bool] = {key: False for key in self.motors}
        self.last_spd_send: dict[int, int] = {key: 0 for key in self.motors}
        self.last_axis = {}
        self.last_motor_speeds = None

        self.switch_label_color()

    def controller(self) -> None:
        '''Manages Joystick Inputs and Calls Joystick Funktions by itself'''
        for event in pygame.event.get(): # All Joystick inputs are in pygame.event

            #print(event)

            axis_x = 0
            axis_y = 0

            # No Joystick inputs if pop_up is visible
            if self.pop_up and self.pop_up.is_visible():
                continue

            # --- Add/Disconnect Joystick
            if event.type == pygame.JOYDEVICEREMOVED:
                print('DISCONECTED')

            elif event.type == pygame.JOYDEVICEADDED:
                self.event_controller_connected(event)

            # --- Button Managment ---
            elif event.type == pygame.JOYBUTTONDOWN:    # Events if button pressed
                if event.button == 4:
                    self.event_button_lb()

                elif event.button == 5:
                    self.event_button_rb_down()

            elif event.type == pygame.JOYBUTTONUP:  # Events if button released
                if event.button == 5:
                    self.event_button_rb_up()

            # --- Joystick Managment ---
            elif event.type == pygame.JOYAXISMOTION:    # Joystick Motion

                # --- Axis Filter ---
                last = self.last_axis.get(event.axis, 0.0)
                if abs(event.value - last) < 0.05:
                    continue 
                self.last_axis[event.axis] = event.value

                parsed_event_code = self.gamepad_parser(event.axis)
                motor_id = self.find_motor_with_axis(parsed_event_code)

                if motor_id is None:
                    continue

                motor_speeds = self.joystick_motion(event.axis, motor_id)                      

                if motor_id in[74,75]: # Hier späte gucken ob einfacher geht
                    axis_x = round(self.joystick.get_axis(0), 2)
                    axis_y = round(self.joystick.get_axis(1) * -1, 2)
  
                # --- Nur senden, wenn sich etwas geändert hat ---
                if motor_speeds != self.last_motor_speeds:
                    self.motor_manager.controller_movement(axis_x, axis_y, motor_speeds)
                    self.last_motor_speeds = motor_speeds

    # --- Button Events ---

    def event_controller_connected(self, event):
        '''Manages adding joystick'''
        motor_index = event.device_index
        self.joystick = pygame.joystick.Joystick(motor_index)
        self.joystick.init()

    def event_button_lb(self):
        '''Manages action for lb button'''
        print(f'[ControllerManager] switched axis layout')
        self.setting = not(self.setting)
        self.switch_label_color()
    
    def event_button_rb_down(self):
        '''Manages action for lb button'''
        print(f'[ControllerManager] double speed ON')
        self.double_speed = True

        for motor_id, value in self.last_spd_send.items():
            if self.moving_motor.get(motor_id):
                axis_x = 0 # Contorller movement braucht diese beiden Werte # Todo controller_movemnt von diesen beiden unabhängig machen wenn möglich
                axis_y = 0
                new_spd = int(value * 2)
                double_speed = {motor_id: new_spd}
                self.motor_manager.controller_movement(axis_x, axis_y, double_speed)
                self.last_spd_send[motor_id] = new_spd

    def event_button_rb_up(self):
        '''Manages action for lb button'''
        print(f'[ControllerManager] double speed OFF')
        self.double_speed = False

        for motor_id, value in self.last_spd_send.items():
            if self.moving_motor.get(motor_id):
                axis_x = 0 # Contorller movement braucht diese beiden Werte # Todo controller_movemnt von diesen beiden unabhängig machen
                axis_y = 0
                new_spd = int(value/2)
                double_speed = {motor_id: new_spd}
                self.motor_manager.controller_movement(axis_x, axis_y, double_speed)
                self.last_spd_send[motor_id] = new_spd

    def joystick_motion(self, joy_axis: int, motor_id: int) -> dict[int, int]:
        '''Manages value from joystick and RT,LT and returns a dict with the motor_id 
            of corresponding joystick action and a spd value based on deflection'''
        spd_rpm: float = float(self.ini_manager.get_value(motor_id, "Soft_Basic", "Max_Speed(rpm)"))
        spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))

        # Calculates speeds for fluid normal x/y movment
        x_motor_n = self.motors.get(5)
        y_motor_n = self.motors.get(6)
        x_rpm_n = x_motor_n.max_speed
        y_rpm_n = y_motor_n.max_speed
        x_spd_n = max(-32768, min(int(x_rpm_n / 60 * 2000), 32767))
        y_spd_n = max(-32768, min(int(y_rpm_n / 60 * 2000), 32767))

        spd_x = spd_y = spd_z = 0

        x_id = y_id = z_id = None

        motor_speeds = {}

        # --- Axis Management ---
        axes = { # Get value from all axis
            0: round(self.joystick.get_axis(0), 2),
            1: round(self.joystick.get_axis(1) * -1, 2),
            2: round(self.joystick.get_axis(2), 2),
            3: round(self.joystick.get_axis(3) * -1, 2),
            4: round(self.joystick.get_axis(4), 2),
            5: round(self.joystick.get_axis(5), 2),
        }

        # Stick-Layout: (x_axis, y_axis)
        stick_map = {
            0: (0, 1),  # joy_axis 0 or 1 → Stick 1
            1: (0, 1),
            2: (2, 3),  # joy_axis 2 or 3 → Stick 2
            3: (2, 3),
        }

        factor = 1 if not self.double_speed else 2

        # --- Stick (X-Axis, Y-Axis) ---
        if joy_axis in stick_map:
            x_axis, y_axis = stick_map[joy_axis]

            x_value = axes[x_axis]
            y_value = axes[y_axis]

            parsed_x_axis = self.gamepad_parser(x_axis)
            parsed_y_axis = self.gamepad_parser(y_axis)
            x_id = self.find_motor_with_axis(parsed_x_axis)
            y_id = self.find_motor_with_axis(parsed_y_axis)

            self.moving_motor[x_id] = x_value > 0
            self.moving_motor[y_id] = y_value > 0

            if motor_id in [5,6]:
                spd_x = factor * int((x_spd_n / 2) * x_value)
                spd_y = factor * int((y_spd_n / 2) * y_value)
            else:
                spd_x = factor * int((spd_stepps / 2) * x_value)
                spd_y = factor * int((spd_stepps / 2) * y_value)

            motor_speeds[x_id] = spd_x
            self.last_spd_send[x_id] = spd_x
            motor_speeds[y_id] = spd_y
            self.last_spd_send[y_id] = spd_y 

        # --- Trigger (Z-Axis) ---
        elif joy_axis in [4, 5]:
            z_axis = axes[4] if axes[4] > 0 else axes[5]
            parsed_z_axis = self.gamepad_parser(joy_axis)
            z_id = self.find_motor_with_axis(parsed_z_axis)
            self.moving_motor[motor_id] = z_axis > 0
            spd_z = factor * self.event_joy_correction_rt_lt(z_axis, spd_stepps)

            # Left Trigger = negative value
            if joy_axis == 4:
                spd_z *= -1

            motor_speeds[z_id] = spd_z
            self.last_spd_send[z_id] = spd_z

        return motor_speeds

    # --- Miscellaneous ---
    def event_joy_correction_rt_lt(self, event_axis, spd_stepps):
        # Trigger: RT = Axis 5, LT = Axis 4 
        # Special because weird values. Sticks have -1.0 to 1.0 but for RT/LT have each -1.0 to 1.0
        trigger_value = (event_axis + 1) / 2 if event_axis != 0 else 0

        if trigger_value > 0.1:
            gradual_spd = int((spd_stepps / 2) * trigger_value)
        else:
            gradual_spd = 0

        return gradual_spd
    
    def find_motor_with_axis(self, axis) -> int:
        for id, motor in self.motors.items():
            if motor.joystick_axis == int(axis):
                return id
            
    def switch_label_color(self) -> None:
        """Switches the labels on the front end"""

        for motor_id, label in self.label_name_list.items():
            motor = self.motors.get(motor_id)
            if not motor:
                continue  

            joystick_axis = motor.joystick_axis
            is_valid_axis = joystick_axis != 0 and joystick_axis <= 5

            # Colouring
            if self.setting:
                color = "white" if is_valid_axis else "yellow"
            else:
                color = "yellow" if is_valid_axis else "white"

            text = ControllerManager.clear_text(label.text())
            label.setText(f"<font color='{color}'>{text}</font>")

    def add_joy(self):
        '''Adds Joystick'''
        joystick = pygame.joystick.Joystick(2)
        joystick.init()
        print(f"Controller erkannt: {joystick.get_name()}")

    def gamepad_parser(self, input: int) -> str:
        ''' Parses Gamepad axis to .ini axis'''
        parser = {
            0 : '1',
            1 : '2',
            2 : '3',
            3 : '4',
            4 : '5',
            5 : '5',
        }

        parser_2 = {
            0 : '6',
            1 : '7',
            2 : '8',
            3 : '9',
            4 : '10',
            5 : '10',
        }

        if self.setting:
            return parser_2.get(input)
        else:    
            return parser.get(input)

    @staticmethod
    def clear_text(text) -> str:
        return text.replace("<font color='white'>", "").replace("<font color='yellow'>", "").replace("</font>", "")
