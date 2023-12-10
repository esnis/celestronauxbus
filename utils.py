
def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val 

def tosigned24(hexnum):
    n = int(hexnum,16)
    n = n & 0xffffff
    return n | (-(n & 0x800000))

def hextoposition(hexnum):
    position = tosigned24(hexnum)/pow(2,24)*360
    return position

def decdeg2dms(dd):
    d = int(dd)
    m = int((abs(dd) - abs(d)) * 60)
    s = round((abs(dd) - abs(d) - m/60) * 3600.00,2)
    return d,m,s

def xprint(*args):
    if __mode__ == 'text':
      print(" ".join(map(str,args)))
    if __mode__ == 'UI':
      q.put(" ".join(map(str,args))) 
      app.event_generate('<<AppendLine>>', when='tail')

def decodecommandvalue(sender,device,command,commandvalue):
    if hex(command) == '0xfe':
        if len(commandvalue)<4:
            commandvalue = '.'.join([format(int(c, 16)) for c in commandvalue])
        else:
            commandvalue = format(int(commandvalue[0], 16)) + '.' + format(int(commandvalue[1], 16))+ '.' + str(int(format(int(commandvalue[2],16), '02x')+format(int(commandvalue[3],16), '02x'),16))
    elif hex(device) == '0x10' or hex(device) == '0x11':
        if hex(command) == '0x1' or hex(command) == '0x2' or hex(command) == '0x3a' or hex(command) == '0x3c':
            commandvaluehex = ''.join([format(int(c, 16), '02x') for c in commandvalue])   
            latitude=twos_comp(int(commandvaluehex,16),24)
            latitude=latitude*360/pow(2,24)
            d,m,s = decdeg2dms(latitude)
            commandvalue = format(d) + '°' + format(m) + '\'' + format(s) + '"'
        elif hex(command) == '0x17' or hex(command) == '0x6' or hex(command) == '0x7':
            if sender == device:
                if hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - ACK'
            else:
                commandvaluehex = ''.join([format(int(c, 16), '02x') for c in commandvalue])   
                latitude=twos_comp(int(commandvaluehex,16),24)
                latitude=latitude*360/pow(2,24)
                d,m,s = decdeg2dms(latitude)
                commandvalue = format(d) + '°' + format(m) + '\'' + format(s) + '"'
        elif hex(command) == '0x5':
            commandvalue = format(''.join([format(int(c, 16), '02x') for c in commandvalue]))
        elif hex(command) == '0x12':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - False'
            elif hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - True'
        elif hex(command) == '0x13' or hex(command) == '0x15':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - Not Done'
            elif hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - Check'
            elif hex(int(commandvalue[0],16)) == '0xff': commandvalue = '255 - Done'
        elif hex(command) == '0x23':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - Disabled'
            elif hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - Enabled'
        elif hex(command) == '0x24' or hex(command) == '0x25' or hex(command) == '0x40' or hex(command) == '0x41':
            commandvalue = format(int(commandvalue[0],16))
        elif hex(command) == '0x3b':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - Disabled'
            elif hex(int(commandvalue[0],16)) == '0xff': commandvalue = '255 - Enabled'
        elif hex(command) == '0x46' or hex(command) == '0x47':
            commandvalue = format(100*int(commandvalue[0],16)/256)
        elif hex(command) == '0xfc' or hex(command) == '0xfd':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - Positive'
            elif hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - Negative'
    elif hex(device) == '0xb0':
        if hex(command) == '0x1' or hex(command) == '0x2':
            commandvaluehex = ''.join([format(int(c, 16), '02x') for c in commandvalue])   
            latitude=twos_comp(int(commandvaluehex,16),24)
            latitude=latitude*360/pow(2,24)
            d,m,s = decdeg2dms(latitude)
            commandvalue = format(d) + '°' + format(m) + '\'' + format(s) + '"'
        elif hex(command) == '0x3':
            commandvalue = format(int(commandvalue[0], 16)) + '/' + format(int(commandvalue[1], 16))
        elif hex(command) == '0x4':
            commandvalue = format(int(''.join([format(int(c, 16), '02x') for c in commandvalue]), 16))
        elif hex(command) == '0x7':
            commandvalue = format(int(commandvalue[0], 16)) + ' - ' + format(int(commandvalue[1], 16))
        elif hex(command) == '0x33':
            commandvalue = format(int(commandvalue[0], 16)) + ':' + format(int(commandvalue[1], 16))+ ':' + format(int(commandvalue[2], 16))
        elif hex(command) == '0x36' or hex(command) == '0x37':
            if hex(int(commandvalue[0],16)) == '0x0': commandvalue = '0 - No'
            elif hex(int(commandvalue[0],16)) == '0x1': commandvalue = '1 - Yes'
    elif hex(device) == '0xb4':
        if hex(command) == '0x3f':
            if len(commandvalue)== 8:
                centerx = ''.join([format(int(c, 16), '02x') for c in reversed(commandvalue[0:4])])
                centery = ''.join([format(int(c, 16), '02x') for c in reversed(commandvalue[4:8])])
                commandvalue = format(int(centerx, 16)) + ' - ' + format(int(centery, 16))
            else:
                commandvalue = format(int(commandvalue[0],16))
    else:
        commandvaluehex = ''.join([format(int(c, 16), '02x') for c in commandvalue])         
        commandvalue = commandvaluehex
    return commandvalue

def decodemsg(msg):
    global mount
    byte=0
    sum=0
    checksumok = 0
    commandvalue = []
    for c in range(0,len(msg),2):
      byte = int(c/2+1)
      value = int(msg[c:c+2],16)
      if (byte>1 and byte <len(msg)/2):
        sum=sum+value
      if (byte == 2):
        length = value
      if (byte == 3):
        sender = value
      if (byte == 4):
        receiver = value   
      if (byte == 5):
        command = value   
      if (byte > 5 and byte < 3+length):
        commandvalue.append(hex(value))
      if (byte == len(msg)/2):
        checksum = value
        sum=65536-sum
        sum=sum&255
        if checksum == sum:
          checksumok = 1
    if checksumok:
      if (sender == scannerid or receiver == scannerid):
        if sender == scannerid:
          device = receiver
        else:
          device = sender
      else:
        if sender not in controllers:
          device = sender
        else:
          device = receiver
      if len(commandvalue)>0:
        if hex(command) == '0xfe':
          commandvalue = decodecommandvalue(sender,device,command,commandvalue)
          if len(commandvalue)>0:
            activedevices.update({hex(sender):commandvalue}) if hex(sender) not in activedevices else activedevices
        else:
          commandvalue = decodecommandvalue(sender,device,command,commandvalue)
          if hex(command) == '0x5' and hex(sender) == '0x10':
            mount = int(commandvalue,16)
      if (device,command) in commands:
          commandtext = commands[(device,command)]
      else:
          commandtext = 'UNKNOWN'
      if sender in devices:
          sendertext = devices[sender]
      else: 
          sendertext = 'UNKNOWN'
      if receiver in devices:
          receivertext = devices[receiver]
      else: 
          receivertext = 'UNKNOWN'
      if verbose:
          dumptext = ' --- ' + str(msg)
      else:
          dumptext = ''
      output = str(format(round(time.time()-starttime,6),'14.6f')) + " - " + "{:<20}".format(sendertext) + " (0x" + str(format(sender,'02x')) + ") " + "-> " + "{:<20}".format(receivertext) + " (0x" + str(format(receiver,'02x')) + ") " + "--- " + "{:<20}".format(commandtext) + " (0x" + str(format(command,'02x')) + ") " + "--- " + str(commandvalue) + dumptext
      xprint (output)
      if filecsvoutput:
          fileoutput = str(format(round(time.time()-starttime,6),'14.6f')) + "," + sendertext + "," + str(hex(sender)) + ","  + receivertext + "," + str(hex(receiver)) + ","  + commandtext + "," + str(hex(command)) + "," + str(commandvalue) + "," + str(msg)
          print(fileoutput,  file=open('auxbuslog.csv', 'a'))
      if emulategps:
        global gpslat,gpslon    
        if str(hex(receiver)) == '0xb0':
          if str(hex(command)) == '0x36':
            transmitmsg('3b',receiver,sender,command,'01')
          if str(hex(command)) == '0xfe':
            transmitmsg('3b',receiver,sender,command,'0b01')
          if str(hex(command)) == '0x33':
            transmitmsg('3b',receiver,sender,command,format(datetime.now(timezone.utc).hour, '02x')+format(datetime.now(timezone.utc).minute, '02x')+format(datetime.now(timezone.utc).second, '02x'))
          if str(hex(command)) == '0x3':
            transmitmsg('3b',receiver,sender,command,format(datetime.now(timezone.utc).month, '02x')+format(datetime.now(timezone.utc).day, '02x'))
          if str(hex(command)) == '0x4':
            transmitmsg('3b',receiver,sender,command,format(datetime.now(timezone.utc).year, '04x'))
          if str(hex(command)) == '0x37':
            transmitmsg('3b',receiver,sender,command,'01')
          if str(hex(command)) == '0x2':
            if gpslon>=0:
                gpslonhex=format(int(gpslon/360*pow(2,24)),'06x')
            else: 
                gpslonhex=format(int((gpslon+360)/360*pow(2,24)),'06x')
            transmitmsg('3b',receiver,sender,command,gpslonhex)
          if str(hex(command)) == '0x1':
            if gpslat>=0:
                gpslathex=format(int(gpslat/360*pow(2,24)),'06x')
            else: 
                gpslathex=format(int((gpslat+360)/360*pow(2,24)),'06x')
            transmitmsg('3b',receiver,sender,command,gpslathex)
    else:
      output = str(hex(sender)+ " -> " + hex(receiver) + " --- " + hex(command) + " --- " + ' '.join(map(str, commandvalue)) + " CRC FAIL!")
      xprint (output)

def decodestarsensestar(msg):
    ssxfov=6.88
    ssyfov=5.16
    msg="".join(reversed([msg[i:i+2] for i in range(0, len(msg), 2)]))
    bx,px,by,py=int(msg[0:2],16)-64,int(msg[2:8],16),int(msg[8:10],16)-64,int(msg[10:16],16)
    dx,mx,sx = decdeg2dms(twos_comp(int(msg[2:8],16),24)*ssxfov/pow(2,24))
    dy,my,sy = decdeg2dms(twos_comp(int(msg[10:16],16),24)*ssyfov/pow(2,24))
    px = format(dx) + '°' + format(mx) + '\'' + format(sx) + '"'
    py = format(dy) + '°' + format(my) + '\'' + format(sy) + '"'
    msg=str(bx) + " - " + "{:<11}".format(px) + " - " + str(by) + " - " + "{:<11}".format(py)
    return msg

def starsensepixel(msg,ssxres,ssyres):
    msg="".join(reversed([msg[i:i+2] for i in range(0, len(msg), 2)]))
    bx,px,by,py=int(msg[0:2],16)-64,int(msg[2:8],16),int(msg[8:10],16)-64,int(msg[10:16],16)
    pixelx = int(ssxres/2+(twos_comp(int(msg[2:8],16),24)*ssxres/pow(2,24)))
    pixely = int(ssyres/2+(twos_comp(int(msg[10:16],16),24)*ssyres/pow(2,24)))
    return pixelx,pixely,bx,by

def decodemsg3c(msg):
    global starsensesave
    starlen=2*8
    pixellist = []
    ssxres=1280
    ssyres=960
    byte=0
    sum=0
    checksumok = 0
    commandvalue = []
    for c in range(2,len(msg),2):
      byte = int(c/2+1)
      value = int(msg[c:c+2],16)
      if (byte>1 and byte <len(msg)/2):
        sum=sum+value
      if (byte == 4):
        lengthH = value
      if (byte == 5):
        lengthL = value
        length = lengthH*256+lengthL 
      if (byte == len(msg)/2):
        checksum = value
        sum=65536-sum
        sum=sum&255
        if checksum == sum:
          checksumok = 1
    if checksumok:
        if verbose:
          dumptext = ' --- ' + str(msg)
        else:
          dumptext = ''
        output = str(format(round(time.time()-starttime,6),'14.6f')) + " - " + "Starsense HC Data - " + str(int(length)/8) + " Stars" + msg[5*2:-2] + dumptext
        xprint (output)       
        data=msg[5*2:-2]
        stars=[data[i:i+starlen] for i in range(0, len(data), starlen)]
        for star in stars:
            if star!="0000000000000000":
                xprint("                 Star ",stars.index(star)+1," - ",decodestarsensestar(star))
                pixellist.append(starsensepixel(star,ssxres,ssyres))
        if starsensesave:
            img = Image.new('L', (ssxres, ssyres))
            imagedata = [0] * ssxres * ssyres
            for pixel in pixellist:
                imagedata[pixel[0]+pixel[1]*ssxres] = 255
                if pixel[2]>1:
                    imagedata[(pixel[0]+1)+pixel[1]*ssxres] = 255
                if pixel[2]>2:
                    imagedata[(pixel[0]-1)+pixel[1]*ssxres] = 255
                if pixel[2]>3:
                    imagedata[(pixel[0]+2)+pixel[1]*ssxres] = 255
                if pixel[3]>1:
                    imagedata[pixel[0]+(pixel[1]+1)*ssxres] = 255
                if pixel[3]>2:
                    imagedata[pixel[0]+(pixel[1]-1)*ssxres] = 255
                if pixel[3]>3:
                    imagedata[pixel[0]+(pixel[1]+2)*ssxres] = 255
            img.putdata(imagedata)
            img.save('starsense-image.png')
        if filecsvoutput:
            fileoutput = str(format(round(time.time()-starttime,6),'14.6f')) + "," + "Starsense Camera" + "," + "0xb4" + ","  + "All" + "," + "0x00" + ","  + "Data" + "," + "0x00" + "," + "[]" + "," + str(msg)
            print(fileoutput,  file=open('auxbuslog.csv', 'a'))
    else:
        xprint ("Starsense HC Data - CRC FAIL!")


def processmsgqueue():
  global msgqueue
  global oof
  if len(msgqueue)>1:
    while len(msgqueue)>1 and msgqueue[0:2] != str(hex(preamble))[2:] and msgqueue[0:2] != str(hex(preamble2))[2:]:
      #oofd = oofd + msgqueue[0:2]
      oof = oof+1
      msgqueue=msgqueue[2:]
  emptyqueue=0
  while len(msgqueue)>=(2*6) and (msgqueue[0:2] == str(hex(preamble))[2:] or msgqueue[0:2] == str(hex(preamble2))[2:]) and emptyqueue==0:
    if msgqueue[0:2] == str(hex(preamble))[2:]:
        length = int(msgqueue[2:4],16)
        if len(msgqueue)>=(2*(length+3)):
          decodemsg(msgqueue[0:2*(length+3)])
          msgqueue=msgqueue[2*(length+3):]
        else:
          emptyqueue=1
    if msgqueue[0:2] == str(hex(preamble2))[2:]:
        msgqueue = msgqueue.replace('3b0202','3b')
        length = int(msgqueue[6:10],16)
        if len(msgqueue)>=(2*(length+6)):
          decodemsg3c(msgqueue[0:2*(length+6)])
          msgqueue=msgqueue[2*(length+6):]
        else:
          emptyqueue=1
        
def encodemsg(sender,receiver,command,value):
  global preamble
  global msgqueue
  global connmode
  commandvalue=[]
  byte=0
  if sender=='':
    if connmode=='wifi' or connmode=='hc' :
        sender = scannerid
    if connmode=='serial':
        sender = scannerid      
  for c in range(0,len(value),2):
      byte = int(c/2+1)
      value2 = int(value[c:c+2],16)
      commandvalue.append(hex(value2))
  length = 3 + int(len(value)/2)
  valuesum = sum(int(i,16) for i in commandvalue)
  summa = length + sender + receiver + command + valuesum
  summa=65536-summa
  summa=summa&255
  output1 = "{:02x}{:02x}{:02x}{:02x}{:02x}".format(preamble,length,sender,receiver,command)
  output2 = value
  output3 = "{:02x}".format(summa)
  output = output1 + output2 + output3
  if (connmode == "hc" or connmode == "wifi") and not emulategps :
    msgqueue = msgqueue + output
    processmsgqueue()
#  decodemsg(output)
  hexoutput = binascii.unhexlify(output)
  return hexoutput

def encodemsg3c():
  global preamble2
  global msgqueue
  data = "5eda6942894f6b4406ea6942ebc25144d9f66942dbe241449d7d6a42b06bca43d95b6942c914a743b94a6c4252ed38433d9d694289d4204400006a4201203744f7c56942f4a8ba4212f16942ce74134359b56942e1adea42ef0e6a4299571b443ee169427734ed43485c6a423c9a3e44922f6a4288b34743477f6a42d77d474201006a4200201644ff7f784300203344b21a6b420000e14343946a4298f75a4443946a426788004416ed68422bc26144d60f6942a8bb274456556942b0486544ffbf764441f94f4444a96942be4666445fdc6a4251892c44bfb869420080b043a123694252c90a445fdc6a42528953440bf86a4254f60144a52e6942fce21e43b6a26942a0b2634256556942ac89844379c56a42f3f5be43a8937644cbd74843cfa4764406059143883a6942ccd7dd42883a694207c5074479c56a42fafa3244449d6a42fafa9a43ea646a423b05bb4362476942760a41439eb86a42b453e041c48e6a420000b34317649a44c91a1a445555784300002943abaa6a4200004b444dd66a422f08124466ad764417f55b43087f6a42ba0264440dc96a420000d3437a9b6a42d9821e440dc96a420000b54387646942da42674487646942dac246440000000000000000"
  data = "13166b4290b09842ddac7644a8dc5044819f6942fc415644a6e56c42cc3138439a998a43cd4c324434246b42e66d0a4311fe6842e00f3744fc920344af170d44e6a374438c5d6b42cb476942270a134300c08a43000073435555784300808f4301006c4200403544d0bfea420d100c445555694200405c44df7e684219a030437aa186433958e442096469423fbd1d44025978437c7ae74323649a44c41b1a4402597843c2422044045d784308ba9e429a85694204432a44a3a4e64356956d44333d9f42519209444dcf8243128c9643386669438e59d34300809143abe6e3425419564339531044e550b143b4ca7342c6eb764400002544520d6f431baf3443abaa554455553a430000000000000000"
  length = "{:08x}".format(int(len(data)/2))
  data = length + data
  valuesum = sum(int(data[c:c+2],16) for c in range(0,len(data),2)) 
  summa = 0 + valuesum
  summa=65536-summa
  summa=summa&255
  output1 = "{:02x}".format(preamble2)
  output2 = data
  output3 = "{:02x}".format(summa)
  output = output1 + output2 + output3
  output = "3c00000320908086434f114844b3707144fb581c44b3e02a4472103644c014fe43b3b4c443372e934458245044232e5143fed1f04377709b445b440e4419355944d59ebb4274dbf6415fb65a443eff2e439b9d5d44a8a57244433f384458fb3944f5085b4444cb3f4306152e4466ca8a440c844d44928939449a141b4451a1e943afa54842ad8f2f440cbc2d4458e98f4492de4f43bd318c44f017e242913f3343eebf5444538883442cbb0b443581594376c34f44ce359944a1816b430e2ff843bf26b743b31c1c43f164c043f96c1644a155b343b5fb2e44d0756c44894b79441b956b44203a3d44e0744d4404d8744467ed5243c1b24444e745bf43e2d17344ee63e243c88ba6438d432f44959be643ab3c3344f1fabc436a03e7430e148344fd245f44e8698344e74c05433ecb93444941b9437f6a8d4469d6c942e6ae6e444f32d943b66d1a44e9600144575a4c449b591f431d41a0432a0cfb436ced664356ddc941a1f25e447fec674343d6d44285ea9e43cfa69044e72536448de978449c424f44071193447b408a42a9000044166f63443188dd43672d48433b020250c24324ccc543d5140c44c75d324308de51444fe63c449809a44327415f4498078143d7e58043057a6b44fb018543c0ed064471fb8a431a6c1e447b8d2c43cc6b6d4463c7bc43b3113144535a6c44b7094b4419432144e2a410441ada25444a76e343a4b46644e74d7144a3de2e44d808974446521e44f0545344d0c39a42c7d05a4453143644389690429188db4398a38d438da25d44b7d4d442f8b4e643ad787a425d1aa7436c072e443c9e4944ecdc7b43d32827447b21e84223633a442efab2439d159443a4e865446d70bb438d073144d8856444456f6a42bcfaa54342a71644a5ca4a438f6f6c43d501d1432ca47544d6f46c440987ca4201c0024446a2c443ebd78a43552a4d44a9983a44f03ee3431c591744d6a2b2437a38c94371938d43054d404476241d446cda3944d1964f445ed2414369f604449c446a449998664340012c443f346a42aa329a428f6e6a42314a3f44978246445aaf3244b302e2430040334454132944d2911b44dc6a7d4344a2314401006a42306629440000000000000000f5"
  if connmode == "hc":
    msgqueue = msgqueue + output
    processmsgqueue()
# decodemsg3c(output)
  hexoutput = binascii.unhexlify(output)
  return hexoutput


def scanauxbus(target):
  xprint ("-----------------------")
  xprint ("Initiating AUXBUS SCAN ")
  xprint ("-----------------------")
  xprint ("     Timestamp - Sender                  Hex   -> Receiver                Hex   --- Command      Hex   --- Value")
  if target=='known':
    for device in devices:
      transmitmsg('3b','',device,0xfe,'')
  if target=='all':
    for device in range(0x01,0xff):
      transmitmsg('3b','',device,0xfe,'')
  time.sleep(0.5)
  identifymount()
  time.sleep(1)
  xprint ("-----------------------")
  xprint (" Finished AUXBUS SCAN  ")
  xprint ("-----------------------")
  printactivedevices()

def identifymount():
  device = 0x10
  if str(hex(device)) in activedevices:
    transmitmsg('3b','',device,0x05,'')
