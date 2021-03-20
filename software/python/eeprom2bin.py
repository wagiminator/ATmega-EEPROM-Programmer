#!/usr/bin/env python3

# EEPROM Programmer - eeprom2bin
#
# Reads EEPROM memory and writes the data to a .bin file.
# python3 eeprom2bin.py <start address> <end address> <filename>
# Addresses must be hex values without prefix
#
# Usage example:
# python3 eeprom2bin.py 0000 03ff output.bin
#
# pySerial needs to be installed
#
# 2020 by Stefan Wagner

import sys
from eeprom import Programmer


# get and check command line arguments
try:
    startAddr = int(sys.argv[1], 16)
    endAddr   = int(sys.argv[2], 16)
    fileName  = sys.argv[3]
except:
    sys.stderr.write('ERROR: Something wrong with the arguments\n')
    sys.exit(1)

if not (0 <= startAddr <= endAddr <= 0x7fff):
    sys.stderr.write('ERROR: Something wrong with the addresses\n')
    sys.exit(1)

count = endAddr - startAddr + 1


# establish serial connection
print('Connecting to EEPROM Programmer ...')
eeprom = Programmer()
if not eeprom.is_open:
    sys.stderr.write ('ERROR: EEPROM Programmer not found\n')
    sys.exit(1)


# open output file
print('Opening file for writing ...')
try:
    f = open(fileName, 'wb')
except:
    sys.stderr.write('ERROR: Could not open file\n')
    ser.close()
    sys.exit(1)


# send command
print('Sending command to EEPROM programmer ...')
eeprom.sendcommand ('r', startAddr, endAddr)


# receive data
print('Transfering data from EEPROM to binary file ...')
while (count):
    data = eeprom.read(1)
    if data:
        f.write(data)
        count -= 1

if eeprom.confirmation():
    print(str(endAddr - startAddr +1) + ' bytes successfully transfered to '
            + fileName)
else:
    sys.stderr.write('ERROR: Data transfer failed\n')
    f.close()
    eeprom.close()
    sys.exit(1)


# close output file and serial connection, then exit
f.close()
eeprom.close()
sys.exit(0)
