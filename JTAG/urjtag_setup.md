# Urjtag setup for SH-3

While it is possible to compile urjtag with the required dependencies on Windows through Cygwin (I've done so, but it was a pain), I recommend using a Linux machine since it's a lot easier to get working. Instructions below are for a Raspberry Pi 4 running Raspbian.

I had issues with the urjtag package available in Raspbian package manager, so I recommend compiling from source.

In general, this is just a regular urjtag install, but you have to repoint the hitachi part from ar7300 to sh7729.

1. Download latest urjtag

Available here: https://sourceforge.net/projects/urjtag/

2. Download dependencies

```
sudo apt-get install libusb-1.0-0-dev libftdi1-dev
```

3. Compile

Make sure that ./configure states that libusb, libftdi and python are present.

```
./configure 
make
make install
sudo ldconfig # I had some weird issues until I ran this too
```

4. Setup boundary scan support for the SH-3 device

Open '/usr/local/share/urjtag/hitachi/PARTS' and replace the line
```
0000000000000001        ar7300          AR7300
```
with
```
0000000000000001        sh7729          SH7729
```

**IMPORTANT NOTE: For some reason urjtag needs to run as superuser to interact with USB. There's probably workarounds for this, but the lazy approach is just to run it with sudo.**

## Test connection

NOTE:

Hookup the Altera USB Blaster to the CV1000 board, then connect by doing:

```
pi@raspberrypi:~ $ sudo jtag

UrJTAG 2021.03 #
Copyright (C) 2002, 2003 ETC s.r.o.
Copyright (C) 2007, 2008, 2009 Kolja Waschk and the respective authors

UrJTAG is free software, covered by the GNU General Public License, and you are
welcome to change it and/or distribute copies of it under certain conditions.
There is absolutely no warranty for UrJTAG.

warning: UrJTAG may damage your hardware!
Type "quit" to exit, "help" for help.

jtag> cable UsbBlaster
Connected to libftdi driver.
jtag> detect
IR length: 16
Chain length: 1
Device Id: 00000000000000000001000000001111 (0x0000100F)
  Manufacturer: Hitachi (0x00F)
  Part(0):      SH7729 (0x001)
  Stepping:     V0
  Filename:     /usr/local/share/urjtag/hitachi/sh7729/sh7729
```
