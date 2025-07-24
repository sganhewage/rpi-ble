import serial
import threading
import time

class AR488Monitor:
    def __init__(self, port='/dev/tty/USB0', baudrate=115200, append_cr=True, append_lf=False):
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
        self.write("++spoll")
        time.sleep(0.2)
        status = self.read().strip()
        # invalid literal for int() with base 16: '0\r\n0\r\n0'
        if status and status.startswith('0x'):
            status = status.split('\r\n')[0]
        elif status and status.startswith('0'):
            status = status.split('\r\n')[0]
        if status:
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
        while True:
            cmd = input(">> ")
            if cmd.lower() in ["exit", "quit"]:
                break
            ar.write(cmd)
            time.sleep(0.5)
            print("📥 Response:", ar.read())
    finally:
        ar.close()
