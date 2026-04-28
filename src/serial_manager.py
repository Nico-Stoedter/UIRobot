from PySide6.QtCore import QMetaObject, QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication

from src.serial_worker import SerialWorker

import time

class SerialManager(QObject):
    data_received = Signal(bytes)  # Signal for GUI thread
    exception_received = Signal(Exception)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

    def _clear_thread_references(self):
        """Drop Qt object references after the worker thread has fully stopped."""
        self.worker = None
        self.thread = None

    def open_connection(self, port, baudrate):
        """Start serial communication in a separate thread."""
        if self.thread and self.thread.isRunning():
            self.close_connection()

        # Most of the time opening a new Connection is faster than finishing the old Thread
        # to prevent a mix-up with the references we wait until the old self.thred reference is deleted
        while self.thread:
            QApplication.processEvents()  # keep GUI responsiv 
            QThread.msleep(10)

        if self.thread == None or self.worker == None:
            self.thread = QThread()
            self.worker = SerialWorker(port, baudrate)
            self.worker.connection_failed.connect(self.exception_received)
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.thread.started.connect(self.worker.start_serial)   
            self.worker.data_received.connect(self.data_received.emit)  # Forward data to GUI
            self.worker.finished.connect(self.thread.quit)
            self.thread.finished.connect(self.on_thread_finished) 

            self.thread.start()
        time.sleep(0.1)
        if not self.worker.running and self.worker == None:
            self.close_connection()
            return False, f"Connection to {port} failed."

        return True, f"Connected to {port} at {baudrate} baud."
    
    def on_thread_finished(self):
        self.worker.deleteLater()
        self.thread.deleteLater()
        self._clear_thread_references()

    def close_connection(self):
        """End the connection and stop the thread."""
        worker = self.worker
        thread = self.thread
        if worker is None or thread is None:
            return

        if worker.running:
            QMetaObject.invokeMethod(worker, "stop", Qt.BlockingQueuedConnection)

        if thread.isRunning():
            thread.quit()
            thread.wait()
        else:
            self._clear_thread_references()

    def is_open(self):
        """Check if a connection exists."""
        return self.worker is not None and self.worker.running

    def send_message(self, message):
        """Send a message via the serial connection."""
        if self.worker:
            self.worker.send_message(message)

    @Slot(Exception)
    def exception_receiveid(self, exception):
        self.exception_received.emit(exception)