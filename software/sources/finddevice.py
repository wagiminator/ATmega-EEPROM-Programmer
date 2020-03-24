#!/usr/bin/env python3

# EEPROM Programmer - finddevice
#
# Finds the EEPROM programmer and returns the com port. The function
# getPort() is used by the other scripts to detect the correct com port.
# python3 finddevice.py
#
# pySerial needs to be installed
#
# 2020 by Stefan Wagner

import serial
import serial.tools.list_ports

def getPort():
    pid = '1a86'
    hid = '7523'
    did = 'EEPROM Programmer'
    port = None

    print('Searching for ' + did + ' ...')
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if pid and hid in p.hwid:
            try:
                ser = serial.Serial(p.device, 1000000, timeout = 1, write_timeout = 1)
            except:
                continue

            try:
                ser.write (b'i\n')
                data = ser.readline().decode().rstrip('\r\n')
            except:
                ser.close()
                continue

            if data == did:
                port = p.device
                print (did + ' found on port ' + port)
                ser.readline()
                ser.write (b'v\n')
                print ('Firmware version: ' + ser.readline().decode().rstrip('\r\n'))
                ser.readline()
                ser.close()
                break
            else:
                ser.close()

    if not port:
        print('ERROR: ' + did + ' not found')

    return port


if __name__ == '__main__':
    getPort()
