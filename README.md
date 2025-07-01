Raspberry Pi BLE Server
========== 
Python GATT server example for the Raspberry Pi
 
Copyright (c) 2019, Douglas Otwell

Distributed under the MIT license http://opensource.org/licenses/MIT 

Modified by Sandith Ganhewage

Prerequisites
-------------
As of BlueZ version 5.43 (currently shipped with Raspbian Stretch),
some BLE aspects are still experimental. You will need to add the
'Experimental' flag to the bluetooth daemon. Do this:
    sudo nano /etc/systemd/system/dbus-org.bluez.service
and add the '-E' flag at the end of the 'ExecStart' line. It should
look like this:

    ExecStart=/usr/lib/bluetooth/bluetoothd -E

Save the file and reboot.

Installation 
------------
    git clone https://github.com/sganhewage/rpi-ble.git

Usage 
----- 
    python3 rpiSort.py

The server should by accessible by any BLE client
