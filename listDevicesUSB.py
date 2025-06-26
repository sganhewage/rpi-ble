import pyvisa
import subprocess
import time
from gpib_usb_configure import main

def list_usb_devices():
    """List all USB devices connected to the system."""
    rm = pyvisa.ResourceManager()
    devices = rm.list_resources()
    
    usb_devices = {}
    for device in devices:
        if 'GPIB' in device:
            try:
                resource = rm.open_resource(device)
                idn = resource.query('*IDN?')
                usb_devices[device] = idn.strip()
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