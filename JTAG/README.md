# CV1000 JTAG

This page documents how to connect to the JTAG port of CV1000 PCBs, and how to interact with various onboard devices.

**VERY IMPORTANT NOTE: THIS CAN HARM YOUR PCB IF YOU DON'T KNOW WHAT YOU ARE DOING.**

I TAKE NO RESPONSIBILITY FOR YOUR HARDWARE. THE INFORMATION HERE SHOULD ONLY BE CONSIDERED INFORMATIONAL ONLY AND MAY CONTAIN MISTAKES. DON'T USE IT UNLESS YOU UNDERSTAND WHAT IT IS DOING AND ARE WILLING TO DOUBLE CHECK EACH STEP.

**This research is WIP, and have not yet been double checked for mistakes**

## Hardware + software needed

- CV1000 PCB
- Altera USB Blaster (or clone)
- Computer running urjtag for SH-3 (see [urjtag_setup.md](urjtag_setup.md) for instructions)

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

## Dump U4

Start urjtag then:

```
jtag> cable UsbBlaster
jtag> detect
jtag> readmem 0 0x200000 u4.bin
```

## Dump U2

```
sudo python3 K9F1G08U0M_JTAG.py read_all
```