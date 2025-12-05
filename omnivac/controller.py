import pygame

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor
    from motor_manager import MotorManager

pygame.init()
pygame.joystick.init()

class ControllerManager:

    def __init__(self, motor_manager: "MotorManager", ini_manager, label_list, pop_up, **kwargs):
        self.double_speed = False      
        self.setting = False            # If false controller has axis 1-5 and 6-10 otherwise

        self.pop_up = pop_up
        self.ini_manager = ini_manager
        self.motor_manager = motor_manager
        self.label_list = label_list
        self.joystick = None

        self.motors: dict[int, "Motor"] = self.motor_manager.motors

    def add_joy(self):
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
    
    def double_speed(self, event_state) -> None:
        if event_state == 1:
            self._double_speed = True
            print('[ControllerManager] Double Speed Enabled')
        else:
            self._double_speed = False
            print('[ControllerManager] Double Speed Disabled')

    def controller(self) -> None:
        for event in pygame.event.get():

            axis_x = 0
            axis_y = 0
            gradual_spd_x = 0
            gradual_spd_y = 0
            gradual_spd  = 0

            if self.pop_up and self.pop_up.is_visible():
                continue

            if event.type == pygame.JOYDEVICEREMOVED:
                print('DISCONECTED')

            elif event.type == pygame.JOYDEVICEADDED:
                self.event_controller_connected(event)

            elif event.type == pygame.JOYBUTTONDOWN:    # Events if button pressed
                if event.button == 4:
                    self.event_button_lb()

                elif event.button == 5:
                    self.event_button_rb_down()

            elif event.type == pygame.JOYBUTTONUP:  # Events if button released
                if event.button == 5:
                    self.event_button_rb_up

            elif event.type == pygame.JOYAXISMOTION:    # Joystick Motion
                parsed_event_code = self.gamepad_parser(event.axis)
                motor_id = self.find_motor_with_axis(parsed_event_code)

                if motor_id == None:
                    print("Upsi nix motor Id gefunden") # Debug
                    break

                spd_rpm: float = float(self.ini_manager.get_value(motor_id, "Soft_Basic", "Max_Speed(rpm)"))
                spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
                gradual_spd = int((spd_stepps / 2) * event.value)

                if event.axis in [1,3,4,5]:
                    gradual_spd = self.event_joy_correction(event, gradual_spd)
                        
                if self.double_speed:
                    gradual_spd = gradual_spd * 2

                if motor_id in[74,75]: # Hier späte gucken ob einfacher geht
                    axis_x = round(self.joystick.get_axis(0), 2)
                    axis_y = round(self.joystick.get_axis(1) * -1, 2)

                    x_device = self.motors.get(74)
                    y_device = self.motors.get(75)

                    x_spd_rpm = x_device.max_speed
                    y_spd_rpm = y_device.max_speed

                    spd_stepps_x = max(-32768, min(int(x_spd_rpm / 60 * 2000), 32767))
                    spd_stepps_y = max(-32768, min(int(y_spd_rpm / 60 * 2000), 32767))

                    gradual_spd_x = int(abs(axis_x) * (spd_stepps_x / 2))
                    gradual_spd_y = int(abs(axis_y) * (spd_stepps_y / 2))
                        
                self.motor_manager.controller_movement(axis_x, axis_y, gradual_spd_x, 
                                                       gradual_spd_y, motor_id, gradual_spd)

    def find_motor_with_axis(self, axis) -> int:
        for id, motor in self.motors.items():
            if motor.joystick_axis == int(axis):
                return id
            
    def switch_label_color(self) -> None:
        for label in self.label_list:
            if self.setting:
                if label in self.label_list[5:]:
                    text = label.text()
                    text = ControllerManager.clear_text(text)
                    label.setText(f"<font color='yellow'>{text}</font>")
                else:
                    text = label.text()
                    text = ControllerManager.clear_text(text)
                    label.setText(f"<font color='white'>{text}</font>")
            else:
                if label in self.label_list[:5]:
                    text = label.text()
                    text = ControllerManager.clear_text(text)
                    label.setText(f"<font color='yellow'>{text}</font>")
                else:
                    text = label.text()
                    text = ControllerManager.clear_text(text)
                    label.setText(f"<font color='white'>{text}</font>")

    def event_controller_connected(self, event):
        print('ADDED')
        device_index = event.device_index
        self.joystick = pygame.joystick.Joystick(device_index)
        self.joystick.init()

    def event_button_lb(self):
        print(f'[ControllerManager] switched axis layout')
        self.setting = not(self.setting)
        self.switch_label_color()
    
    def event_button_rb_down(self):
        print(f'[ControllerManager] double speed ON')
        self.double_speed = True

    def event_button_rb_up(self):
        print(f'[ControllerManager] double speed OFF')
        self.double_speed = False

    def event_joy_correction(self, event, spd_stepps):
        # Trigger: RT = Axis 5, LT = Axis 4 (special because weird values)
        if event.axis == 5:  # RT
            trigger_value = (event.value + 1) / 2

            if trigger_value > 0.1:
                gradual_spd = int((spd_stepps / 2) * trigger_value)
            else:
                gradual_spd = 0

        elif event.axis == 4:  # LT
            trigger_value = (event.value + 1) / 2

            if trigger_value > 0.1:
                gradual_spd = int(-(spd_stepps / 2) * trigger_value)
            else:
                gradual_spd = 0
        elif event.axis == 1 or event.axis == 3:
            # invert axis 1 and 3
            gradual_spd = int(event.value * (spd_stepps / -2))

        return gradual_spd

    @staticmethod
    def clear_text(text) -> str:
        return text.replace("<font color='white'>", "").replace("<font color='yellow'>", "").replace("</font>", "")
