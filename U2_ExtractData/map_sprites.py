import png
import glob
import sys

#################
#################
################# EXPERIMENTAL WIP
################# DO NOT USE. DOESNT WORK YET
#################
#################

def flatten(t): return [item for sublist in t for item in sublist]

class Bitmap(object):
    def __init__(self, name, sx, sy):
        self.name = name
        self.sx = sx
        self.sy = sy
        self.data = [[0] * sx * 4 for y in range(sy)]
    def set_pixel(self, x, y, data, sx=0):
        if y >= self.sy:
            y -= self.sy
            x -= sx
        self.data[y][x*4: x*4+4] = data
    def get_pixel(self, x, y, sx=9999):
        if y >= self.sy:
            y -= self.sy
            x -= sx
        return self.data[y][x*4: x*4+4]
    def write_to_png(self):
        f=open(self.name, "wb")
        w = png.Writer(self.sx, self.sy, greyscale=False, alpha=True)
        w.write(f, self.data)
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

def remap(infile):
    inputs = {}
    outputs = {}
    for line in infile.readlines():
        line = line.split("#")[0].strip()
        if line.startswith("#"):
            continue
        print ("Parsing", line)
        data = line.split(",")
        cmd = data[0]
        if cmd == "output":
            name = data[1]
            w,h = map(int, data[2:])
            print ("Added output with name", name, "size:",w,"x",h)
            outputs[name] = Bitmap(name, w, h)
        if cmd == "input":
            name = data[1]
            inputs[name] = make_bitmap_from_file(name)
        if cmd == "map":
            infile,outfile = data[1:3]
            sx,sy,sw,sh,tx,ty = map(int, data[3:])
            print ("Mapping ",infile,"to",outfile)
            print ("Src data. x=",sx,"y=",sy,"w=",sw,"h=",sh)
            print ("Dst data. x=",tx,"y=",ty)
            assert infile in inputs
            assert outfile in outputs
            infile = inputs[infile]
            outfile = outputs[outfile]
            for y_off, y in enumerate(range(sy,sy+sh)):
                for x_off, x in enumerate(range(sx,sx+sw)):
                    outfile.set_pixel(tx+x_off,ty+y_off,infile.get_pixel(x,y,sw))
    for output in outputs:
        outputs[output].write_to_png()

def map_back(infile):
    inputs = {}
    outputs = {}

    for line in infile.readlines():
        line = line.split("#")[0].strip()
        if line.startswith("#"):
            continue
        print ("Parsing", line)
        data = line.split(",")
        cmd = data[0]
        if cmd == "output":
            name = data[1]
            w,h = map(int, data[2:])
            print ("Added output with name", name, "size:",w,"x",h)
            outputs[name] = make_bitmap_from_file(name)
        if cmd == "input":
            name = data[1]
            inputs[name] = Bitmap(name.split(".")[0] + "_remap.png", 256, 256) # TODO: Fix size
        if cmd == "map":
            infile,outfile = data[1:3]
            sx,sy,sw,sh,tx,ty = map(int, data[3:])
            print ("ReMapping ",infile,"to",outfile)
            print ("Src data. x=",sx,"y=",sy,"w=",sw,"h=",sh)
            print ("Dst data. x=",tx,"y=",ty)
            assert infile in inputs
            assert outfile in outputs
            infile = inputs[infile]
            outfile = outputs[outfile]
            for y_off, y in enumerate(range(sy,sy+sh)):
                for x_off, x in enumerate(range(sx,sx+sw)):
                    infile.set_pixel(x,y,outfile.get_pixel(tx+x_off,ty+y_off),sw)
    for input in inputs:
        inputs[input].write_to_png()
                    

if __name__ == "__main__":
    infile = open(sys.argv[1])
    map_back(infile)
    infile.close()
    