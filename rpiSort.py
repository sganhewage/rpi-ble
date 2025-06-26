#!/usr/bin/python3

"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dbus

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

#from listDevices import list_devices
from listDevicesUSB import list_usb_devices
import json

from handlerFunctions import main
from gpib_usb_configure import configureDevice


GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

LOCAL_NAME = "rpi-sort"
val_buffer = ''  # Global buffer to hold incoming values

class BLEAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name(LOCAL_NAME)
        configureDevice()  # Configure the GPIB device if needed
        # self.include_tx_power = True

class BLEService(Service):
    BLE_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.address = None
        self.ids: set = None

        Service.__init__(self, index, self.BLE_SVC_UUID, True)
        self.add_characteristic(AvailableDevicesCharacteristic(self))
        self.add_characteristic(SendIDsCharacteristic(self))
        self.add_characteristic(SetAddressCharacteristic(self))

    def sendJob(self):
        print(f"Starting job with address: {self.address} and IDs: {self.ids}")
        if self.address is not None and self.ids is not None:
            main(GPIBaddr=self.address, numParts=len(self.ids), IDset=set(self.ids))
        else:
            print("Address or IDs not set. Cannot start job.")

    def getAddress(self):
        return (self.address)

    def set_address(self, address):
        self.address = address
 
    def set_ids(self, ids):
        self.ids = ids
        
    def getIds(self):
        if self.ids is not None:
            return self.ids
        else:
            return []

class AvailableDevicesCharacteristic(Characteristic):
    GET_DEVICES_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"
    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.GET_DEVICES_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(TempDescriptor(self))

    def get_devices(self):
        devices = list_usb_devices()
        device_str = json.dumps(devices)  # Convert dict/list to JSON string
        return [dbus.Byte(c.encode()) for c in device_str]

    def set_get_device_callback(self):
        if self.notifying:
            value = self.get_devices()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_devices()
        print("GetDeviceCharacteristic StartNotify: " + str(value))
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_get_device_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_devices()

        return value

class TempDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "CPU Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TEMP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class SendIDsCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.UNIT_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(UnitDescriptor(self))

    def WriteValue(self, value, options):
        global val_buffer
        
        #convert value to string
        EOI_KEY = '**!@ble-eoi@!**'
        
        incoming = ''.join([chr(b) for b in value]).strip()
        if incoming == EOI_KEY:
            values = val_buffer.split(',')
            self.service.set_ids(set(values))
            print(f"Received IDs: {values}")
            self.service.sendJob()
            val_buffer = ''
            
        else:
            val_buffer += incoming

    def ReadValue(self, options):
        value = []

        if self.service.is_farenheit(): val = "F"
        else: val = "C"
        value.append(dbus.Byte(val.encode()))

        return value

class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Temperature Units (F or C)"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.UNIT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class SetAddressCharacteristic(Characteristic):
    UUID = '00000004-710e-4a5b-8d75-3e5b444b3c3f'  # ← Pick a new UUID

    def __init__(self, service):
        Characteristic.__init__(self, self.UUID,
                                ['write'],
                                service)

    def WriteValue(self, value, options):
        command = ''.join([chr(b) for b in value])
        print(f"Received command: {command}")
        
        self.service.set_address(command.strip())
        print(f"Address set to: {self.service.getAddress()}")

app = Application()
app.add_service(BLEService(0))
app.register()

adv = BLEAdvertisement(0)
adv.add_service_uuid(BLEService.BLE_SVC_UUID)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
