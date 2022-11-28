import os
import logging

from .interface import Interface

log = logging.getLogger('hidapi')


try:
    import hid
    IS_AVAILABLE = True
except:
    IS_AVAILABLE = False


class HIDApi(Interface):
    '''
    This class provides basic functions to access a USB HID device using cython-hidapi:
        - write/read an endpoint
    '''

    isAvailable = IS_AVAILABLE

    @staticmethod
    def get_all_connected_interfaces():
        devices = []

        for devInfo in hid.enumerate():
            try:
                dev = hid.device(vendor_id=devInfo['vendor_id'], product_id=devInfo['product_id'], path=devInfo['path'])
            except IOError:
                continue

            # Create the USB interface object for this device.
            device = HIDApi()
            device.vendor_name  = devInfo['manufacturer_string']
            device.product_name = devInfo['product_string']
            device.vid = devInfo['vendor_id']
            device.pid = devInfo['product_id']
            device.dev_info = devInfo
            device.dev = dev
            devices.append(device)

        return devices

    def __init__(self):
        super(HIDApi, self).__init__()
        self.dev = None

    def open(self):
        try:
            self.dev.open_path(self.dev_info['path'])
            self.dev.set_nonblocking(True)
        except IOError as exc:
            raise Exception('Unable to open device')

    def write(self, data):
        ''' write data on the OUT endpoint associated to the HID interface '''
        for _ in range(self.packet_size - len(data)):
            data.append(0)
        self.dev.write([0] + data)

    def read(self, timeout=-1):
        ''' read data on the IN endpoint associated to the HID interface '''
        return self.dev.read(self.packet_size)

    def close(self):
        self.dev.close()
