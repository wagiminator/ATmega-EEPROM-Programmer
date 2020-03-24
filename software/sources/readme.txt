Python scripts for the EEPROM Programmer
========================================
These scripts can be used to interface with the EEPROM programmer.
The Scripts have been tested on Linux, but they should work with other OS
as well. You need to install Python 3.6+ and pySerial. For eepromgui.py
you need to have tkinter 8.6+ installed.
You may need to make the scripts executable. Windows users have to install
CH330/340 drivers.


eepromgui.py
------------
Simple GUI-based application for up- and downloading binary files. 


eepromcmd.py
------------
Command line skript which sends a command to the programmer and prints the
received data. This can be used instead of a serial monitor.
(Commands must comply with those shown in the EEPROM sketch. Addresses are
 always hex values without prefix.)

Usage:
python3 eepromcmd.py <command> [<startAddr> [<endAddr> [<ctrlByte>]]]

Examples:
python3 eepromcmd.py d 0000 7fff - print hex dump of memory addresses 0000-7fff
python3 eepromcmd.py f 1000 1fff ff - fill memory (1000-1fff) with value ff


eeprom2bin.py
-------------
Command line skript which reads EEPROM memory and writes the binary data
to a .bin file.

Usage:
python3 eeprom2bin.py <start address> <end address> <filename>
(Addresses must be hex values without prefix)

Example:
python3 eeprom2bin.py 0000 03ff output.bin


bin2eeprom.py
-------------
Command line skript which reads binary file and writes the data to the EEPROM.

Usage:
python3 bin2eeprom.py <start address> <filename>
(Address must be hex value without prefix)

Example:
python3 bin2eeprom.py 0000 content.bin


eeprom.py
---------
Module that contains the class Programmer which is used by the other scripts.
Programmer is inheritated from the class Serial of the pySerial module. It
provides the basic functions for communicating with the EEPROM programmer.


finddevice.py
-------------
Module that contains the function getPort() which detects the com port of the
EEPROM programmer. This module is no longer used since the port detection is 
now handled by the Programmer class.

Example:
python finddevice.py
