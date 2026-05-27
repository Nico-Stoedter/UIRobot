from PySide6.QtCore import QObject, QTimer, Slot, Signal

import pygame

class JoystickManager(QObject):

    create_pop_up = Signal(list)            # Signal(list[message: str])
    send_joystick_movement = Signal(object) # Signal(dict[motor_id: int, joy_deflection: float]) dict is object because of Conversion error otherwise
    layout_changed = Signal(bool)           # Changes the coloring of the device names on the motor page ui

    def __init__(self, parent=None):
        super().__init__(parent)
        pygame.init()

        self.joystick = None
        self.joystick_instance_id = None

        self.pop_up = False
        self.layout = False # If False Config Axis 1-5 are Used. 6-10 Otherwise
        self.spd_factor = 1 # Is 2 if RB Button pressed 1 otherwise 
        self.axis_motor_dict = {}
        self.last_axis_values: dict[int, int] = {}    # Need to Remember last spd to Enable Correct RB Button spd during Joystick use
        self.moving_motor: dict[int, bool] = {}

        # IDs for the XYMotorWorkspace
        self.x_motor_id = 74    
        self.y_motor_id = 75

        self._connect_first_available_joystick()

        self._timer = QTimer(self)
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    def _connect_first_available_joystick(self):
        if pygame.joystick.get_count() > 0:
            self._set_joystick(pygame.joystick.Joystick(0))

    def _set_joystick(self, joystick):
        joystick.init()
        self.joystick = joystick
        self.joystick_instance_id = joystick.get_instance_id()
        print(f"Connected: {joystick.get_name()}")

    def _poll(self):
        try:
            for event in pygame.event.get():
                if self.pop_up: # No Movement if PopUp exists
                    return
                elif self.axis_motor_dict == {}:
                    return
                elif event.type == pygame.JOYDEVICEADDED:
                    self._handle_device_added(event)
                elif event.type == pygame.JOYDEVICEREMOVED:
                    self._handle_device_removed(event)
                elif event.type == pygame.JOYBUTTONDOWN:
                    self.on_button_down(event.button, event)
                elif event.type == pygame.JOYBUTTONUP:
                    self.on_button_up(event.button, event)
                elif event.type == pygame.JOYAXISMOTION:
                    self.on_axis_moved(event.axis, event)

                pygame.event.clear()

        except Exception as e:
            print(f"Joystick polling failed: {e}")

    def _handle_device_added(self, event):
        if self.joystick is None:
            self._set_joystick(pygame.joystick.Joystick(event.device_index))

    def _handle_device_removed(self, event):
        if self.joystick is not None and event.instance_id == self.joystick_instance_id:
            self.joystick.quit()
            self.joystick = None
            self.joystick_instance_id = None
            print("[JoystickManager] Disconnected")
        
    def on_button_down(self, button, event):
        #print("=== JOYBUTTONDOWN ===")
        #print("button:", event.button)     # Welcher Button gedrückt
        if event.button == 3:
            test = ["Test"]
            self.create_pop_up.emit(test)
        if event.button == 4:
            print("Cool")
            self._lb_button_down()
        if event.button == 5:
            self._rb_button_down()

    def _lb_button_down(self):
        print(f"[JoystickManager]")
        self.layout = not(self.layout)

        self.layout_changed.emit(self.layout)

    def _rb_button_down(self):
        print(f'[JoystickManager] double speed ON')
        self.spd_factor = 2

        for motor_id, value in self.last_axis_values.items():
            if self.moving_motor.get(motor_id):
                new_spd_pps = float(value * 2)
                self.last_axis_values[motor_id] = new_spd_pps
                self.send_joystick_movement.emit((motor_id, new_spd_pps))

    def on_button_up(self, button, event):
        if event.button == 5:
            self.rb_button_up()

    def rb_button_up(self):
        print("[JoystickManager] double speed OFF")
        self.double_speed = 1

        for motor_id, value in self.last_axis_values.items():
            if self.moving_motor.get(motor_id):
                new_spd_pps = float(value / 2)
                self.last_axis_values[motor_id] = new_spd_pps
                self.send_joystick_movement.emit((motor_id, new_spd_pps))
    
    def on_axis_moved(self, axis, event):
        input_dict = {}
        parsed_axis = int(self.parse_axis(event.axis))
        motor_id = self.axis_motor_dict.get(parsed_axis)
        value = event.value

        # Technically LT, RT are both axis on its own with [-1.0, 1.0]. Convert them to LT [-1.0, 0]; RT [0.0, 1.0]
        if axis == 5:   
            value = ((event.value + 1) / 2) * self.spd_factor
        if axis == 4:
            value = (((event.value + 1) / 2) * -1) * self.spd_factor

        self.last_axis_values[motor_id] = value

        if motor_id == self.x_motor_id:
            x_value = self.joystick.get_axis(0)
            y_value = -self.joystick.get_axis(1)
            input_dict[motor_id] = x_value
            input_dict[motor_id + 1] = y_value
        elif motor_id == self.y_motor_id:
            x_value = self.joystick.get_axis(0)
            y_value = -self.joystick.get_axis(1)
            input_dict[motor_id - 1] = x_value
            input_dict[motor_id] = y_value
        else:
            input_dict[motor_id] = value

        self.send_joystick_movement.emit(input_dict)

    def parse_axis(self, input: int) -> str:
        '''Parses Pygame axis number to omnivac axis'''
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

        if self.layout:
            return parser_2.get(input)
        else:    
            return parser.get(input)   

    @Slot(object)
    def receive_axis_motor_pairs(self, axis_motor_pairs) -> None:
        self.axis_motor_dict = axis_motor_pairs
        self.moving_motor = {key: False for key in axis_motor_pairs.values()}
        self.last_spd_send = {key: 0 for key in axis_motor_pairs.values()}

    @Slot()
    def pop_up_created(self) -> None:
        self.pop_up = True

    @Slot()
    def pop_up_closed(self) -> None:
        self.pop_up = False