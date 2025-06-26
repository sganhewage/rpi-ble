import pyvisa
import subprocess
import time

def list_usb_devices():
    try:
        subprocess.run(["sudo udevadm control --reload"], check=True)
    except Exception as e:
        print(f"Firmware load failed or not needed: {e}")
    
    
    try:
        subprocess.run(["sudo /usr/sbin/gpib_config"], check=True)
    except Exception as e:
        print(f"gpib_config failed: {e}")
        
    for i in range(10):
        if subprocess.call(["test", "-e", "/dev/gpib0"]) == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError("/dev/gpib0 did not appear")
    
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