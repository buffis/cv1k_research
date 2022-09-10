# Important: This file is WIP. Not really ready for use yet.

import glob
import sys
from gfx_utils import *

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
            outputs[name] = Bitmap(w, h)
        if cmd == "input":
            name = data[1]
            inputs[name] = Bitmap.from_png(name)
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
        outputs[output].write_to_png(output)

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
            outputs[name] = Bitmap.from_png(name)
        if cmd == "input":
            name = data[1]
            inputs[name] = Bitmap.from_png(name)
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
        inputs[input].write_to_png(input)
                    

if __name__ == "__main__":
    infile = open(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "back":
        map_back(infile)
    else:
        remap(infile)
    infile.close()
    