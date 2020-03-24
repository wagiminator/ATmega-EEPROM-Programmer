For ATmega8:
avrdude -c usbtiny -p m8 -U lfuse:w:0xff:m -U hfuse:w:0xd9:m -U flash:w:EEPROM_programmer_m8.hex

For ATmega328p:
avrdude -c usbtiny -p m328p -U lfuse:w:0xff:m -U hfuse:w:0xdb:m -U efuse:w:0xfc:m -U flash:w:EEPROM_programmer_m328p.hex
