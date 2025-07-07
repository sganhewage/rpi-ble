from AR488Monitor import AR488Monitor
import time

def list_devices():
    """List all GPIB devices connected to the system."""
    monitor = AR488Monitor()
    monitor.write("++fndl")
    time.sleep(0.5)
    devices: list = monitor.get_buffer().splitlines()
    devices = [line.strip() for line in devices if line.strip()]
    monitor.close()
    
    monitor = AR488Monitor()
    ret_devices = {}
    if len(devices) > 0:
        for device in devices:
            monitor.write(f"++addr {device}")
            time.sleep(0.5)
            monitor.write("*IDN?")
            time.sleep(1.0)
            response = monitor.get_buffer().strip()
            if response:
                ret_devices[f"GPIB0::{device}::INSTR"] = response
            print(f"Device at address {device}: {response}")
    else:
        print("🔍 No devices found.")
        
    monitor.close()
    return ret_devices

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        print(devices)
    else:
        print("No GPIB devices found.")
