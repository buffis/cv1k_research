import argparse
import sys
import urjtag
import time

EEPROM_ADDR = 0x10C00001
CMD_ADDR    = 0x10C00002

class EEPROMJtag(object):
    """Low level interface for doing stuff with cv1k EEPROM."""
    def __init__(self):
        self.c = urjtag.chain()

    def setup(self):
        self.c.cable("UsbBlaster")
        self.c.tap_detect()
        self.write_enable()

    def rst_cs4(self):
        """Resets state of SH-3 CS4 between commands. Possibly not needed."""
        self.c.peek(0)

    def chip_enable(self):  self.write(1, 1, 0)
    def chip_disable(self): self.write(0, 1, 0)

    def write(self, ce, clock, data):
        cmd = ce << 2 | clock << 1 | data
        self.c.poke(EEPROM_ADDR, cmd)
        self.rst_cs4()

    def read_bit(self):
        self.write(1, 0, 0)
        data = self.c.peek(EEPROM_ADDR) & 1
        self.rst_cs4()
        self.write(1, 1, data)
        return data

    def read_byte(self):
        data = 0
        for i in range(8):
            data = data << 1
            data = data | self.read_bit()
        return data

    def write_bit(self, bit):
        self.write(1, 0, bit & 1)
        self.write(1, 1, bit & 1)

    def write_bits(self, bits):
        for bit in bits: self.write_bit(bit)

    def write_byte(self, byte):
        for i in reversed(range(8)):
            self.write_bit((byte >> i) & 1)

    def write_enable(self):
        self.chip_enable()
        self.write_bits([0,1,1,0,   0,   1,0,0,1,1   ,0,0,0,0,0,0])
        self.chip_disable()
        # The datasheet specifies to pulse this again, so why not.
        self.chip_enable()
        self.chip_disable()

    def read_eeprom(self, addr):
        self.chip_enable()
        self.write_bits([1,0,1,0,0,0,0])
        self.write_byte(addr)
        self.write_bit(0)
        data = (self.read_byte(), self.read_byte())
        self.chip_disable()
        return data

    def write_eeprom(self, addr, byte_high, byte_low):
        self.chip_enable()
        self.write_bits([0,0,1,0,0,0,0])
        self.write_byte(addr)
        self.write_bit(0)
        self.write_byte(byte_high) # d8-dF
        self.write_byte(byte_low) # d0-d7
        self.chip_disable()

def fail(msg):
    print("ERROR:", msg)
    sys.exit(1)


if __name__ == "__main__":
    print("Starting")
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str)
    p.add_argument('--filename', type=str, default='eeprom.bin')
    p.add_argument('--address', type=int, default=-1)
    p.add_argument('--bytehigh', type=int, default=0)
    p.add_argument('--bytelow', type=int, default=0)
    args = p.parse_args()

    jtag = EEPROMJtag()
    jtag.setup()

    if args.cmd == "print_all":
        for addr in range(256):
            x = jtag.read_eeprom(addr)
            print ("Read:", addr, hex(x[0]), hex(x[1]))
    if args.cmd == "read":
        if args.address == -1 or args.address > 255: fail("Invalid address %d" % args.address)
        x = jtag.read_eeprom(addr)
        print ("Read:", addr, hex(x[0]), hex(x[1]))
    if args.cmd == "write":
        if args.address == -1 or args.address > 255: fail("Invalid address %d" % args.address)
        print ("Writing:", addr, hex(args.bytehigh), hex(args.bytelow))
        jtag.write_eeprom(addr, args.bytehigh, args.bytelow)
    if args.cmd == "read_to_file":
        f = open(args.filename, "wb")
        for addr in range(256):
            x = jtag.read_eeprom(addr)
            print ("Read:", addr, hex(x[0]), hex(x[1]))
            f.write(x[0].to_bytes(1, 'big'))
            f.write(x[1].to_bytes(1, 'big'))
        f.close()
    if args.cmd == "write_from_file":
        f = open(args.filename, "rb")
        for addr in range(256):
            h = int.from_bytes(f.read(1), 'big')
            l = int.from_bytes(f.read(1), 'big')
            jtag.write_eeprom(addr, h, l)
            print ("Wrote:", addr, hex(h), hex(l))
        f.close()

    print("Done.")
