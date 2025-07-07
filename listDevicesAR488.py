from AR488Monitor import AR488Monitor
import time

def list_devices():
    """List all GPIB devices connected to the system."""
    monitor1 = AR488Monitor()
    monitor1.write("++fndl")
    time.sleep(0.1)
    devices: list = monitor1.get_buffer().splitlines()
    devices = [line.strip() for line in devices if line.strip()]
    # monitor.close()
    
    monitor2 = AR488Monitor()
    ret_devices = {}
    if len(devices) > 0:
        for device in devices:
            monitor2.write(f"++addr {device}")
            time.sleep(0.1)
            monitor2.write("*IDN?")
            time.sleep(0.1)
            response = monitor2.get_buffer().strip()
            if response:
                ret_devices[f"GPIB0::{device}::INSTR"] = response
            print(f"Device at address {device}: {response}")
    else:
        print("🔍 No devices found.")
        
    monitor1.close()
    monitor2.close()
    return ret_devices

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        print(devices)
    else:
        print("No GPIB devices found.")
