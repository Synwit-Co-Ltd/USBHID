

class Codec(object):
    def __init__(self, ui):
        super(Codec, self).__init__()

        self.ui = ui
        
    def send(self, text):
        try:
            list = [int(x, 16) for x in text.split()]

            self.ui.dev.write(list)
        except Exception as e:
            self.ui.txtMain.append(str(e))
    
    def recv(self, list):
        text = ''.join([f'{x:02X} ' for x in list])

        self.ui.txtMain.append(f'\nRX: {text}\n')

    def info(self):
        self.ui.txtMain.clear()
        self.ui.txtMain.append('''Plain Hex Input and Output, for example:
71 0E 10 00 00 00 01 00 00 00 48 49 44 43 a8 01 00 00\n\n''')


    def int2list(self, int):
        return [int & 0xFF, (int >> 8) & 0xFF, (int >> 16) & 0xFF, (int >> 24) & 0xFF]

    def short2list(self, short):
        return [short & 0xFF, (short >> 8) & 0xFF]
