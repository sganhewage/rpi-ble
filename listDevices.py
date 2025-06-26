import serial
import threading
import time

# === CONFIGURATION ===
PORT = '/dev/cu.usbserial-10'   # Change to your port
BAUDRATE = 115200
APPEND_CR = True     # Carriage Return (\r)
APPEND_LF = False    # Line Feed (\n)
# ======================

def read_from_port(ser):
    """Continuously read from serial and print to screen."""
    while True:
        if ser.in_waiting:
            try:
                data = ser.read(ser.in_waiting).decode(errors='ignore')
                print(data, end='', flush=True)
            except Exception as e:
                print(f"[Read error]: {e}")

def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        time.sleep(2)  # Wait for Arduino reset
        print(f"✅ Connected to {PORT} at {BAUDRATE} baud.\nType your commands below:")

        # Start background reader
        reader = threading.Thread(target=read_from_port, args=(ser,), daemon=True)
        reader.start()

        # Command loop
        while True:
            line = input()
            if line.lower() in ["exit", "quit"]:
                break

            # Append terminators
            if APPEND_CR:
                line += '\r'
            if APPEND_LF:
                line += '\n'

            ser.write(line.encode())

    except serial.SerialException as e:
        print(f"❌ Could not open serial port: {e}")
    finally:
        try:
            ser.close()
        except:
            pass
        print("🔌 Serial port closed.")

if __name__ == "__main__":
    main()
