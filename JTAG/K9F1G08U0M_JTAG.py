import argparse
import sys
import urjtag

# Device info
# 1 page = (2k + 64)=2112 bytes
# 1 block = 64 pages
# 1 device = 1024 blocks = 65536 pages

DATA_ADDR = 0x10000000
CMD_ADDR  = 0x10000001
ADDR_ADDR = 0x10000002
CS_ADDR   = 0x10C00003

class K9F1G08U0MJtag(object):
    """Low level interface for doing stuff with a K9F1G08U0M."""
    def __init__(self):
        urjtag.loglevel(urjtag.URJ_LOG_LEVEL_WARNING)
        self.c = urjtag.chain()
    
    def connect(self): self.c.cable("UsbBlaster")
    def detect(self): self.c.tap_detect()
    def cs(self, enabled): self.c.poke(CS_ADDR, 1 if enabled else 0)

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

    def read_page(self, page, offset=0):
        print("Reading page", page)
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x00) # Read command cycle 1
        self.c.poke(ADDR_ADDR, offset & 0xFF)
        self.c.poke(ADDR_ADDR, (offset >> 8) & 0xFF)
        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        self.c.poke(CMD_ADDR, 0x30) # Read command cycle 2
        page = bytearray()
        for _ in range(2112-offset):
            page.append(self.c.peek(DATA_ADDR) & 0xFF)
        self.cs(0)
        return page

    def read_status(self):
        """Reads status of flash. 0 means ok."""
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x70)
        status = self.c.peek(DATA_ADDR) & 0xFF
        self.cs(0)
        return status

class JtagProgrammer(object):
    """Util for doing cool stuff to the NAND flash."""
    def __init__(self):
        self.jtag = K9F1G08U0MJtag()

    def setup(self):
        self.jtag.connect()
        self.jtag.detect()
        self.jtag.reset()

    def read_id(self): self.jtag.read_id()

    def read_page(self, filename, page):
        outfile = open(filename, "wb")
        outfile.write(self.jtag.read_page(page))
        outfile.close()

    def read_all(self, filename):
        outfile = open(filename, "wb")
        for page in range(65536):
            outfile.write(self.jtag.read_page(page))
        outfile.close()

def fail(msg):
    print("ERROR:", msg)
    sys.exit(1)

if __name__ == "__main__":
    print("Starting")
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str)
    p.add_argument('--filename', type=str, default='data.bin')
    p.add_argument('--block', type=int, default=0)
    p.add_argument('--page', type=int, default=0)
    args = p.parse_args()

    jtag = JtagProgrammer()
    jtag.setup()
    
    if args.cmd == "read_id":     jtag.read_id()
    elif args.cmd == "read_all":  jtag.read_all(args.filename)
    elif args.cmd == "read_page": jtag.read_page(args.filename, args.page)
    else: fail("Unsupported cmd: %s" % args.cmd)

    print("Done.")
