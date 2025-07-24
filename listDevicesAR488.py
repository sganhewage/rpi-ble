from AR488Monitor import AR488Monitor
import time

def list_devices():
    """List all GPIB devices connected to the system."""
    monitor1 = AR488Monitor()
    monitor1.write("++fndl")
    time.sleep(0.5)
    response = monitor1.read().strip()
    print(f"Response from ++fndl: {response}")
    devices: list = monitor1.read().splitlines()
    devices = [line.strip() for line in devices if line.strip()]
    monitor1.write("++clr")
    
    time.sleep(0.1)
    ret_devices = {}
    if len(devices) > 0:
        for device in devices:
            monitor1.write(f"++addr {device}")
            time.sleep(0.1)
            monitor1.write("*IDN?")
            time.sleep(0.1)
            response = monitor1.read().strip()

            if response:
                ret_devices[f"GPIB0::{device}::INSTR"] = response
            print(f"Device at address {device}: {response}")
    else:
        print("🔍 No devices found.")

    monitor1.close()
    return ret_devices

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        print(devices)
    else:
        print("No GPIB devices found.")
