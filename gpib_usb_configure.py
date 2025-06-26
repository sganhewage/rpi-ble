import os
import subprocess
import time

# Optional: switch to root directory (if needed for your logic)
# os.chdir("/")

def configureDevice():
    # Step 1: Reload udev rules
    try:
        subprocess.run(["udevadm", "control", "--reload"], check=True)
        print("udev rules reloaded")
    except Exception as e:
        print("udev reload failed:", e)

    # Step 2: Trigger udev (simulate replugging all devices)
    try:
        subprocess.run(["udevadm", "trigger"], check=True)
        print("udev trigger executed")
    except Exception as e:
        print("udev trigger failed:", e)

    # Step 3: Wait for /dev/gpib0 to appear
    for i in range(10):
        if os.path.exists("/dev/gpib0"):
            print("/dev/gpib0 is now available")
            break
        time.sleep(1)
    else:
        raise RuntimeError("GPIB device did not appear")

    # Step 4: Run gpib_config (adjust path if needed)
    try:
        subprocess.run(["gpib_config"], check=True)
        print("gpib_config executed successfully")
    except Exception as e:
        print("gpib_config failed:", e)
        
if __name__ == "__main__":
    configureDevice()