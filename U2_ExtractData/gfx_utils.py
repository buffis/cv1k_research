import png
import compress

PAGE_LEN  = 2112
BLOCK_LEN = 2112 * 64

def block_addr(block, offset=0):
    return BLOCK_LEN * block + offset

def get_block(offset):
    return offset // BLOCK_LEN

def get_int32(infile):
    return int.from_bytes(infile.read(4), "big")

def flatten(t):
    return [item for sublist in t for item in sublist]

class Bitmap(object):
    def __init__(self, width, height, data=None):
        self.width = width
        self.height = height
        if data:
            self.data = data
        else:
            self.data = [[0] * width * 4 for y in range(height)]

    @classmethod
    def from_png(cls, filename):
        reader = png.Reader(filename).asRGBA()
        (w, h, data) = reader[:3]
        data = [list(y) for y in data]
        bitmap = cls(w, h)
        for y in range(h):
            for x in range(w):
                bitmap.set_pixel(x, y, data[y][x*4:x*4+4])    
        return bitmap
    
    @classmethod
    def from_u2_data(cls, data, compressed=False):
        png_data = []
        width = ((data[12] << 8) | data[13]) + 1
        height = ((data[14] << 8) | data[15]) + 1
        i = 16 # Initial offset

        for h in range(height):
            row = []
            for w in range(width):
                row.extend(Bitmap.parse_RGBA555(data[i:i+2]))
                i += 2
            png_data.append(row)
        return cls(width, height, png_data)

    def set_pixel(self, x, y, data, wrap_width=None):
        if wrap_width and y >= self.height:
                y -= self.height
                x -= wrap_width
        self.data[y][x*4: x*4+4] = data

    def get_pixel(self, x, y, wrap_width=None):
        if wrap_width and y >= self.height:
            y -= self.height
            x -= wrap_width
        return self.data[y][x*4: x*4+4]

    def write_to_png(self):
        f=open(self.name, "wb")
        w = png.Writer(self.width, self.height, greyscale=False, alpha=True)
        w.write(f, self.data)
        f.close()

    @staticmethod
    def make_RGBA555(pixel_data):
        (r,g,b,a) = pixel_data
        # Byte 1
        alpha_bits = 0x80 if a else 0x00
        r_bits = (r//8) << 2
        g_bits1 = (g//8) >> 3
        # Byte 2
        g_bits2 = ((g//8) & 0b111) << 5
        b_bits = b//8

        data = ((alpha_bits | r_bits | g_bits1) << 8) | (g_bits2 | b_bits)
        return data.to_bytes(2, byteorder="big")

    @staticmethod
    def parse_RGBA555(x):
        a = 255 if (x[0] >> 7) else 0
        r = 8 * ((x[0] >> 2) & 0b11111)
        g = 8 * (((x[0] & 0b11) << 3) | (x[1] >> 5))
        b = 8 * (x[1] & 0b11111)
        return (r,g,b,a)

    def write_to_png(self, filename):
        f=open(filename, "wb")
        w = png.Writer(self.width, self.height, greyscale=False, alpha=True)
        w.write(f, self.data)
        f.close()

    def write_to_gfx(self, outname):
        f=open(outname, "wb")
        f.write(b'\x14\xc1@\x00\x00\x00\x00\x00|\xa9\x12\x00') # TODO: What is this?
        f.write((self.width - 1).to_bytes(2, "big"))
        f.write((self.height - 1).to_bytes(2, "big"))
        for y in range(self.height):
            for x in range(self.width):
                f.write(Bitmap.make_RGBA555(self.get_pixel(x,y)))
        f.write(b'\xFF\xFF\xFF\xFF')
        f.close()

def make_bitmap_from_file(filename):
    reader = png.Reader(filename).asRGBA()
    (w, h, data) = reader[:3]
    data = [list(y) for y in data]
    bitmap = Bitmap(filename, w, h)
    for y in range(h):
        for x in range(w):
            bitmap.set_pixel(x, y, data[y][x*4:x*4+4])    
    return bitmap
