#!/usr/bin/env python3

# EEPROM Programmer - Module eeprom
#
# Module that contains the class Programmer which is used by the other scripts.
# Programmer is inheritated from the class Serial of the pySerial module. It
# provides the basic functions for communicating with the EEPROM programmer.
#
# pySerial needs to be installed
#
# 2020 by Stefan Wagner

from serial import Serial
from serial.tools.list_ports import comports

class Programmer(Serial):
    def __init__(self):
        super().__init__(baudrate = 1000000, timeout = 1, write_timeout = 1)
        self.identify()

    def identify(self):
        pid = '1a86'
        hid = '7523'
        did = 'EEPROM Programmer'
        for p in comports():
            if pid and hid in p.hwid:
                self.port = p.device

                try:
                    self.open()
                except:
                    continue

                try:
                    self.sendcommand ('i')
                    data = self.getline()
                except:
                    self.close()
                    continue

                if data == did:
                    self.readline()
                    break
                else:
                    self.close()


    def sendcommand(self, cmd, startAddr=-1, endAddr=-1, ctrlByte=-1):
        if startAddr >= 0:
            cmd += ' %04x' % startAddr
            if endAddr >= 0:
                cmd += ' %04x' % endAddr
                if ctrlByte >= 0:
                    cmd += ' %02x' % ctrlByte
        self.write((cmd + '\n').encode())


    def getline(self):
        return self.readline().decode().rstrip('\r\n')


    def confirmation(self):
        return (self.getline() == 'Ready')


    def getversion(self):
        self.sendcommand ('v')
        version = self.getline()
        self.readline()
        return version


    def unlock(self):
        self.sendcommand('u')
        return self.confirmation()


    def lock(self):
        self.sendcommand('l')
        return self.confirmation()


if __name__ == '__main__':
    eeprom = Programmer()
    if not eeprom.is_open:
        print('ERROR: EEPROM Programmer not found')
        exit(1)

    print('EEPROM Programmer found on ' + eeprom.port)
    print('Firmware version: ' + eeprom.getversion())
