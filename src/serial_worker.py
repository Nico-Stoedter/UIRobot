import serial
from PySide6.QtCore import QObject, QTimer, Signal, Slot

class SerialWorker(QObject):
    data_received = Signal(bytes)  # Signal for sending received data
    finished = Signal()  # Signal for thread completion
    connection_failed = Signal(Exception)  # Signal for connection failure

    def __init__(self, port, baudrate):
        super().__init__()
        self.serial_connection = None
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.timer = None

    @Slot()
    def start_serial(self):
        """Connect to the serial port and start reading."""
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.read_data)
            self.timer.start(10)  # Check every 10ms
        except serial.SerialException as e:
            self.connection_failed.emit(e)
            self.stop()

    @Slot()
    def read_data(self):
        """Read data asynchronously and emit via signal."""
        #print(self.running, self.serial_connection, self.serial_connection.is_open)
        if self.running and self.serial_connection and self.serial_connection.is_open:
            #print(self.serial_connection.in_waiting)
            if self.serial_connection.in_waiting:
                data = self.serial_connection.read_until(b'\xff')
                self.data_received.emit(data)  # Processed safely in GUI thread

    def send_message(self, message):
        """Send a message via the serial port."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(message.encode('utf-8'))
            print(f"Sent: {message}")

    @Slot()
    def stop(self):
        """Stop the serial communication."""
        self.running = False

        if self.timer is not None:
            self.timer.stop()
            #self.timer.deleteLater()
            self.timer = None

        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

        self.serial_connection = None
        self.finished.emit()