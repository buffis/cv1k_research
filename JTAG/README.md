# CV1000 JTAG

This page documents how to connect to the JTAG port of CV1000 PCBs, and how to interact with various onboard devices.

**VERY IMPORTANT NOTE: THIS CAN HARM YOUR PCB IF YOU DON'T KNOW WHAT YOU ARE DOING.**

**I TAKE NO RESPONSIBILITY FOR YOUR HARDWARE. THE INFORMATION HERE SHOULD ONLY BE CONSIDERED INFORMATIONAL ONLY AND MAY CONTAIN MISTAKES. DON'T USE IT UNLESS YOU UNDERSTAND WHAT IT IS DOING AND ARE WILLING TO DOUBLE CHECK EACH STEP.**

**This research is WIP, and have not yet been fully double checked for mistakes**

## Hardware + software needed

- CV1000 PCB
- Altera USB Blaster (or clone)
- Computer running urjtag for SH-3 (see [urjtag_setup.md](urjtag_setup.md) for instructions)

Getting urjtag running with SH-3 takes a bit of extra work so **make sure you read the instructions**.

## CV1000 JTAG Pinout and connections

```
 CV1000 P4
 ________
|        |
| 14  13 |  14: GND  13: CV1K RST
| 12  11 |  12: GND  11: TDI
| 10  9  |  10: GND   9: TMS
| 8   7      8: NC?   7: ASEBRKAK (Dedicated emulator pin)
| 6   5  |   6: GND   5: TDO
| 4   3  |   4: GND   3: TRST [See note on JTAG mode]
| 2   1  |   2: GND   1: TCK
|________|

CV1000 S1
 ____
|     |
|--0--| Normal startup
|     |
|  1  | Startup in ASE mode (see reset hold section)
|_____|
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
- Hookup VCC VTARGET to a stable +3.3V source on the board.
- ASEBRKAK should not be used
- Only one GND pin needs to be connected
- Ignore the pins marked N/A on the Altera USB Blaster
- It's good (but not required) to connect TRST to the USB Blaster,  but that pin needs to be used to get the device into JTAG mode. See below.

## Getting the PCB into reset hold mode for JTAG

- Flip the switch at S1 so that the switch is not between the white lines. This will put the device in ASE mode.
- Hold TRST tied to ground when powering up the PCB to enable "reset hold".
- When starting up now, the CPU will not start executing instructions, and you can JTAG stuff without worrying about the CPU.
- Remove TRST from ground once PCB has started.

Note that this means that you should not be getting any video output. If the pcb starts showing video, you did something wrong.

## Dump U4

```
sudo jtag
jtag> cable UsbBlaster
jtag> detect
jtag> detectflash 0
jtag> readmem 0 0x200000 u4.bin
```

Note: For CV1000-D, use 0x400000 instead of 0x200000.

## Write U4

**Note that this will take aprox 2.5 hours.**

```
sudo jtag
jtag> cable UsbBlaster
jtag> detect
jtag> detectflash 0
jtag> flashmem 0 u4.bin
```

## Dump U2

**Note that this will take a very long time (close to 3 days).**

```
sudo python3 K9F1G08U0M_JTAG.py read_all
```

## Write U2

Currently not supported, since the only way I've been doing it so far feels a bit too hacky. Writing to U2 the same way as reads are done doesn't seem to behave well, without severe hacks. Needs more investigation + work.

## Dump EEPROM

This is pretty quick.

```
sudo python3 RTC9701_JTAG.py read_to_file --filename=eeprom.dump
```

## Write to EEPROM 

This is also pretty quick.

```
sudo python3 RTC9701_JTAG.py write_from_file --filename=eeprom.dump
```

## Special thanks

- rtw: For very helpful discussions on CV1000 hardware. Without him, this project would have taken a lot longer.
- Anyone working on the mame cv1k.cpp driver which has a lot helpful technical info.
