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

    def block_erase(self, page):
        """DONT USE THIS UNLESS YOU ARE BRAVE."""
        print("Erasing page", page)
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x60) # Erase command cycle 1
        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        self.c.poke(CMD_ADDR, 0xD0) # Erase command cycle 2
        self.c.flush()
        time.sleep(0.003) # tBERS
        self.cs(0)
        return self.read_status()

    def write_page(self, page, data, offset=0):
        """DONT USE THIS UNLESS YOU ARE BRAVE."""
        print("Writing page", page)
        self.cs(1)
        self.c.poke(CMD_ADDR, 0x80) # Write command cycle 1
        self.c.poke(ADDR_ADDR, offset & 0xFF)
        self.c.poke(ADDR_ADDR, (offset>>8) & 0xFF)
        self.c.poke(ADDR_ADDR, page & 0xFF)
        self.c.poke(ADDR_ADDR, (page >> 8) & 0xFF)
        self.c.flush()
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

    def write_page(self, infile, page):
        """DONT USE THIS UNLESS YOU ARE BRAVE."""
        # Everything about this is a little bit sketchy.
        # Need to split up the write in four writes, since JTAG is so slow?
        # There's probably a better way to do it, but this is the easiest
        # one I've found so far.
        for i in range(4):
            data = infile.read(512)
            status = self.jtag.write_page(page, data, i*512)
            if status & 1:
                fail("error writing page:", page)
            # This is a very big hack.
            # When doing several writes, the NAND starts returning an error code
            # indicating it's been write protected after a while. The easiest way
            # to get around this seems to be to reset the jtag stage by calling detect.
            # If someone comes up with a better way to do it, let me know.
            self.jtag.detect()

    def write_all(self, filename, block_start=0, block_end=1024):
        """DONT USE THIS UNLESS YOU ARE BRAVE."""
        infile = open(filename, "rb")
        for block in range(block_start, block_end):
            # Erases are done at block level, so this will erase the next 64 pages. 
            print("Erasing block:", block)
            self.jtag.block_erase(block*64)
            time.sleep(0.00001)

            print("Writing block:", block)
            for block_page in range(64):
                page = block * 64 + block_page
                print("Writing page:", page)
                write_page(infile, page)

def fail(msg):
    print("ERROR:", msg)
    sys.exit(1)

def show_scary_warning(cmd_text):
    print("""WARNING: Writing data to U2 will take aprox 60 hours and is likely to
cause damage to your PCB unless you know what you're doing.

Command: %s

Do you still want to proceed? (yes/no)""" % cmd_text)
    i = input()
    if (i != "yes"):
        fail("User abort")

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
    elif args.cmd == "write_all":
        show_scary_warning("write_all")
        jtag.write_all(args.filename)
    elif args.cmd == "write_block":
        show_scary_warning("write block: %d" % args.block)
        jtag.write_all(args.filename, args.block, args.block+1)
    else: fail("Unsupported cmd: %s" % args.cmd)

    print("Done.")
