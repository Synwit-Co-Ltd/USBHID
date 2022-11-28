
class Interface(object):

    @staticmethod
    def get_all_connected_interfaces():
        return []

    def __init__(self):
        self.vid = 0
        self.pid = 0
        self.vendor_name = ""
        self.product_name = ""

        self.packet_size = 64
    
    def open(self):
        return

    def write(self, data):
        return

    def read(self, size=-1, timeout=-1):
        return

    def info(self):
        return '%s %s (%04X, %04X)' %(self.vendor_name, self.product_name, self.vid, self.pid)

    def close(self):
        return
