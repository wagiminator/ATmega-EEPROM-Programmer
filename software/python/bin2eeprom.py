#!/usr/bin/env python3

# EEPROM Programmer - bin2eeprom
#
# Reads binary file and writes the data to the EEPROM.
# python3 bin2eeprom.py <start address> <filename>
# Address must be hex value without prefix
#
# Usage example:
# python3 bin2eeprom.py 0000 content.bin
#
# pySerial needs to be installed
#
# 2019 by Stefan Wagner

import sys
import os
from eeprom import Programmer


# functions
def progress(percent=0, width=50):
    left = width * percent // 100
    right = width - left
    sys.stdout.write('\r[' + '#' * left + ' ' * right + '] ' + str(percent) + '%')
    sys.stdout.flush()


# get and check command line arguments
try:
    startAddr = int(sys.argv[1], 16)
    fileName  = sys.argv[2]
except:
    sys.stderr.write ('ERROR: Something wrong with the arguments\n')
    sys.exit(1)

try:
    fileSize  = os.stat(fileName).st_size
except:
    sys.stderr.write ('ERROR: File not found\n')
    sys.exit(1)

if (startAddr < 0) or (startAddr > 0x7fff):
    sys.stderr.write ('ERROR: Address out of range\n')
    sys.exit(1)

if (startAddr + fileSize) > 0x8000:
    sys.stderr.write ('ERROR: Binary file doesn\'t fit into eeprom\n')
    sys.exit(1)


# establish serial connection
print ('Connecting to EEPROM Programmer ...')
eeprom = Programmer()
if not eeprom.is_open:
    sys.stderr.write ('ERROR: EEPROM Programmer not found\n')
    sys.exit(1)


# open binary file
print ('Opening binary file ...')
try:
    f = open(fileName, 'rb')
except:
    sys.stderr.write ('ERROR: Could not open file\n')
    ser.close()
    sys.exit(1)


# writing binary data
print ('Writing data from binary file to EEPROM ...')
eeprom.unlock()

datalength = fileSize
byteswritten = 0
addr1 = startAddr

while (datalength):
    count = (addr1 | 0x3f) - addr1 + 1
    if count > datalength:
        count = datalength
    addr2 = addr1 + count - 1
    eeprom.sendcommand('p', addr1, addr2)
    eeprom.write(f.read(count))
    byteswritten += count
    progress(byteswritten * 100 // fileSize)
    eeprom.readline()
    addr1 += count
    datalength -= count

eeprom.lock()
print ('')
print (str(byteswritten) + ' bytes written')


# verify written data
print ('Verifying written data ...')
f.seek(0)
endAddr = startAddr + byteswritten - 1
count = byteswritten
eeprom.sendcommand ('r', startAddr, endAddr)

while (count):
    data = eeprom.read(1)
    if data:
        if data != f.read(1):
            sys.stderr.write ('ERROR: Data mismatch\n')
            f.close()
            eeprom.close()
            sys.exit(1)
        count -= 1
eeprom.readline()
print ('Mission accomplished')


# close binary file and serial connection, then exit
f.close()
eeprom.close()
sys.exit(0)
