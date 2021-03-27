// Parallel EEPROM Programmer for 28C256 and 28C64B - for ATmega328P
//
// This version of the software implements:
// - Hardware SPI with 8 Mbps to control address bus via shift registers
// - Hardware UART with 1 Mbps for data transfer to/from PC via USB 2.0
// - Fast page write mode
// - Access via serial monitor
// - Binary data transmission
//
// Usage examples via serial monitor (set baud rate to 1000000):
// - i                  - print "EEPROM Programmer" (for identification)
// - v                  - print firmware version
// - a 0100             - set address bus to 0100 (hex) (for test purposes)
// - d 0000 7fff        - print hex dump of memory addresses 0000-7fff (hex)
// - f 1000 1fff ff     - fill memory (1000-1fff) with value ff (hex)
//
// Usage examples for binary data transmissions:
// (do not use these commands via serial monitor !!!)
// - r 0000 3fff        - read memory addresses 0000-3fff (hex) and send as binary data
// - p 0100 013f        - page write binary data to memory page 0100-013f (hex)
// - l                  - lock EEPROM (enable write protection)
// - u                  - unlock EEPROM (disable write protection)
// 
// Core:          MiniCore (https://github.com/MCUdude/MiniCore)
// Board:         ATmega328
// Clock:         External 16 MHz
// BOD:           BOD 4.3V
// Compiler LTO:  LTO enabled
// Variant:       328P / 328PA
// Bootloader:    No bootloader
// Leave the rest on default settings. Don't forget to "Burn bootloader" !
//
// 2019 by Stefan Wagner 
// Project Files (EasyEDA): https://easyeda.com/wagiminator
// Project Files (Github):  https://github.com/wagiminator
// License: http://creativecommons.org/licenses/by-sa/3.0/


// Libraries
#include <avr/io.h>
#include <util/delay.h>

// Identifiers
#define VERSION         "1.0"
#define IDENT           "EEPROM Programmer"

// Pin and port definitions
#define CONTROL_REG     DDRB
#define CONTROL_PORT    PORTB
#define DATAL_REG       DDRC
#define DATAL_PORT      PORTC
#define DATAL_INPUT     PINC
#define DATAH_REG       DDRD
#define DATAH_PORT      PORTD
#define DATAH_INPUT     PIND
#define LED_REG         DDRC
#define LED_PORT        PORTC
#define CE_REG          DDRC
#define CE_PORT         PORTC

#define DATA            (1<<PB3)              // MOSI (SI)
#define LATCH           (1<<PB2)              // !SS  (RCK)
#define CLOCK           (1<<PB5)              // SCK  (SCK)

#define CHIP_ENABLE     (1<<PC5)              // EEPROM !CE
#define WRITE_ENABLE    (1<<PB0)              // EEPROM !WE
#define OUTPUT_ENABLE   (1<<PB1)              // EEPROM !OE

#define LED_READ        (1<<PC2)              // read indicator LED  
#define LED_WRITE       (1<<PC3)              // write indicator LED

// Macros
#define ReadLEDon       LED_PORT |=  LED_READ
#define ReadLEDoff      LED_PORT &= ~LED_READ
#define WriteLEDon      LED_PORT |=  LED_WRITE
#define WriteLEDoff     LED_PORT &= ~LED_WRITE

#define enableChip      CE_PORT  &= ~CHIP_ENABLE
#define disableChip     CE_PORT  |=  CHIP_ENABLE
#define enableOutput    CONTROL_PORT &= ~OUTPUT_ENABLE
#define disableOutput   CONTROL_PORT |= OUTPUT_ENABLE
#define enableWrite     CONTROL_PORT &= ~WRITE_ENABLE
#define disableWrite    CONTROL_PORT |=  WRITE_ENABLE

#define toggleLatch     {CONTROL_PORT |=  LATCH; CONTROL_PORT &= ~LATCH;}

#define readDataBus     (DATAL_INPUT & 0b00000011) | (DATAH_INPUT & 0b11111100)
#define setDataBusRead  {DATAL_REG &= 0b11111100; DATAH_REG &= 0b00000011;}
#define setDataBusWrite {DATAL_REG |= 0b00000011; DATAH_REG |= 0b11111100;}

#define delay125ns      {asm volatile("nop"); asm volatile("nop");}

// Buffers
uint8_t pageBuffer[64];                       // page buffer
char    cmdBuffer[16];                        // command buffer

// -----------------------------------------------------------------------------
// UART Implementation (1M BAUD)
// -----------------------------------------------------------------------------

#define UART_available()  (UCSR0A & (1<<RXC0))  // check if byte was received
#define UART_read()       UDR0                  // read received byte

// UART init
void UART_init(void) {
  UCSR0B = (1<<RXEN0)  | (1<<TXEN0);          // enable RX and TX
  UCSR0C = (3<<UCSZ00);                       // 8 data bits, no parity, 1 stop bit
}

// UART send data byte
void UART_write(uint8_t data) {
  while(!(UCSR0A & (1<<UDRE0)));              // wait until previous byte is completed
  UDR0 = data;                                // send data byte
}

// UART send string
void UART_print(const char *str) {
  while (*str) UART_write(*str++);            // write characters of string
}

// UART send string with new line
void UART_println(const char *str) {
  UART_print(str);                            // print string
  UART_write('\n');                           // send new line command
}

// Reads command string via UART
void readCommand() {
  for(uint8_t i=0; i< 16; i++) cmdBuffer[i] = 0;  // clear command buffer
  char c; uint8_t idx = 0;                        // initialize variables
  
  // Read serial data until linebreak or buffer is full
  do {
    if(UART_available()) {
      c = UART_read();
      cmdBuffer[idx++] = c;
    }
  } while (c != '\n' && idx < 16);
  cmdBuffer[idx - 1] = 0;                     // change last newline to '\0' termination
}

// -----------------------------------------------------------------------------
// String Converting
// -----------------------------------------------------------------------------

// Convert byte nibble into hex character and print it via UART
void printNibble(uint8_t nibble) {
  uint8_t c;
  if (nibble <= 9)  c = '0' + nibble;
  else              c = 'a' + nibble - 10;
  UART_write(c);
}

// Convert byte into hex characters and print it via UART
void printByte(uint8_t value) {
  printNibble (value >> 4);
  printNibble (value & 0x0f);
}

// Convert word into hex characters and print it via UART
void printWord(uint16_t value) {
  printByte(value >> 8);
  printByte(value);
}

// Convert character representing a hex nibble into 4-bit value
uint8_t hexDigit(char c) {
  if      (c >= '0' && c <= '9') return c - '0';
  else if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  else if (c >= 'A' && c <= 'F') return c - 'A' + 10; 
  else return 0;
}

// Convert string containing a hex byte into 8-bit value
uint8_t hexByte(char* a) {
  return ((hexDigit(a[0]) << 4) + hexDigit(a[1]));
}

// Convert string containing a hex word into 16-bit value
uint16_t hexWord(char* data) {
  return ((hexDigit(data[0]) << 12) +
          (hexDigit(data[1]) <<  8) +
          (hexDigit(data[2]) <<  4) +
          (hexDigit(data[3]))); 
}

// -----------------------------------------------------------------------------
// Low Level Communication with EEPROM
// -----------------------------------------------------------------------------

// Setup SPI for controlling shift registers for the address bus
void SPI_init(void) {
  CONTROL_REG   |=  (DATA | LATCH | CLOCK);   // set control pins as outputs
  CONTROL_PORT  &= ~(DATA | LATCH | CLOCK);   // set control pins low
  SPCR = (1<<SPE) | (1<<MSTR);                // start SPI as Master
  SPSR = (1<<SPI2X);                          // set speed to F_CPU/2
}

// Shift out address by using hardware SPI
void setAddress (uint16_t addr) { 
  SPDR = addr >> 8;                           // high byte of address
  while (!(SPSR & (1<<SPIF)));                // wait for SPI process to finish
  SPDR = addr;                                // low byte of address
  while (!(SPSR & (1<<SPIF)));                // wait for SPI process to finish
  toggleLatch;                                // latch address bus
}

// Write a single byte to the EEPROM at the given address
void setByte (uint16_t addr, uint8_t value) {
  // shift out address with hardware SPI and set data bus at the same time
  SPDR = addr >> 8;
  DATAL_PORT = (DATAL_PORT & 0b11111100) | (value & 0b00000011);
  while (!(SPSR & (1<<SPIF)));
  SPDR = addr;
  DATAH_PORT = (DATAH_PORT & 0b00000011) | (value & 0b11111100);
  while (!(SPSR & (1<<SPIF)));

  toggleLatch;                                // latch address bus

  // write data byte to EEPROM
  enableWrite;                                // set low for write enable
  delay125ns;                                 // wait >100ns
  disableWrite;                               // set high to initiate write cycle
}

// Wait for write cycle to finish using data polling
void waitWriteCycle (uint8_t writtenByte) {
  enableOutput;                               // EEPROM output enable
  delay125ns;                                 // wait for output valid
  while (writtenByte != (readDataBus));       // wait until valid reading
  disableOutput;                              // EEPROM output disable
}

// Read a byte from the EEPROM at the given address
uint8_t readDataByte(uint16_t addr) { 
  enableOutput;                               // EEPROM output enable
  setAddress (addr);                          // set address bus
  delay125ns;                                 // wait for output valid
  uint8_t value = readDataBus;                // read data byte from data bus
  disableOutput;                              // EEPROM output disable 
  return value;                               // return byte
}

// Write a byte to the EEPROM at the given address
void writeDataByte (uint16_t addr, uint8_t value) {
  setDataBusWrite;                            // set data bus pins as output  
  setByte (addr, value);                      // write byte to EEPROM
  setDataBusRead;                             // release data bus (set as input)
  waitWriteCycle (value);                     // wait for write cycle to finish
}

// Write up to 64 bytes; bytes have to be page aligned (28C256 and 26C64B only)
void writePage (uint16_t addr, uint8_t count) {
  if (!count) return;                         // return if no bytes to write
  WriteLEDon;                                 // turn on write LED
  setDataBusWrite;                            // set data bus pins as output
  
  for (uint8_t i=0; i<count; i++) {           // write <count> numbers of bytes 
    setByte (addr++, pageBuffer[i]);          // to EEPROM
  }

  setDataBusRead;                             // release data bus (set as input)
  waitWriteCycle (pageBuffer[count-1]);       // wait for write cycle to finish
  WriteLEDoff;                                // turn off write LED
}

// -----------------------------------------------------------------------------
// High Level EEPROM Functions
// -----------------------------------------------------------------------------

// Write the special six-byte code to turn off software data protection
void disableWriteProtection() {
  setDataBusWrite;                            // set data bus pins as output 
  setByte (0x5555, 0xaa);                     // write code sequence
  setByte (0x2aaa, 0x55);
  setByte (0x5555, 0x80);
  setByte (0x5555, 0xaa);
  setByte (0x2aaa, 0x55);
  setByte (0x5555, 0x20);
  setDataBusRead;                             // release data bus (set as input)
  _delay_ms(10);                              // wait write cycle time
}

// Write the special three-byte code to turn on software data protection
void enableWriteProtection() {
  setDataBusWrite;                            // set data bus pins as output
  setByte (0x5555, 0xaa);                     // write code sequence
  setByte (0x2aaa, 0x55);
  setByte (0x5555, 0xa0);
  setDataBusRead;                             // release data bus (set as input)
  _delay_ms(10);                              // wait write cycle time
}

// Fill specified part of EEPROM memory with the given value
void fillMemory(uint16_t addr, uint16_t dataLength, uint8_t value) {
  uint16_t addr2; uint8_t  count;             // initialize variables
  for (uint8_t i=0; i<64; i++) pageBuffer[i] = value; // fill page buffer with value
  disableWriteProtection();                   // disable write protection
  while (dataLength) {                        // repeat until all bytes written
    addr2 = addr | 0x3f;                      // addr2 = end of current page
    count = addr2 - addr + 1;                 // number of bytes to fill rest of page
    if (count > dataLength) count = dataLength; // make sure not to write too many bytes
    writePage (addr, count);                  // fill page with data
    addr += count;                            // next page address
    dataLength -= count;                      // decrease number of bytes to write
  }
  enableWriteProtection();                    // enable write protection
}

// Read content of EEPROM and print hex dump via UART
void printContents(uint16_t addr, uint16_t count) {
  static char ascii[17];                      // buffer string
  ascii[16] = 0;                              // string terminator
  ReadLEDon;                                  // turn on read LED
  for (uint16_t base = 0; base < count; base += 16) {
    printWord(base); UART_print(":  ");
    for (uint8_t offset = 0; offset <= 15; offset += 1) {
      uint8_t databyte = readDataByte(addr + base + offset);
      if (databyte > 31 && databyte < 127) ascii[offset] = databyte;
      else ascii[offset] = '.';
      printByte(databyte);
      UART_print(" ");
    }
    UART_print(" "); UART_println(ascii);
  }
  ReadLEDoff;                                 // turn off read LED
}

// Read content of EEPROM and send it as binary data via UART
void readBinary(uint16_t addr, uint16_t count) {
  ReadLEDon;
  while (count) {
    UART_write(readDataByte(addr++));
    count--;
  }
  ReadLEDoff;
}

// Write binary data from UART to a memory page
void writePageBinary(uint16_t startAddr, uint8_t count) {
  for (uint8_t i=0; i<count; i++) {
    while (!UART_available());
    pageBuffer[i] = UART_read();
  }
  writePage (startAddr, count);
}

// -----------------------------------------------------------------------------
// Main Function
// -----------------------------------------------------------------------------

int main(void) {
  // Setup EEPROM control pins
  CONTROL_PORT |= (WRITE_ENABLE | OUTPUT_ENABLE);   // set high to disable
  CONTROL_REG  |= (WRITE_ENABLE | OUTPUT_ENABLE);   // set pins as output
  CE_REG  |=  CHIP_ENABLE;                          // set CE pin as output
  CE_PORT &= ~CHIP_ENABLE;                          // set low to enable
  
  // Setup LED pins
  LED_REG   |=  (LED_READ | LED_WRITE);       // set LED pins as output
  LED_PORT  &= ~(LED_READ | LED_WRITE);       // turn off LEDs
  
  // Setup data bus
  DATAL_REG &= 0b11111100;                    // low part of data bus as input
  DATAH_REG &= 0b00000011;                    // high part of data bus as input

  // Setup SPI for controlling shift registers for the address bus
  SPI_init();

  // Setup UART for 1M BAUD
  UART_init();

  // Loop
  while(1) {
    UART_println("Ready");
    readCommand();
    char cmd = cmdBuffer[0];
    uint16_t startAddr = hexWord(cmdBuffer+2);
    uint16_t endAddr   = hexWord(cmdBuffer+7);
    uint8_t  ctrlByte  = hexByte(cmdBuffer+12);
    startAddr &= 0x7fff; endAddr &= 0x7fff;
    if (endAddr < startAddr) endAddr = startAddr;
    uint16_t dataLength = endAddr - startAddr + 1;

    switch(cmd) {
      case 'i':   UART_println(IDENT); break;
      case 'v':   UART_println(VERSION); break;
      case 'a':   setAddress(startAddr); break;
      case 'd':   printContents(startAddr, dataLength); break;
      case 'f':   fillMemory(startAddr, dataLength, ctrlByte); break;
      case 'r':   readBinary(startAddr, dataLength); break;
      case 'p':   writePageBinary(startAddr, dataLength); break;
      case 'l':   enableWriteProtection(); break;
      case 'u':   disableWriteProtection(); break;
      default:    break;    
    }
  }
}
