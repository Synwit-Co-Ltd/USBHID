import os
import time
import logging
import collections

from .interface import Interface

log = logging.getLogger('pywinusb')


try:
    import pywinusb.hid as hid
    IS_AVAILABLE = True
except:
    IS_AVAILABLE = False
    

class PyWinUSB(Interface):
    '''
    This class provides basic functions to access a USB HID device using pywinusb:
        - write/read an endpoint
    '''

    isAvailable = IS_AVAILABLE

    @staticmethod
    def get_all_connected_interfaces():
        devices = []

        for dev in hid.find_all_hid_devices():
            try:
                dev.open(shared=True)

                device = PyWinUSB()
                device.vendor_name = dev.vendor_name
                device.product_name = dev.product_name
                device.vid = dev.vendor_id
                device.pid = dev.product_id
                device.dev = dev
                device.report = dev.find_output_reports()[0]
                devices.append(device)

                dev.close()

            except Exception as e:
                dev.close()

        return devices

    def __init__(self):
        super(PyWinUSB, self).__init__()
        self.dev = None
        
        self.report = None

        self.rcv_data = collections.deque()
    
    # handler called when a report is received
    def rx_handler(self, data):
        self.rcv_data.append(data[1:])

    def open(self):
        self.dev.set_raw_data_handler(self.rx_handler)

        start = time.time()
        while time.time() - start < 5:
            try:
                self.dev.open(shared=False)
                break
            except hid.HIDError:
                pass

            # Attempt to open the device in shared mode to make sure it is still there
            try:
                self.dev.open(shared=True)
                self.dev.close()
            except hid.HIDError as exc:
                raise Exception('Unable to open device')

        else:
            # If this timeout has elapsed then another process
            # has locked this device in shared mode. This should not happen.
            assert False

    def write(self, data):
        ''' write data on the OUT endpoint associated to the HID interface '''
        for _ in range(self.packet_size - len(data)):
            data.append(0)
        self.report.send([0] + data)

    def read(self, timeout=20.0):
        ''' read data on the IN endpoint associated to the HID interface '''
        if len(self.rcv_data): 
            return self.rcv_data.popleft()
                    
        return []
    
    def close(self):
        self.dev.close()
