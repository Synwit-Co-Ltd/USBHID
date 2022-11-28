import os
import time
import logging
import threading

from .interface import Interface

log = logging.getLogger('pyusb')


try:
    import usb
    IS_AVAILABLE = True
except:
    IS_AVAILABLE = False
    

class PyUSB(Interface):
    '''
    This class provides basic functions to access a USB device using pyusb:
        - write/read an endpoint
    '''

    isAvailable = IS_AVAILABLE

    @staticmethod
    def get_all_connected_interfaces():
        devices = []

        for dev in usb.core.find(find_all=True):
            try:
                device = PyUSB()
                device.vendor_name = dev.manufacturer
                device.product_name = dev.product
                device.vid = dev.idVendor
                device.pid = dev.idProduct

                devices.append(device)

            except Exception as e:
                pass

        return devices

    def __init__(self):
        super(PyUSB, self).__init__()
        self.dev = None

        self.intf_number = None
        
        self.ep_out = None
        self.ep_in = None

        self.rcv_data = []
        self.thread = None
    
    def open(self):
        for dev in usb.core.find(find_all=True):
            try:
                if dev.idVendor == self.vid and dev.idProduct == self.pid:
                    self.dev = dev
                    break
            except Exception as e:
                pass
        
        config = self.dev.get_active_configuration()

        interface = config[(0, 0)]

        self.intf_number = interface.bInterfaceNumber

        for ep in interface:
            if ep.bEndpointAddress & 0x80: self.ep_in  = ep
            else                         : self.ep_out = ep

        try:
            usb.util.claim_interface(self.dev, self.intf_number)
        except usb.core.USBError as e:
            raise e

        self.closed = False
        self.thread = threading.Thread(target=self.rcv_task)
        self.thread.daemon = True
        self.thread.start()

    def rcv_task(self):
        while not self.closed:
            try:
                self.rcv_data.append(self.ep_in.read(self.packet_size, 100))
                time.sleep(0.1)
            except Exception as e:
                pass

    def read(self, timeout=20.0):
        ''' read data on the IN endpoint '''
        if len(self.rcv_data): 
            return self.rcv_data.pop(0)
        
        return []

    def write(self, data):
        ''' write data on the OUT endpoint '''
        for i in range(self.packet_size - len(data)):
            data.append(0)

        self.ep_out.write(data)
    
    def close(self):
        self.closed = True
        self.thread.join()

        usb.util.release_interface(self.dev, self.intf_number)
        usb.util.dispose_resources(self.dev)
