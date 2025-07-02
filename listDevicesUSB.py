import pyvisa

def list_usb_devices():
    """List all USB devices connected to the system."""
    rm = pyvisa.ResourceManager()
    print("Opened Resource Manager")
    devices = rm.list_resources()
    print(f"Found devices: {devices}")
    
    usb_devices = {}
    for device in devices:
        if 'GPIB' in device:
            try:
                resource = rm.open_resource(device)
                idn = resource.query('*IDN?')
                usb_devices[device] = idn.strip()
                resource.close()
            except Exception as e:
                usb_devices[device] = f"Error: {str(e)}"
    
    return usb_devices

if __name__ == "__main__":
    devices = list_usb_devices()
    if devices:
        print("Connected USB Devices:")
        for device, idn in devices.items():
            print(f"{device}: {idn}")
    else:
        print("No USB devices found.")