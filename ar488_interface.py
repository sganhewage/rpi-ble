import serial
import threading
import time
import re

class AR488:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1,
                 append_cr: bool = True, append_lf: bool = False, monitor_output: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.append_cr = append_cr
        self.append_lf = append_lf
        self.monitor_output = monitor_output

        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.buffer = ""
        self._stop_thread = False
        self._reader_thread = threading.Thread(target=self._read_from_port, daemon=True)
        self._reader_thread.start()

        time.sleep(2)  # Wait for Arduino to reset
        print(f"✅ Connected to {port} at {baudrate} baud.")

    def _read_from_port(self):
        while not self._stop_thread:
            if self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                    self.buffer += data
                    if self.monitor_output:
                        print(data, end='', flush=True)
                except Exception as e:
                    print(f"[Read error]: {e}")
            time.sleep(0.01)

    def close(self):
        self._stop_thread = True
        if self.ser and self.ser.is_open:
            time.sleep(0.2)
            self.ser.close()
            print("🔌 Serial port closed.")

    def flush(self):
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.buffer = ""

    def send(self, command: str):
        """Send a raw command to AR488, appending CR/LF as configured."""
        if self.append_cr:
            command += '\r'
        if self.append_lf:
            command += '\n'
        self.ser.write(command.encode())

    def read(self, wait: float = 0.5) -> str:
        """Return the current contents of the buffer after waiting briefly."""
        time.sleep(wait)
        result = self.buffer.strip()
        self.buffer = ""  # Clear buffer after read
        return result

    def send_and_read(self, command: str, wait: float = 0.5) -> str:
        """Send a command, wait, then read response."""
        self.send(command)
        return self.read(wait=wait)

    def set_address(self, addr: int):
        self.send(f"++addr {addr}")

    def identify(self, addr: int = None) -> str:
        if addr is not None:
            self.set_address(addr)
        self.send("*IDN?")
        return self.send_and_read("++read", wait=1.0)

def list_gpib_devices(gpib: AR488) -> list:
    devices = []

    try:
        gpib.flush()
        gpib.send("++eoi 1")
        gpib.send("++mode 1")

        print("🔍 Sending ++fndl...")
        gpib.send("++fndl")
        response = gpib.read()
        print(f"🧾 ++fndl response: {response.strip()}")

        addresses = list(map(int, re.findall(r'\b\d+\b', response)))
        print(f"🎯 Found listeners: {addresses}")

        for addr in addresses:
            print(f"\n📡 Querying GPIB address {addr}")
            gpib.set_address(addr)
            gpib.send("*IDN?")
            time.sleep(0.5)
            gpib.send("++read")
            idn = gpib.read(wait=1.0).strip()
            print(f"🔖 {addr}: {idn or 'No response'}")
            devices.append({'gpib_address': addr, 'idn': idn or 'No response'})

    finally:
        gpib.close()

    return devices

if __name__ == "__main__":
    port = "/dev/cu.usbserial-10"  # Your device port
    gpib = AR488(port=port, monitor_output=True)
    results = list_gpib_devices(gpib)
    print("\n📋 GPIB Devices Found:")
    for d in results:
        print(f" - Address {d['gpib_address']}: {d['idn']}")
