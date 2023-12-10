#!/usr/bin/env python

"""Celestron.py: Celestron AUXBUS Scanner"""
__author__ = "Patricio Latini"
__copyright__ = "Copyright 2021, Patricio Latini"
__credits__ = "Patricio Latini"
__license__ = "GPLv3"
__version__ = "0.12.26"
__maintainer__ = "Patricio Latini"
__email__ = "p_latini@hotmail.com"
__status__ = "Production"
__mode__ = "text"

##### TKINTER CODE
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import serial.tools.list_ports
import re
import queue
##### TKINTER CODE

import sys, getopt
import socket
import time
import threading
import binascii
import serial
import keyboard
import argparse
import os
from datetime import datetime,timezone

from constant import *
from utils import *

global triggerscan
triggerscan = ' '
global endthread
endthread = False
global msgqueue
msgqueue = ''
global emulategps
emulategps = False
global mount
mount = ''
global verbose
verbose = False
global starsensesave
starsensesave = False
global filecsvoutput
filecsvoutput = False
global rawfileoutput
rawfileoutput = False
global oof
oof = 0

scannerid = 0x22
preamble = 0x3b
preamble2 = 0x3c



def printactivedevices():
  if mount in mounts:
    mounttext = mounts[mount]
  else: 
    mounttext = 'UNKNOWN' + " (" + str(hex(mount))+ ")" if len(str(mount))>0 else 'NOT DETECTED'  
  xprint ("-----------------------")
  xprint (" Mount :", mounttext )
  xprint ("-----------------------")
  xprint ("-----------------------")
  xprint ("   Detected Devices    ")
  xprint ("-----------------------")
  listactivedevices=list(activedevices)
  for device in activedevices:
    output = str(listactivedevices.index(device))+ ") " + "{:<21}".format(devices[int(device,16)]) + " (0x" + format(int(device,16),'02x') + ") - " + activedevices[device]
    xprint (output)
  
def resettime():
    global starttime
    starttime=time.time()

def printhelpmenu():
  xprint ("-----------------------")
  xprint ("      Commands         ")
  xprint ("-----------------------")
  xprint ("d) show Device list    ")
  xprint ("c) send Command to device")
  xprint ("k) toggle Keepalive send")
  xprint ("s) reScan AUXBUS       ")
  xprint ("a) rescan AUXBUS for All")
  xprint ("v) toggle Verbose output")
  xprint ("f) toggle csv File output")
  xprint ("g) toggle GPS simulator")
  xprint ("ss) toggle Starsense Image Save")
  xprint ("8) Read raw capture from file rawinput.txt")
  xprint ("9) Write raw capture to file rawoutput.txt")
  xprint ("r) Reset Packet Timer  ")
  xprint ("o) Out of frame counter") 
  xprint ("h) print this Help menu")
  xprint ("q) Quit                ")
  xprint ("-----------------------")

def transmitmsg(msgtype,sender,receiver,command,value):
    if msgtype=='3b':
        data = encodemsg(sender,receiver,command,value)
    if msgtype=='3c':
        data = encodemsg3c()
    if rawfileoutput:
        fileoutput = str(round(time.time()-starttime,6)) + " " + str(binascii.hexlify(data),'utf-8')
        print(fileoutput, file=open('rawoutput.txt', 'a'))
    if connmode == 'wifi':
        sock.send(data)
    if connmode == 'serial':
        ser.rtscts = True
        ser.rts=True
        ser.write(data)
        ser.rts=False
        ser.rts=True
        ser.rts=False
        time.sleep(.1)
        ser.read(ser.inWaiting())
        ser.rtscts = False
    if connmode == 'hc':
        ser.write(data)
    time.sleep(0.15)

def keep_alive(interval):
    global endthread
    while not endthread:     
        if keepalive:
            transmitmsg('3b','',0x10,0xfe,'')
        time.sleep(interval)
    xprint ("Finished Keep Alive")

def receivedata():
  global msgqueue
  global endthread
  global rawfileoutput
  data=''
  while not endthread:
      time.sleep(.05)
      if connmode=='wifi':
        data = sock.recv(BUFFER_SIZE)
      if connmode=='serial' or connmode=='hc':
        if (ser.inWaiting()>0):
            data = ser.read(ser.inWaiting())
      if len(data)>0:
          stringdata = binascii.hexlify(data)
          msgqueue = msgqueue + str(stringdata,'utf-8')
          if rawfileoutput:
              fileoutput = str(round(time.time()-starttime,6)) + " " + str(stringdata,'utf-8')
              print(fileoutput,  file=open('rawoutput.txt', 'a'))
          processmsgqueue()
          data=''
  xprint ("Finished Receive Data")

def sendingdata(interval):
  global triggerscan
  lasttx = 0
  while not endthread:
      time.sleep(.05)
      if triggerscan == 'known' or triggerscan == 'all':
          scanauxbus (triggerscan)
          triggerscan = ''
          lasttx = time.time()
      if keepalive:
          if time.time()-lasttx > interval:
             transmitmsg('3b','',0x10,0xfe,'')
             lasttx = time.time()

def fileplayback(filename):
    global msgqueue
    resettime()
    f = open(filename, "r")
    f.seek(0)
    file =''
    linenum=0
    for line in f.read().splitlines():
      linenum=linenum+1
      line2=line.split()
      if len(line2) == 2: 
         if linenum != 1:
            time.sleep(float(line2[0])-lasttime)
         lasttime = float(line2[0])
         data = line2[1]
      else:
         data = line2[0]
      msgqueue = msgqueue + data
      processmsgqueue()
    f.close()
    xprint ("Finished File Processing")

def initializeconn(connmodearg,port):
    global connmode
    global keepalive
    connmode = connmodearg
    if connmode=='wifi':
        keepalive=True
        SERVER_IP = port
        global sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
    if connmode=='serial' or connmode=='hc':
        keepalive=False
        COM_PORT = port
        global ser
        ser = serial.Serial()
        ser.port = COM_PORT
        if connmode=='serial':
            ser.baudrate = 19200
        if connmode=='hc':
            ser.baudrate = 9600
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.timeout = 0
        ser.xonxoff = False
        ser.open()
        if ser.isOpen():
            ser.flushInput()
            ser.flushOutput()
        if connmode=='hc':
            data = b'\x56'
            ser.write(data)
            time.sleep(.5)
            #Should return 0x05 0x1f 0x23
            ser.read(ser.inWaiting())
            data = b'\x8a'
            ser.write(data)
            time.sleep(.5)
            #Should return 0xf8
            ser.read(ser.inWaiting())
            #print(data)
            ser.close
            ser.baudrate = 115200
            ser.open
            time.sleep(1)
            data = b'\x0a\x00\x02\x08\x00\x4b\x00\x00\xd0\xc0'
            ser.write(data)
            time.sleep(.5)
            #Should return 0x05 0x00 0x06 0x38 0xc0
            data = ser.read(ser.inWaiting())

def appstartup():
  global starttime
  global triggerscan
  xprint ("-------------------------------")
  xprint (" AUXBUS SCANNER VERSION",__version__)
  xprint ("-------------------------------") 
  starttime=time.time()
  launchthreads()
  xprint ("-----------------------")
  xprint ("Starting AUXBUS Monitor")
  xprint ("-----------------------")
  triggerscan='known'

def closeconn():
  xprint ("-----------------------")
  xprint ("      Closing          ")
  xprint ("-----------------------")
  if connmode=='wifi': 
    sock.close()
  if connmode=='serial' or connmode=='hc':
    ser.close()

def launchthreads():
    global t0,t1,t2
    
    t0 = threading.Thread(target=receivedata)
    t0.daemon = True
    t0.start()

    t2 = threading.Thread(target=sendingdata, args = (KEEP_ALIVE_INTERVAL,))
    t2.daemon = True
    t2.start()
    
def mainloop():
  global emulategps
  global keepalive
  global gpslat,gpslon
  global activedevices
  global mount
  global starttime
  global endthread
  global verbose
  global filecsvoutput
  global rawfileoutput
  global oof
  global triggerscan
  global starsensesave

  printhelpmenu()
  
  while True:
    inputkey = input("Enter Command:")
    if inputkey == "d":
        printactivedevices()

    if inputkey == "c":
        printactivedevices()
        time.sleep(0.2)
        print ("-----------------------")
        print ("Choose device")
        key1 = input("Enter Device:")
        listactivedevices=list(activedevices)
        filtercommands=[(k[1], v) for k, v in commands.items() if k[0]==int(listactivedevices[int(key1)],16)]
        for command in filtercommands:
            output = chr(97+filtercommands.index(command)) + ") " + str(hex(command[0])) + " (" + str(command[1]) + ") "
            print (output)
        time.sleep(0.2)
        print ("-----------------------")
        print ("Choose command")
        key2 = input("Enter Command:")
        transmitmsg('3b','',int(listactivedevices[int(key1)],16),filtercommands[ord(key2)-97][0],'')

    if inputkey == "k":
        print ("-----------------------")
        print ("   Toggle Keepalive    ")
        print ("-----------------------")
        if keepalive:
            keepalive=False
            print ("   Keepalive Disabled    ")
        else:
            keepalive=True
            print ("   Keepalive Enabled    ")
    if inputkey == "g":
        print ("-----------------------")
        print (" Toggle GPS Emulation  ")
        print ("-----------------------")
        if emulategps:
            emulategps=False
            print ("  GPS Emulation Disabled    ")
        else:
            activedevices.update({hex(176):'11.1'}) if hex(176) not in activedevices else activedevices
            gpslat=float(input("Enter GPS Latitude in Decimal Format: "))
            gpslon=float(input("Enter GPS Longitude in Decimal Format: "))
            emulategps=True
            print ("  GPS Emulation Enabled    ")
    if inputkey == "s":
        activedevices = {}
        mount = ''
        triggerscan = 'known'
    if inputkey == "a":
        activedevices = {}
        mount = ''
        triggerscan = 'all'
    if inputkey == "i":
        identifymount()
    if inputkey == "v":
        verbose = not verbose
    if inputkey == "f":
        filecsvoutput = not filecsvoutput
        if filecsvoutput:
            fileoutput = 'timestamp,'+'sender,'+'sender_id,'+'receiver,'+'receiver_id,'+'command,'+'command_id,'+'command_data,'+'raw_packet'
            print(fileoutput, file=open('auxbuslog.csv','w'))
    if inputkey == "ss":
        starsensesave = not starsensesave
    if inputkey == "r":
        resettime()
    if inputkey == "h":
        printhelpmenu()
    if inputkey == "o":
        print("Out of Frame bytes : ", oof)
    if inputkey == "3":
        transmitmsg('3c','','','','')
    if inputkey == "8":
        if os.path.isfile("rawinput.txt"):
          fileplayback("rawinput.txt")
        else:
          print ("rawinput.txt is not present")
    if inputkey == "9":
        rawfileoutput = not rawfileoutput
        if rawfileoutput:
          open('rawoutput.txt','w')
    if inputkey == "q":
        endthread = True
        transmitmsg('3b','',0x10,0xfe,'')
        t0.join()
        t2.join()
        closeconn()
        break
    time.sleep(.1)

#### TKINTER
def validate(P):
    test = re.compile('(^\d{0,3}$|^\d{1,3}\.\d{0,3}$|^\d{1,3}\.\d{1,3}\.\d{0,3}$|^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{0,3}$)')
    if test.match(P):
        return True
    else:
        return False

def serial_ports():
    ports = serial.tools.list_ports.comports()
    portlist = []
    for port in sorted(ports):
        portlist.append(port.device)
    return portlist

def connect():
    global connectbutton_text
    if connectbutton_text.get() == "Connect":
        if radioValue.get() != ' ':
            connmode = radioValue.get()
            if (radioValue.get() == 'wifi'):
                port = ipadd.get()
            else:
                port = comboExample.get().split(' ', 1)[0]
        else:
            return
    ##messagebox.showinfo(connmode,port)
        initializeconn(connmode, port)
        appstartup()
        connectbutton_text.set("Disconnect")
    else:
        closeconn()
        connectbutton_text.set("Connect")
    
def appendLine(event): 
    line = q.get_nowait()
    text_area.insert(tk.END, str(line)+"\n")
    text_area.see(tk.END)

def triggerbusscan():
    global triggerscan 
    triggerscan = 'known'

def updateCBvar():
    global keepalive
    global verbose
    global filecsvoutput
    global rawfileoutput
    global emulategps
    keepalive = CBkeepalive.get()
    verbose = CBverbose.get()
    filecsvoutput = CBfilecsvoutput.get()
    rawfileoutput = CBrawfileoutput.get()
    emulategps = CBemulategps.get()


def tkinterinit():
    global keepalive
    global verbose
    global filecsvoutput
    global rawfileoutput
    global emulategps
    global q
    global app
    global radioValue,connectbutton_text,comboExample,ipadd,text_area
    global CBkeepalive,CBverbose,CBfilecsvoutput,CBrawfileoutput,CBemulategps

    q = queue.Queue()
    app = tk.Tk() 
    app.geometry('1024x768')
    app_title = tk.StringVar()
    app_title.set("Celestron AUXBUS Scanner " + __version__)
    app.title(app_title.get())
    app.bind('<<AppendLine>>', appendLine)

    radioValue = tk.StringVar() 
    radioValue.set(' ')
    radioOne = tk.Radiobutton(app, text='Serial', variable=radioValue, value="serial") 
    radioTwo = tk.Radiobutton(app, text='Hand Controller', variable=radioValue, value="hc") 
    radioThree = tk.Radiobutton(app, text='WiFi', variable=radioValue, value="wifi")
    connectbutton_text = tk.StringVar()
    connectbutton_text.set("Connect")
    connectbutton = tk.Button(app, textvariable=connectbutton_text, command=connect)
    scanbutton = tk.Button(app, text='Rescan AUXBUS', command=triggerbusscan)
    devicebutton = tk.Button(app, text='Device List', command=printactivedevices)
    comboExample = ttk.Combobox(app, values=serial_ports())
    comboExample.current(0)
    varip = tk.StringVar()
    varip.set('1.2.3.4')
    vcmd = app.register(validate)
    ipadd = tk.Entry(app, textvariable = varip, width = 23, validate = 'key', validatecommand = (vcmd, '%P'))
    text_area = scrolledtext.ScrolledText(app, wrap = tk.WORD, width = 120, height = 40)
    CBkeepalive = tk.BooleanVar()
    CBverbose = tk.BooleanVar()
    CBfilecsvoutput = tk.BooleanVar()
    CBrawfileoutput = tk.BooleanVar()
    CBemulategps = tk.BooleanVar()
    checkButton1 = tk.Checkbutton(app, text='Send Keepalives',variable=CBkeepalive, onvalue=True, offvalue=False,command=updateCBvar)
    checkButton2 = tk.Checkbutton(app, text='Verbose Output',variable=CBverbose, onvalue=True, offvalue=False,command=updateCBvar)
    checkButton3 = tk.Checkbutton(app, text='CSV Output',variable=CBfilecsvoutput, onvalue=True, offvalue=False,command=updateCBvar)
    checkButton4 = tk.Checkbutton(app, text='Write rawoutput',variable=CBrawfileoutput, onvalue=True, offvalue=False,command=updateCBvar)
    checkButton5 = tk.Checkbutton(app, text='GPS Emulator',variable=CBemulategps, onvalue=True, offvalue=False,command=updateCBvar)
    radioOne.grid(column=0, row=0)
    radioTwo.grid(column=1, row=0)
    radioThree.grid(column=2, row=0)
    scanbutton.grid(column=3,row=0,rowspan=1)
    devicebutton.grid(column=3,row=1,rowspan=1)
    connectbutton.grid(column=4,row=0,rowspan=2)
    comboExample.grid(column=0, row=1, columnspan=2)
    ipadd.grid(row = 1, column = 2, padx = 5, pady = 5)
    checkButton1.grid(column=0, row=2)
    checkButton2.grid(column=1, row=2)
    checkButton3.grid(column=2, row=2)
    checkButton4.grid(column=3, row=2)
    checkButton5.grid(column=4, row=2)
    text_area.grid(row = 3, column = 0, pady = 10, padx = 10, columnspan = 5)
    app.mainloop()

##### TKNTER

def main():
  if __mode__ == 'text': 
    parser = argparse.ArgumentParser()
    parser.add_argument('connmode', help='connection mode (wifi / serial / hc)')
    parser.add_argument('port', help='connection port (ip address / COM Port')
    args = parser.parse_args()
    initializeconn(args.connmode, args.port)
    appstartup()
    mainloop()
  if __mode__ == 'UI':   
    tkinterinit()

if __name__ == '__main__':
    main()
