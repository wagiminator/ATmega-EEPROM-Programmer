#!/usr/bin/env python3

# EEPROM Programmer - eepromcmd
#
# Sends a command to the programmer and prints the received data.
# python3 eepromcmd.py <command> [<startAddr> [<endAddr> [<ctrlByte>]]]
#
# Usage examples:
# python3 eepromcmd.py d 0000 7fff - print hex dump of memory addresses 0000-7fff
# python3 eepromcmd.py f 1000 1fff ff - fill memory (1000-1fff) with value ff
#
# pySerial needs to be installed
#
# 2020 by Stefan Wagner

import sys
from eeprom import Programmer


# get and check command line arguments
startAddr = endAddr = ctrlByte = 0
try:
    l = len(sys.argv)
    cmd = sys.argv[1]
    if l > 2:
        startAddr = abs(int(sys.argv[2], 16))
        if l > 3:
            endAddr = abs(int(sys.argv[3], 16))
            if l > 4:
                ctrlByte = abs(int(sys.argv[4], 16))
except:
    sys.stderr.write ('ERROR: Something wrong with the arguments\n')
    sys.exit(1)

if cmd[0] not in ['i', 'v', 'a', 'd', 'f']:
    sys.stderr.write ('ERROR: Invalid command\n')
    sys.exit(1)

if (startAddr > 0x7fff) or (endAddr > 0x7fff) or ctrlByte > (0xff):
    sys.stderr.write ('ERROR: Invalid parameters\n')
    sys.exit(1)


# establish serial connection
print('Connecting to EEPROM Programmer ...')
eeprom = Programmer()
if not eeprom.is_open:
    sys.stderr.write ('ERROR: EEPROM Programmer not found\n')
    sys.exit(1)


# send command
print ('Sending command to EEPROM programmer ...')
eeprom.sendcommand (cmd, startAddr, endAddr, ctrlByte)


# receive data
while (1):
    data = eeprom.getline()
    if data:
        if data == 'Ready':
            break
        print (data)
print ('Mission accomplished')


# close serial connection and exit
eeprom.close()
sys.exit(0)
