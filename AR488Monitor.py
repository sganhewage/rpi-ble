import serial
import threading
import time

# === CONFIGURATION ===
PORT = '/dev/cu.usbserial-10'   # Update this to your serial port
BAUDRATE = 115200
APPEND_CR = True     # Append carriage return (\r)
APPEND_LF = False    # Append line feed (\n)
# ======================

class AR488Monitor:
    def __init__(self, port=PORT, baudrate=BAUDRATE, append_cr=APPEND_CR, append_lf=APPEND_LF):
        self.port = port
        self.baudrate = baudrate
        self.append_cr = append_cr
        self.append_lf = append_lf
        self.ser = None
        self._buffer = ""
        self._stop_reader = False
        self._lock = threading.Lock()
        self._connect()
        self._start_reader()


    def _connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
        time.sleep(2)  # Let device reset
        print(f"✅ Connected to {self.port} at {self.baudrate} baud.")

    def _start_reader(self):
        thread = threading.Thread(target=self._read_from_serial, daemon=True)
        thread.start()

    def _read_from_serial(self):
        while not self._stop_reader:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                    with self._lock:
                        self._buffer += data
                    print(data, end='', flush=True)
            except Exception as e:
                print(f"[Read error]: {e}")
            time.sleep(0.01)


    def write(self, command: str):
        """Write a command to the serial port and reset response buffer."""
        with self._lock:
            self._buffer = ""  # clear previous response
        if self.append_cr:
            command += '\r'
        if self.append_lf:
            command += '\n'
        self.ser.write(command.encode())

    def get_buffer(self) -> str:
        """Return the latest buffered response (since last write)."""
        with self._lock:
            return self._buffer.strip()

    def close(self):
        self._stop_reader = True  # tell thread to exit cleanly
        time.sleep(0.05)          # short pause to allow thread to exit
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Serial port closed.")

    def interactive(self):
        print("📝 Type commands below. Type 'exit' or 'quit' to close.")
        try:
            while True:
                line = input()
                if line.lower() in ["exit", "quit"]:
                    break
                self.write(line)
                time.sleep(0.1)
                print(f"\n📦 Response Buffer:\n{self.get_buffer()}\n")
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.close()

# Example usage
if __name__ == "__main__":
    monitor = AR488Monitor()
    # monitor.write("++verbose 0")
    monitor.write("++fndl")
    time.sleep(0.5)
    print(monitor.get_buffer())
    monitor.close()
    
    monitor = AR488Monitor()
    monitor.write("++addr 5")
    time.sleep(0.5)
    monitor.write("*IDN?")
    time.sleep(1.0)
    response = monitor.get_buffer()
    print("Device responded:", response)
    
    monitor.write("++addr 7")
    time.sleep(0.5)
    monitor.write("*IDN?")
    time.sleep(1.0)
    response = monitor.get_buffer()
    print("Device responded:", response)
    
    monitor.write("++addr 5")
    time.sleep(0.5)
    monitor.write("*IDN?")
    time.sleep(1.0)
    response = monitor.get_buffer()
    print("Device responded:", response)
    monitor.close()

