import pyvisa

def list_usb_devices():
    """List all USB devices connected to the system."""
    rm = pyvisa.ResourceManager()
    print("Opened Resource Manager")
    
    possible_addresses = [f"GPIB0::{i}::INSTR" for i in range(1, 32)]
    
    print("Checking possible GPIB addresses...")
    usb_devices = {}
    for device in possible_addresses:
        print(f"Checking {device}...")
        try:
            resource = rm.open_resource(device)
            resource.timeout = 500  # Set timeout to 0.5 seconds
            idn = resource.query('*IDN?')
            usb_devices[device] = idn.strip()
            print(f"Found device at {device}: {idn.strip()}")
            resource.close()
        except Exception as e:
            print(f"Failed to connect to {device}: {str(e)}")
    
    return usb_devices

if __name__ == "__main__":
    devices = list_usb_devices()
    if devices:
        print("Connected USB Devices:")
        for device, idn in devices.items():
            print(f"{device}: {idn}")
    else:
        print("No USB devices found.")