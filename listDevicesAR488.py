from AR488Monitor import AR488Monitor
import time

def list_devices():
    """List all GPIB devices connected to the system."""
    monitor1 = AR488Monitor()
    monitor1.write("++fndl")
    response = monitor1.read().strip()
    devices: list = response.splitlines()
    devices = [line.strip() for line in devices if line.strip()]
    print(f"Response from ++fndl: {devices}")
    # monitor1.write("++clr")
    
    time.sleep(0.2)
    ret_devices = {}
    if len(devices) > 0:
        for device in devices:
            monitor1.write(f"++addr {device}")
            monitor1.write("++clr")
            monitor1.write("*IDN?")
            time.sleep(0.2)
            response = monitor1.manual_read().strip()

            if response:
                ret_devices[f"GPIB0::{device}::INSTR"] = response
            print(f"Device at address {device}: {response}")
    else:
        print("🔍 No devices found.")

    monitor1.close()
    return ret_devices

if __name__ == "__main__":
    response = list_devices()
    if response:
        print(f"Device identification: {response}")
    else:
        print("No GPIB devices found.")
