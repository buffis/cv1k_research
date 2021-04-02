# CV1000 JTAG

This page documents how to connect to the JTAG port of CV1000 PCBs, and how to interact with various onboard devices.

**VERY IMPORTANT NOTE: THIS CAN HARM YOUR PCB IF YOU DON'T KNOW WHAT YOU ARE DOING.**

I TAKE NO RESPONSIBILITY FOR YOUR HARDWARE. THE INFORMATION HERE SHOULD ONLY BE CONSIDERED INFORMATIONAL ONLY AND MAY CONTAIN MISTAKES. DON'T USE IT UNLESS YOU UNDERSTAND WHAT IT IS DOING AND ARE WILLING TO DOUBLE CHECK EACH STEP.

**This research is WIP, and have not yet been double checked for mistakes**

## Hardware + software needed

- CV1000 PCB
- Altera USB Blaster (or clone)
- Computer running urjtag

## CV1000 JTAG Pinout and connections

```
 CV1000 P4
 ________
|        |
| 14  13 |  14: GND  13: CV1K RST (VCC TARGET)
| 12  11 |  12: GND  11: TDI
| 10  9  |  10: GND   9: TMS
| 8   7      8: NC?   7: ASEBRKAK (Dedicated emulator pin)
| 6   5  |   6: GND   5: TDO
| 4   3  |   4: GND   3: TRST
| 2   1  |   2: GND   1: TCK
|________|
```

```
 Altera USB Blaster
 ________
|        |
| 10  9  |  10: GND          9: TDI
| 8   7  |   8: TRST         7: N/A
| 6   5      6: N/A          5: TMS
| 4   3  |   4: VCC TARGET   3: TDO
| 2   1  |   2: GND          1: TCK
|________|
```

Notes:
- Hookup CV1K RST to VCC VTARGET
- ASEBRKAK should not be used
- Only one GND pin needs to be connected
- Ignore the pins marked N/A on the Altera USB Blaster

## Urjtag setup

While it is possible to compile urjtag with the required dependencies on Windows through Cygwin (I've done so, but it was a pain), I recommend using a Linux machine since it's a lot easier to get working. Instructions below are for a Raspberry Pi 4 running Raspbian.

I had issues with the urjtag package available in Raspbian package manager, so I recommend compiling from source.

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

## Dump U4

```
jtag> cable UsbBlaster
jtag> detect
jtag> readmem 0 0x200000 u4.bin
```

## Dump U2

See u2_dump.py