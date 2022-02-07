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
    self.sendCommand(1, [0x01, 0x00])
    self.sendCommand(2, [0x01, 0x00])
    print("Initialized Sensor {}".format(addr))

  def setTime(self):
    now = datetime.now()
   
  def sendCommand(self, custom_num: int, command: list):
    handle = [0x13, 0x16, 0x18]
    pack_format = '<' + 'b' * len(command)    
    self.alps.writeCharacteristic(handle[custom_num-1], struct.pack(pack_format, *command), True)

  def setSensorBeaconMode(self):
    self.sendCommand(3, [0x2F, 0x03, 0x03])
    self.sendCommand(3, [0x16, 0x07, 0x01, 0x00, 0x00, 0x00, 0x00])
    self.sendCommand(3, [0x12, 0x06, 0x20, 0x03, 0x00, 0x00])
    self.alps.disconnect()
    print("Set Sensor Beacon mode")

def generateMacAddr(addr: str):
  ans = []
  for i in range(6):
    ans.append(addr[i*2:i*2+2])
  return ":".join(ans)


test_sensor = "48F07B784B6B"
test_sensor = generateMacAddr(test_sensor)
sensor = Sensor(test_sensor)
sensor.setSensorBeaconMode()
