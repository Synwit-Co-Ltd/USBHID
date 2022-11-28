from . import codec


class RAMDisk(codec.Codec):
    SIGNATURE = 0x43444948

    def __init__(self, ui):
        super(RAMDisk, self).__init__(ui)

        self.ui = ui
    
    def send(self, text):
        try:
            list = text.split()
            if list[0] == 'erase':
                sector, count = int(list[1]), int(list[2])

                cmd = [0x71, 14]
                cmd.extend(self.int2list(sector))
                cmd.extend(self.int2list(count))
                
            elif list[0] == 'write':
                page, data = int(list[1]), [int(x, 16) for x in list[2:]]

                cmd = [0xC3, 14]
                cmd.extend(self.int2list(page))
                cmd.extend(self.int2list(0))

            elif list[0] == 'read':
                page = int(list[1])

                cmd = [0xD2, 14]
                cmd.extend(self.int2list(page))
                cmd.extend(self.int2list(0))

            else:
                raise Exception()

        except Exception as e:
            self.ui.txtMain.append('\nInvalid Command\n')
            return

        try:
            cmd.extend(self.int2list(self.SIGNATURE))
            cmd.extend(self.int2list(sum(cmd)))

            self.ui.txtMain.append('\nTX: %s\n' %''.join(['%02X ' %x for x in cmd]))

            self.ui.dev.write(cmd)

            if list[0] == 'write':
                data.extend([0xFF] * (256 - len(data)))
                for i in range(256 // 64):
                    self.ui.dev.write(data[64*i:64*(i+1)])

        except Exception as e:
            self.ui.txtMain.append('\nCommand send fail\n')

    def recv(self, list):
        text = ''.join([f'{x:02X} ' for x in list])

        self.ui.txtMain.append(f'RX:\n{text}\n')

    def info(self):
        self.ui.txtMain.clear()
        self.ui.txtMain.append('''read and write RAMDisk through hid command, supported command:

erase <start sector> <sector count>
erase 0 1

write <page number>
write 0 00 11 AA FF 99 ... <up to 256 bytes>

read <page number>
read 0

note: page size is 256 bytes, sector size is 1024 bytes, total size is 4096 bytes\n\n''')
