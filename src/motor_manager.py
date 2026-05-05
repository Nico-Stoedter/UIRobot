from PySide6.QtCore import QObject, Signal, QTimer, Slot

from src.motor import Motor
from src.motor_position_poller import MotorPositionPoller

class MotorManager(QObject):
    motor_discovered = Signal(int, object)  # Signal for newly discovered motor
    motor_state = Signal(int, dict)  # Signal for motor status update
    motor_position = Signal(int, int)            # Signal for motor position update: motor_id, rEncoder 
    motor_ready = Signal(int, int)  # Signal for motor ready state
    scan_completed = Signal()  # Signal for scan completion

    def __init__(self, serial_manager, config_manager=None):
        super().__init__()
        self.serial_manager = serial_manager
        self.config_manager = config_manager
        self.serial_manager.data_received.connect(self.handle_serial_data)
        self.motors = {}  # Stores all discovered motors
        self.address_list = []
        self.is_scanning = False

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
        print(f"Received message: Header={header}, ID={controller_id}, Message={message_id}, Data={data_bytes}, Terminator={terminator}")
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

    def get_motor_status(self, controller_id):
        """Get motor status - called by GUI."""
        if controller_id in self.motors:
            status = self.motors[controller_id].get_status()
            self.motor_state.emit(controller_id, status)

    def get_motor_position(self, controller_id):
        """Request the current motor position from hardware."""
        if controller_id in self.motors:
            msg = f"ADR{controller_id};QEC;"
            self.serial_manager.send_message(msg)

    def set_motor_speed(self, controller_id, value):
        """Set motor speed."""
        if controller_id in self.motors:
            self.motors[controller_id].set_spd(value)
            self.motors[controller_id].spd(value)

    def set_motor_position_abs(self, controller_id, value):
        """Set motor absolute position."""
        if controller_id in self.motors:
            self.motors[controller_id].set_position(value)
            self.motors[controller_id].qec(value)

    def stop_motor(self, controller_id):
        """Stop a specific motor immediately."""
        if controller_id not in self.motors:
            return False

        self.motors[controller_id].stop()
        return True

    def set_motor_enabled_state(self, controller_id, enabled):
        """Explicitly enable or disable a specific motor."""
        if controller_id not in self.motors:
            return False

        motor = self.motors[controller_id]
        motor.set_enable(enabled)
        motor.ena()
        return True
    
    def move_motor(self, motor_id, position):
        motor = self.motors.get(motor_id)

        msg = f"ADR={motor_id};SPD{motor.spd};QEC{position};"
        self.serial_manager.send_message(msg)

    def move_motor_to_units(
        self,
        controller_id,
        target_units,
        speed_units_per_sec=None,
        forward_only=False,
        wrap_direction=None,
    ):
        """Move a motor to an absolute target in calibrated display units."""
        if controller_id not in self.motors:
            return False

        motor = self.motors[controller_id]
        if wrap_direction is not None:
            if wrap_direction >= 0:
                delta_units = (target_units - motor.get_position()) % 360.0
            else:
                delta_units = -((motor.get_position() - target_units) % 360.0)
        elif forward_only:
            delta_units = (target_units - motor.get_position()) % 360.0
        else:
            delta_units = target_units - motor.get_position()

        motor.prepare_for_motion(speed_units_per_sec=speed_units_per_sec)
        delta_raw = motor.get_delta_raw_from_units(delta_units)
        motor.stp(delta_raw)
        return True

    def zero_motor_position(self, controller_id):
        """Reset the displayed motor position to zero at the current physical location."""
        if controller_id not in self.motors:
            return False

        self.motors[controller_id].zero_position()
        self.motor_state.emit(controller_id, self.motors[controller_id].get_status())
        return True

    def zero_motor_encoder_hardware(self, controller_id):
        """Ask the controller to set the current encoder position to zero."""
        return self.set_motor_encoder_hardware(controller_id, 0)

    def set_motor_encoder_hardware(self, controller_id, encoder_value):
        """Ask the controller to set the current encoder position to a specific raw value."""
        if controller_id not in self.motors:
            return False

        motor = self.motors[controller_id]
        encoder_value = int(round(encoder_value))
        motor.qec(encoder_value)
        motor.status["rEncoder"] = encoder_value
        motor.status["sEncoder"] = encoder_value
        motor.status["hasPosition"] = True
        motor.status["displayPosition"] = motor.get_position()
        motor.status["displayUnit"] = motor.display_unit
        self.motor_state.emit(controller_id, motor.get_status())
        return True

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
                msg = f"ADR{idx};OFF;"
                self.serial_manager.send_message(msg)

    def stop_all(self):
        """Stop all motors."""
        for idx in self.address_list:
            if idx in self.motors:
                self.motors[idx].stp(0)

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
                self.motor_discovered.emit(controller_id, self.motors[controller_id]) # emit hat noch kein SLot
                print(f"Motor {controller_id} registered from serial response")

        if controller_id in self.motors:
            motor = self.motors[controller_id]
            status_update = {}

            if header == "AA":  # Feedback header "AA"
                if message_id == "B1" and len(data_bytes) == 6:  # MAC; MAC; set acceleration rate
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
                    status_update = {"sSpd": self.get_16bit(data_bytes)}
                elif message_id == "B6" and len(data_bytes) == 5:  # STP; Set desired incremental displacement
                    status_update = {"sDisplacement": self.get_32bit(data_bytes)}
                    self.motor_ready.emit(controller_id, 2)
                elif message_id == "B8" and len(data_bytes) == 5:  # QEC; Set desired quadrature encoder's position
                    status_update = {"sEncoder": self.get_32bit(data_bytes)}
                    self.motor_ready.emit(controller_id, 2)
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
                else:  # CURn; MCSn; ENA; OFF;
                    acr, ena, direction, mcs = self.analyze_message_id(int(message_id, 16))
                    status_update = {"acr": acr, "ena": ena, "direction": direction, "mcs": mcs}
                    if len(data_bytes) == 9:  # All messages should return 9 data bytes
                        status_update.update({
                            "rCur": self.get_current(data_bytes[0]),
                            "rSpd": self.get_16bit(data_bytes[1:4]),
                            "rDisplacement": self.get_32bit(data_bytes[4:])
                        })
                        self.motor_ready.emit(controller_id, ena)

            elif header == "CC":  # Feedback header "CC"
                if message_id == "B1" and len(data_bytes) == 5:  # QEC; Check current quadrature encoder's position
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
                    self.motor_ready.emit(controller_id, 1)
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