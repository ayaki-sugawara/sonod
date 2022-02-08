from bluepy.btle import Peripheral
import bluepy.btle as btle
import datetime
import binascii
import struct

class NtfyDelegate(btle.DefaultDelegate):
  def __init__(self, params):
    btle.DefaultDelegate.__init__(self)

  def handleNotification(self, cHandle, data):
    return 0

class AlpsSensor(Peripheral):
  def __init__(self, addr):
    Peripheral.__init__(self, addr)  
    self.result = 1

class Sensor():
  def __init__(self, addr):#initialize sensor
    self.alps= AlpsSensor(addr)
    self.alps.setDelegate(NtfyDelegate(btle.DefaultDelegate))
    self.sendCommand(3, [0x20, 0x03, 0x00])#stop measuring
    self.sendCommand(3, [0x2F, 0x03, 0x03])#initialize sensor
    self.sendCommand(1, [0x01, 0x00])
    self.sendCommand(2, [0x01, 0x00])
    print("Initialized Sensor {}".format(addr))

  def setTime(self):
    now = datetime.datetime.now()
    year = int(str(now.year)[2:])
    month = now.month
    day = now.day
    hour = now.hour
    minute = now.minute
    second = now.second
    self.sendCommand(3, [0x30, 0x0A, 0x00, 0x00, second, minute, hour, day, month, year])
    print("datetime has been saved {}".format(now))
   
  def sendCommand(self, custom_num: int, command: list):
    handle = [0x13, 0x16, 0x18]
    pack_format = '<' + 'b' * len(command)    
    self.alps.writeCharacteristic(handle[custom_num-1], struct.pack(pack_format, *command), True)

  def setDeviceName(self, name):
    name_array = []
    for x in name:
      name_array.append(ord(x))
    self.sendCommand(3, [0x15, len(name)+2, *name_array])
    print("Device name has been saved as {}".format(name))
    print([0x15, len(name)+2, *name_array])

  def setSensorBeaconMode(self):
    self.sendCommand(3, [0x16, 0x07, 0x01, 0x00, 0x00, 0x00, 0x00])
    self.sendCommand(3, [0x12, 0x06, 0x20, 0x03, 0x00, 0x00])
    self.alps.disconnect()
    print("Set Sensor Beacon mode")

def generateMacAddr(addr: str):
  ans = []
  for i in range(6):
    ans.append(addr[i*2:i*2+2])
  return ":".join(ans)


sensor = "48F07B784B6B"
sensor = generateMacAddr(sensor)
sensor = Sensor(sensor)
sensor.setTime()
sensor.setDeviceName("ARASHI")
sensor.setSensorBeaconMode()
