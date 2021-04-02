# Note: Dumping U2 takes a looooooong time.

import urjtag

CS_ADDR  = 0x10C00003
DATA_ADDR = 0x10000000
CMD_ADDR = 0x10000001
ADDR_ADDR = 0x10000002

# Flash layout:
# 1 page = (2k + 64)=2112 bytes
# 1 block = 64 pages
# 1 device = 1024 blocks = 65536 pages

class Jtagger(object):
    def __init__(self, filename="dump.u2"):
        self.c = urjtag.chain()
        self.outfile = open(filename, "wb")

    def connect(self):
        self.c.cable("UsbBlaster")
        self.c.tap_detect()

    def u2_cs(self, enabled):
        self.c.poke(CS_ADDR, 1 if enabled else 0)

    def u2_reset(self):
        print("Resetting U2")
        self.u2_cs(1)
        self.c.poke(CMD_ADDR, 0xFF)
        self.u2_cs(0)

    def u2_read_device(self):
        print("Read U2 device info")
        self.u2_cs(1)
        self.c.poke(CMD_ADDR, 0x90)
        self.c.poke(ADDR_ADDR, 0x00)
        maker = self.c.peek(DATA_ADDR) & 0xFF
        device = self.c.peek(DATA_ADDR) & 0xFF
        self.u2_cs(0)
        print("Device info:", hex(maker), hex(device))

    def u2_read_page(self, page):
        print("Reading page", page)
        self.u2_cs(1)
        self.c.poke(CMD_ADDR, 0x00) # Read command cycle 1
        self.c.poke(ADDR_ADDR, 0x00)
        self.c.poke(ADDR_ADDR, 0x00)

        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        self.c.poke(CMD_ADDR, 0x30) # Read command cycle 2
        for _ in range(2112):
            b = self.c.peek(DATA_ADDR) & 0xFF
            self.outfile.write(b.to_bytes(1, byteorder='big'))
        self.u2_cs(0)

    def cleanup(self):
        self.outfile.close()

if __name__ == "__main__":
    print("Starting")
    jtag = Jtagger()
    jtag.connect()
    jtag.u2_reset()
    jtag.u2_read_device()
    for page in range(65536):
        jtag.u2_read_page(page)

    jtag.cleanup()
    print("Done")
