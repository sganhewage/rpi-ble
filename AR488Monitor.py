import serial
import threading
import time

class AR488Monitor:
    def __init__(self, port='/dev/cu.usbserial-10', baudrate=115200, append_cr=True, append_lf=False):
        self.port = port
        self.baudrate = baudrate
        self.append_cr = append_cr
        self.append_lf = append_lf
        self.ser = None
        self.buffer = ""
        self.lock = threading.Lock()
        self._stop_thread = False

        self._connect()
        self._start_reader()

    def _connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
        time.sleep(2)  # Arduino reset time
        print(f"✅ Connected to {self.port} at {self.baudrate} baud.")

    def _start_reader(self):
        thread = threading.Thread(target=self._reader_loop, daemon=True)
        thread.start()

    def _reader_loop(self):
        while not self._stop_thread:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                    with self.lock:
                        self.buffer += data
            except Exception as e:
                print(f"[Read error] {e}")
            time.sleep(0.05)

    def write(self, command: str):
        """Sends a command and clears the buffer before doing so."""
        with self.lock:
            self.buffer = ""
        line = command
        if self.append_cr:
            line += '\r'
        if self.append_lf:
            line += '\n'
        self.ser.write(line.encode())

    def read(self) -> str:
        """Returns whatever was received since the last write."""
        with self.lock:
            return self.buffer.strip()
        
    def getStatusByte(self) -> int:
        """Returns the status byte from the device."""
        self.write("++clr")
        time.sleep(0.1)
        self.write("++spoll")
        time.sleep(1)
        status = self.read()
        if not status:
            print("No status byte received.")
            return -1
        
        return int(status)

    def close(self):
        self._stop_thread = True
        time.sleep(0.1)
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Serial port closed.")

# Example usage
if __name__ == "__main__":
    ar = AR488Monitor()

    try:
        ar.write("++addr 1")
        print(ar.getStatusByte())

    finally:
        ar.close()
