#!/usr/bin/env python3

# EEPROM Programmer - eepromgui
#
# A simple GUI based on tkinter to interface with the EERPOM programmer.
#
# pySerial and tkinter (8.6 or newer) need to be installed
#
# 2020 by Stefan Wagner

import os
from eeprom  import Programmer
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *


class Progressbox(Toplevel):
    def __init__(self, root = None, title = 'Please wait !', 
                activity = 'Doing stuff ...', value = 0):
        Toplevel.__init__(self, root)
        self.__step = IntVar()
        self.__step.set(value)
        self.__act = StringVar()
        self.__act.set(activity)
        self.title(title)
        self.resizable(width=False, height=False)
        self.transient(root)
        self.grab_set()
        Label(self, textvariable = self.__act).pack(padx = 20, pady = 10)
        Progressbar(self, orient = HORIZONTAL, length = 200, 
                variable = self.__step, mode = 'determinate').pack(
                padx = 10, pady = 10)
        self.update_idletasks()

    def setactivity(self, activity):
        self.__act.set(activity)
        self.update_idletasks()

    def setvalue(self, value):
        self.__step.set(value)
        self.update_idletasks()


def showContent():
    eeprom = Programmer()
    if not eeprom.is_open:
        messagebox.showerror('Error', 'EEPROM Programmer not found !')
        return

    contentWindow = Toplevel(mainWindow)
    contentWindow.title('EEPROM memory content')
    contentWindow.minsize(200, 100)
    contentWindow.resizable(width=False, height=True)
    contentWindow.transient(mainWindow)
    contentWindow.grab_set()

    l = Listbox(contentWindow, font = 'TkFixedFont', height = 36, width = 72)
    l.pack(side='left', fill=BOTH)
    s = Scrollbar(contentWindow, orient = VERTICAL, command = l.yview)
    l['yscrollcommand'] = s.set
    s.pack(side='right', fill='y')

    startAddr = 0
    endAddr = eepromType.get()
    eeprom.sendcommand ('r', startAddr, endAddr)
    while (startAddr < endAddr):
        bytesline = '%04x:  ' % startAddr
        asciiline = ' '
        i = 16
        while(i):
            data = eeprom.read(1)
            if data:
                bytesline += '%02x ' % data[0]
                if (data[0] > 31) and data[0] < 127: asciiline += chr(data[0])
                else: asciiline += '.'
                i -= 1
        l.insert('end', bytesline + asciiline)
        startAddr += 16
    eeprom.readline()
    eeprom.close()

    contentWindow.mainloop()
    contentWindow.quit()



def uploadBin():
    eeprom = Programmer()
    if not eeprom.is_open:
        messagebox.showerror('Error', 'EEPROM Programmer not found !')
        return

    maxAddr = eepromType.get()
    startAddr = 0

    fileName = filedialog.askopenfilename(title = "Select binary file for upload",
                filetypes = (("binary files","*.bin"),("all files","*.*")))
    if not fileName:
        return

    try:
        f = open(fileName, 'rb')
    except:
        messagebox.showerror('Error', 'Could not open file !')
        eeprom.close()
        return

    fileSize = os.stat(fileName).st_size
    if (startAddr + fileSize) > (maxAddr + 1):
        messagebox.showerror('Error', 'Binary file doesn\'t fit into EEPROM !')
        f.close()
        eeprom.close()
        return

    progress = Progressbox(mainWindow, 'Please wait !', 'Writing data to EEPROM ...')

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
        progress.setvalue(byteswritten * 100 // fileSize)
        eeprom.readline()
        addr1 += count
        datalength -= count

    eeprom.lock()

    progress.setactivity('Verifying written data ...')
    f.seek(0)
    endAddr = startAddr + byteswritten - 1
    count = byteswritten
    eeprom.sendcommand ('r', startAddr, endAddr)

    while (count):
        data = eeprom.read(1)
        if data:
            if data != f.read(1):
                progress.close()
                messagebox.showerror('Error', 'Verification failed !')
                f.close()
                eeprom.close()
                return
            count -= 1
    eeprom.readline()

    f.close()
    eeprom.close()
    progress.destroy()
    messagebox.showinfo('Mission accomplished', 
                str(byteswritten) + ' bytes successfully written !')


def downloadBin():
    eeprom = Programmer()
    if not eeprom.is_open:
        messagebox.showerror('Error', 'EEPROM Programmer not found !')
        return

    startAddr = 0
    endAddr   = eepromType.get()
    count     = endAddr - startAddr + 1

    fileName = filedialog.asksaveasfilename(title = "Select output file",
                filetypes = (("binary files","*.bin"),("all files","*.*")))
    if not fileName:
        return

    try:
        f = open(fileName, 'wb')
    except:
        messagebox.showerror('Error', 'Could not open file !')
        eeprom.close()
        return

    eeprom.sendcommand ('r', startAddr, endAddr)
    while (count):
        data = eeprom.read(1)
        if data:
            f.write(data)
            count -= 1
    eeprom.readline()
    f.close()
    eeprom.close()
    messagebox.showinfo('Mission accomplished', 'Download completed !')




mainWindow = Tk()
mainWindow.title('EEPROM Programmer')
mainWindow.resizable(width=False, height=False)

eepromType = IntVar()
eepromType.set(0x1fff)

typeFrame = Frame(mainWindow, borderwidth = 2, relief = 'groove')
Label(typeFrame, text = '1. Choose EEPROM type:').pack(pady = 5)
Radiobutton(typeFrame, text = '28C64B ( 8k)', variable=eepromType,
            value = 0x1fff).pack()
Radiobutton(typeFrame, text = '28C256 (32k)', variable=eepromType,
            value = 0x7fff).pack()
typeFrame.pack(padx = 10, pady = 10, ipadx = 5, ipady = 5, fill = 'x')

actionFrame = Frame(mainWindow, borderwidth = 2, relief = 'groove')
Label(actionFrame, text = '2. Take your action:').pack(pady = 5)
Button(actionFrame, text = 'Show EEPROM Content', command = showContent
            ).pack(padx = 10, fill = 'x')
Button(actionFrame, text = 'Binary file to EEPROM', command = uploadBin,
            ).pack(padx = 10, fill = 'x')
Button(actionFrame, text = 'EEPROM to binary file', command = downloadBin,
            ).pack(padx = 10, fill = 'x')
actionFrame.pack(padx =10, ipadx = 5, ipady = 5, fill = 'x')

Button(mainWindow, text = 'Exit', command = mainWindow.quit).pack(pady = 10)

mainWindow.mainloop()
