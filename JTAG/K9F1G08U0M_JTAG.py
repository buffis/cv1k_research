# Note: Dumping a full device takes a LONG time (~60 hours).

import urjtag

CS_ADDR  = 0x10C00003
DATA_ADDR = 0x10000000
CMD_ADDR = 0x10000001
ADDR_ADDR = 0x10000002

# Flash layout:
# 1 page = (2k + 64)=2112 bytes
# 1 block = 64 pages
# 1 device = 1024 blocks = 65536 pages

class K9F1G08U0MJtag(object):
    """Lib for talking with K9F1G08U0M through UsbBlaster JTAG."""
    def __init__(self):
        self.c = urjtag.chain()

    def connect(self):
        self.c.cable("UsbBlaster")
        self.c.tap_detect()

    def cs(self, enabled):
        self.c.poke(CS_ADDR, 1 if enabled else 0)

    def reset(self):
        print("Resetting Flash")
        self.cs(1)
        self.c.poke(CMD_ADDR, 0xFF)
        self.cs(0)

    def read_id(self):
        print("Read Flash id")
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x90)
        self.c.poke(ADDR_ADDR, 0x00)
        maker = self.c.peek(DATA_ADDR) & 0xFF
        device = self.c.peek(DATA_ADDR) & 0xFF
        self.cs(0)
        print("Device info:", hex(maker), hex(device))

    def read_page(self, page):
        print("Reading page", page)
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x00) # Read command cycle 1
        self.c.poke(ADDR_ADDR, 0x00)
        self.c.poke(ADDR_ADDR, 0x00)
        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        self.c.poke(CMD_ADDR, 0x30) # Read command cycle 2
        page = bytearray()
        for _ in range(2112):
            page.append(self.c.peek(DATA_ADDR) & 0xFF)
        self.cs(0)
        return page

    def write_page(self, page, data):
        """UNTESTED: DONT USE THIS UNLESS YOU ARE BRAVE."""
        print("Writing page", page)
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x80) # Write command cycle 1
        self.c.poke(ADDR_ADDR, 0x00)
        self.c.poke(ADDR_ADDR, 0x00)
        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        for d in data:
            self.c.poke(DATA_ADDR, d & 0xFF)
        self.c.poke(CMD_ADDR, 0x10) # Write command cycle 2
        self.cs(0)
        return self.read_status()

    def read_status(self):
        """Reads status of flash. 0 means ok."""
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x70)
        status = self.c.peek(DATA_ADDR) & 0xFF
        self.cs(0)
        return status

if __name__ == "__main__":
    print("Starting")
    jtag = K9F1G08U0MJtag()
    jtag.connect()
    jtag.reset()

    if sys.argv[1] == "read_id":
        jtag.read_id()
    elif sys.argv[1] == "read_all":
        outfile = open("flashdump.bin", "wb")
        for page in range(65536):
            outfile.write(jtag.read_page(page))
        outfile.close()

    print("Done")
