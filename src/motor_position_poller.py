from PySide6.QtCore import Signal, QObject, QTimer, Slot

class MotorPositionPoller(QObject):
    poll_motor = Signal(int)           # motor_id 
    position_ready = Signal(int, int)  # motor_id, position
    polling_started = Signal()
    polling_stopped = Signal()
    
    def __init__(self):
        super().__init__()
        self.motor_ids = []  # Wird per Signal gesetzt
        self.motor_index = 0
        self.polling_timer = QTimer(self)
        self.polling_timer.timeout.connect(self._poll_next)

    @Slot(list)
    def set_motor_ids(self, motor_ids):
        """Gets Motoradress list after Scan per Signal"""
        self.motor_ids = motor_ids
        self.motor_index = 0
        print(f"Poller: {len(motor_ids)} Motoren konfiguriert")
        self.start_polling(1000)

    def start_polling(self, interval_ms):
        """Startet kontinuierliche Abfragen"""
        self.polling_timer.start(interval_ms)
        self.polling_started.emit()

    def stop_polling(self):
        """Stoppt Polling"""
        self.polling_timer.stop()
        self.polling_stopped.emit()

    def _poll_next(self):
        """Nächsten Motor abfragen (Round-Robin)"""
        if not self.motor_ids:
            return
            
        motor_id = self.motor_ids[self.motor_index]
        self.poll_motor.emit(motor_id)  # An MotorManager
        
        self.motor_index = (self.motor_index + 1) % len(self.motor_ids)