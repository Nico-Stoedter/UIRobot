from PySide6.QtCore import QObject, Signal, QTimer, Slot

from src.motor import Motor
from src.motor_position_poller import MotorPositionPoller
from src.motor_motion_profiles.x_y_motor_workspace import XYMotorWorkspace 
from src.motor_motion_profiles.teleskoparm import TeleskopArm
from src.motor_motion_profiles.rot_tran_motor import RotTranMotor

class MotorManager(QObject):
    motor_discovered = Signal(int, object)      # Signal(motor_id: int, Motor: object)
    motor_state = Signal(int, dict)             # Signal for motor status update: Signal(motor_id: int, motor_status: dict[str, int])
    motor_position = Signal(int, int)           # Signal for motor position update: Signal(motor_id: int, rEncoder: int) 
    scan_completed = Signal() 
    motor_ena = Signal(int)                     # Signal(motor_id: int)
    motor_off = Signal(int)                     # Signal(motor_id: int)
    motor_starts_moving = Signal(int)           # Signal(motor_id: int)
    motor_finished_moving  = Signal(tuple)      # Signal(tuple[motor_id: int, command: str])
    #security_position_reached = Signal(list)   # Signal(list[pop_up_msg: str])
    pop_up_request = Signal(list)               # Signal(list[pop_up_error: str])
    hardware_info = Signal(int, str)            # Signal(motor_id: int, hardware_info: str)

    def __init__(self, serial_manager, config_manager=None):
        super().__init__()
        self.serial_manager = serial_manager
        self.config_manager = config_manager
        self.serial_manager.data_received.connect(self.handle_serial_data)
        self.motors = {}  # Stores all discovered motors
        self.address_list = []
        self.is_scanning = False

        # --- Motor Motion Profiles ---
        self.r1_motor_id = 70
        self.r3_motor_id = 71
        self.special_motor = TeleskopArm(self.r1_motor_id, self.r3_motor_id, parent=self)

        self.rot_motor_id = 72
        self.trn_motor_id = 73
        self.rot_tran_motor = None # Not implemented

        self.x_motor_id = 74
        self.y_motor_id = 75
        self.x_y_motor_workspace = XYMotorWorkspace(self.x_motor_id, self.y_motor_id, parent=self)

    def handle_serial_data(self, data):
        """Handle raw serial data emitted by the serial manager."""
        if not data:
            return
        try:
            self.get_message(data)
        except Exception as error:
            print(f"Failed to parse serial data {data!r}: {error}")

    def get_message(self, data):
        """Extract header, controller ID, message ID, and data from the response."""
        header = hex(data[0])[2:].upper()
        controller_id = data[1]
        message_id = hex(data[2])[2:].upper()
        terminator = hex(data[-1])[2:].upper()
        data_bytes = data[3:-1]
        #print(f"Received message: Header={header}, ID={controller_id}, Message={message_id}, Data={data_bytes}, Terminator={terminator}")
        self.process_message(header, controller_id, message_id, data_bytes, terminator)

    @Slot()
    def scan_motors(self):
        """Start scanning motors via Broadcast Address"""
        if self.is_scanning:
            return  # Prevent multiple scans

        self.is_scanning = True
        # Send single scan message to broadcast address 127
        message = "ADR=127;FBK;"
        self.serial_manager.send_message(message)
        QTimer.singleShot(1000, self.on_scan_completed)

    def on_scan_completed(self):
        # Reset scanning flag (motors will be discovered in process_message)
        self.is_scanning = False
        self.scan_completed.emit()  # Or handle completion differently

    def get_motor_position(self, motor_id):
        """Request the current motor position from hardware."""
        if motor_id in self.motors:
            motor = self.motors.get(motor_id)
            
            if motor.encoder == "1":
                msg = f"ADR={motor_id};QEC;"
            else:
                msg = f"ADR={motor_id};POS;"

            self.serial_manager.send_message(msg)

    def move_motor_joy(self, motor_id, joy_spd, encoder, position=None) -> None:
        """Manages Joystick Movement"""

        if position == None:
            msg = f"ADR={motor_id};SPD{joy_spd};"
        else:
            if encoder:     
                msg = f"ADR={motor_id};SPD{joy_spd};QEC{position};"
            else:
                msg = f"ADR={motor_id};SPD{joy_spd};POS{position};"
        
        self.serial_manager.send_message(msg)
    
    def move_motor(self, target_dict: dict[int, int]) -> None:
        """
        Executes the correct movement function based on the motor_id in input_dict[motor_id:int, target_stp:int]
        """
        for motor_id, target_stp in target_dict.items():
            if motor_id in [self.r1_motor_id, self.r3_motor_id]:        #70,71
                pass
            elif motor_id in [self.rot_motor_id, self.trn_motor_id]:    #72,73
                pass
            elif motor_id in [self.x_motor_id, self.y_motor_id]:        #74,75
                x_target_stp = target_dict.get(74)
                y_target_stp = target_dict.get(75)
                self.x_y_motor_workspace.move_motor(x_target_stp, y_target_stp)
            else:
                self.move(motor_id, target_stp)


    def move(self, motor_id, position):
        motor = self.motors.get(motor_id)

        if motor.encoder == "1":
            msg = f"ADR={motor_id};SPD{motor.spd_pps};QEC{position};"
        else:
            msg = f"ADR={motor_id};SPD{motor.spd_pps};POS{position};"

        self.serial_manager.send_message(msg)

    def reset_position(self, motor_id, stp):
        msg = f"ADR={motor_id};ORG{stp};"
        self.serial_manager.send_message(msg)


    def enable_all(self):
        """Enable all motors"""
        for idx in self.address_list:
            if idx in self.motors:
                msg = f"ADR={idx};ENA;"
                self.serial_manager.send_message(msg)

    def disable_all(self):
        """Disable all motors"""
        for idx in self.address_list:
            if idx in self.motors:
                msg = f"ADR={idx};OFF;"
                self.serial_manager.send_message(msg)

    def stop_all(self):
        """Stop all motors."""
        for idx in self.address_list:
            if idx in self.motors:
                msg = f"ADR={idx};STP0;"
                self.serial_manager.send_message(msg)

    # Helper methods for data processing
    def get_32bit(self, data_bytes):
        """Convert 5 bytes to 32-bit signed integer."""
        data_value = 0
        data_value |= (data_bytes[0] & 0x000F) << 28  # D31-D28
        data_value |= (data_bytes[1] & 0x7F) << 21   # D27-D21
        data_value |= (data_bytes[2] & 0x7F) << 14   # D20-D14
        data_value |= (data_bytes[3] & 0x7F) << 7   # D13-D7
        data_value |= data_bytes[4]                # D6-D0
        if data_value & 0x80000000:
            data_value = -((data_value ^ 0xFFFFFFFF) + 1)
        return data_value

    def get_16bit(self, data_bytes):
        """Convert 3 bytes to 16-bit signed integer."""
        while len(data_bytes) < 3:
            data_list = list(data_bytes)
            data_list.insert(0, 0)
            data_bytes = bytes(data_list)
        data_value = 0
        data_value |= (data_bytes[0] & 0x03) << 14  # D15-D14
        data_value |= (data_bytes[1] & 0x7F) << 7   # D13-D7
        data_value |= data_bytes[2]                # D6-D0
        if data_value & 0x8000:
            data_value = -((data_value ^ 0xFFFF) + 1)
        return data_value

    def get_current(self, byte):
        """Convert current byte to float."""
        return byte / 10

    def analyze_message_id(self, message_id):
        """Analyze message ID bits."""
        acr_bit = (message_id & 0x40) >> 6
        ena_bit = (message_id & 0x20) >> 5
        dir_bit = (message_id & 0x10) >> 4
        mcs_bits = message_id & 0x0F
        steps_lookup = {0: 1, 1: 2, 3: 4, 7: 8, 15: 16}
        mcs_steps = steps_lookup.get(mcs_bits, None)
        return acr_bit, ena_bit, dir_bit, mcs_steps

    def analyze_ICFG(self, value):
        """Analyze initial configuration register."""
        Elock_MASK = 0b0000000000001000
        CCW_MASK = 0b0000000000000010
        ENA_MASK = 0b0000000000000001

        P4IE = bool(value & Elock_MASK)
        S2IE = bool(value & CCW_MASK)
        S1IE = bool(value & ENA_MASK)

        return {
            "Elock": P4IE,
            "CCW": S2IE,
            "autoENA": S1IE
        }
    
    def process_message(self, header, controller_id, message_id, data_bytes, terminator):
        # Register motors on any valid response, not only during the scan window.
        if header in {"AA", "CC"}:
            should_track_motor = self.is_scanning
            if should_track_motor and controller_id not in self.motors and controller_id != 127:
                self.motors[controller_id] = Motor(controller_id, self.serial_manager, self.config_manager)
                self.address_list.append(controller_id)
                self.address_list.sort()
                self.motor_discovered.emit(controller_id, self.motors[controller_id])
                print(f"Motor {controller_id} registered from serial response")

        if controller_id in self.motors:
            motor = self.motors[controller_id]
            status_update = {}

            if header == "AA":  # Feedback header "AA"
                if message_id == "B0" and len(data_bytes) == 3: # MCFη; MCF; master configuration register
                    mcf = self.get_16bit(data_bytes)
                    bin16 = format(mcf & 0xFFFF, "016b")
                    print(bin16[2], bin16[4], bin16[5])
                    self.hardware_info.emit(controller_id, bin16)
                elif message_id == "B1" and len(data_bytes) == 6:  # MAC; MAC; set acceleration rate
                    status_update = {"AM": data_bytes[0], "accRate": self.get_32bit(data_bytes[1:])}
                elif message_id == "B2" and len(data_bytes) == 6:  # MDE; MDE; set deceleration rate
                    status_update = {"DM": data_bytes[0], "decRate": self.get_32bit(data_bytes[1:])}
                elif message_id == "B3" and len(data_bytes) == 3:  # MMS; MMS; Set maximum starting speed
                    mms = self.get_16bit(data_bytes)
                    status_update = {"maxStartSpeed": mms if mms >= 0 else (1 << 16) + mms}
                elif message_id == "B4" and len(data_bytes) == 3:  # MMD; MMD; Set maximum cessation speed
                    mmd = self.get_16bit(data_bytes)
                    status_update = {"maxStopSpeed": mmd if mmd >= 0 else (1 << 16) + mmd}
                elif message_id == "B5" and len(data_bytes) == 3:  # SPD; set desired speed
                    spd = self.get_16bit(data_bytes)
                    self.motor_finished_moving.emit((controller_id, "spd"))
                    status_update = {"sSpd": spd}
                elif message_id == "B6" and len(data_bytes) == 5:  # STP; Set desired incremental displacement
                    status_update = {"sDisplacement": self.get_32bit(data_bytes)}
                elif message_id == "B7" and len(data_bytes) == 5:  # POS; Set desired encoder position
                    status_update = {"sEncoder": self.get_32bit(data_bytes)}
                    self.motor_starts_moving.emit(controller_id)
                elif message_id == "B8" and len(data_bytes) == 5:  # QEC; Set desired quadrature encoder's position
                    status_update = {"sEncoder": self.get_32bit(data_bytes)}
                    self.motor_starts_moving.emit(controller_id)
                elif message_id == "BA" and len(data_bytes) == 1:  # ACR; ACR; Check auto-current reduction ratio
                    status_update = {"holdingCurrent": data_bytes[0]}
                elif message_id == "C2" and len(data_bytes) == 3:  # QER; QER; Set desired quadrature encoder's position
                    status_update = {"encoderRes": self.get_16bit(data_bytes)}
                elif message_id == "C9" and len(data_bytes) == 9:  # STG; STG; Set digital input sampling mode
                    status_update = {"sTimeS1": self.get_16bit(data_bytes[0:3]), "sTimeS2": self.get_16bit(data_bytes[3:6]), "sTimeS3": self.get_16bit(data_bytes[6:])}
                elif message_id == "DA" and len(data_bytes) == 3:  # ICF; ICF; Set initial configuration register
                    status_update = self.analyze_ICFG(self.get_16bit(data_bytes))
                elif message_id == "DE" and len(data_bytes) == 3:  # BLC; BLC; Set backlash compensation value
                    backlash = self.get_16bit(data_bytes)
                    status_update = {"backlash": backlash if backlash >= 0 else (1 << 16) + backlash}
                elif message_id == "D0" and len(data_bytes) == 0: # ADR=number;
                    pass
                else:  # CURn; MCSn; ENA; OFF;
                    acr, ena, direction, mcs = self.analyze_message_id(int(message_id, 16))
                    status_update = {"acr": acr, "ena": ena, "direction": direction, "mcs": mcs}

                    print("Cool", ena, controller_id)

                    if ena == 1:
                        self.motor_ena.emit(controller_id)
                    if ena == 0:
                        self.motor_off.emit(controller_id)

                    if len(data_bytes) == 9:  # All messages should return 9 data bytes
                        status_update.update({
                            "rCur": self.get_current(data_bytes[0]),
                            "rSpd": self.get_16bit(data_bytes[1:4]),
                            "rDisplacement": self.get_32bit(data_bytes[4:])
                        })

            elif header == "CC":  # Feedback header "CC"
                if message_id == "B0" and len(data_bytes) == 5: # POS; Check current position
                    rEncoder = self.get_32bit(data_bytes)
                    self.motor_position.emit(controller_id, rEncoder)
                if message_id == "B1" and len(data_bytes) == 5: # QEC; Check current quadrature encoder's position
                    rEncoder = self.get_32bit(data_bytes)
                    self.motor_position.emit(controller_id, rEncoder)
                    status_update = {"rEncoder": rEncoder}
                elif message_id == "B2" and len(data_bytes) == 3:  # SPD; Check current speed
                    status_update = {"rSpd": self.get_16bit(data_bytes)}
                elif message_id == "B3" and len(data_bytes) == 5:  # STP; Check current incremental displacement
                    status_update = {"rDisplacement": self.get_32bit(data_bytes)}
                elif message_id == "C1" and len(data_bytes) == 5:  # SFB; Check sensor status
                    status_update = {"S1": data_bytes[0], "S2": data_bytes[1], "S3": data_bytes[2], "AnalogIn": self.get_16bit(data_bytes[3:])}
                elif message_id == "A8" and len(data_bytes) == 6:  # Unknown message
                    status_update = {"rEncoder": self.get_32bit(data_bytes[1:])}
                    self.motor_finished_moving.emit((controller_id, "qec"))
                else:  # Other messages
                    acr, ena, direction, mcs = self.analyze_message_id(int(message_id, 16))
                    status_update = {"acr": acr, "ena": ena, "direction": direction, "mcs": mcs}
                    if len(data_bytes) == 9:
                        status_update.update({
                            "rCur": self.get_current(data_bytes[0]),
                            "rSpd": self.get_16bit(data_bytes[1:4]),
                            "rDisplacement": self.get_32bit(data_bytes[4:])
                        })

            if status_update:
                motor.handle_status_update(status_update)
                self.motor_state.emit(controller_id, motor.status)

    # --- Signal Slots for Motor Motion Profiles ---

    @Slot(list)
    def x_y_out_of_range(self, error_list) -> None:
        self.pop_up_request.emit(error_list)