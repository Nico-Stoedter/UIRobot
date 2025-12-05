import serial
import threading

class RS232(serial.Serial):
    """Reiner serieller Transport mit Thread-Safety"""

    def __init__(self, port, baudrate, bytesize, parity, stopbits, **kwargs):
        super().__init__(port=port, baudrate=baudrate, bytesize=bytesize,
                         parity=parity, stopbits=stopbits, **kwargs)
        self.lock = threading.Lock()

    def write(self, data, print_log: bool, *args, **kwargs):
        with self.lock:
            super().write(data, *args, **kwargs)
            if print_log:
                print(f"Sent: {data}")

    def read_until(self, terminator=b'\n', *args, **kwargs):
        with self.lock:
            return super().read_until(terminator, *args, **kwargs)