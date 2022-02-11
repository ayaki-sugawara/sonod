from bluepy.btle import Peripheral
import bluepy.btle as btle
import datetime
import binascii
import struct
import binascii
from publish import Pub
import json
import os
import sys
import signal

def detectError(stError:int):
  error = ["acceleration", "Geo-Magnetic", "Humidity", "UV", "Pressure"]
  response = []
  for i in range(5):
    if(stError%2==1):
      print("===={} sensor ERROR====".format(error[i]))
      response.append(error[i])
    stError = stError >> 1 
  return response

def readRSSI(rssi:int):
  rssi = (rssi ^ 0b11111111) * -1
  print("RSSI is {}".format(rssi))
  return rssi

def detectNACK(AckOrNack:int):
  if AckOrNack == 2:
    print("====Some command was not acceptted correctly====")

class NtfyDelegate(btle.DefaultDelegate):
  def __init__(self, params, name, mqtt, place):
    btle.DefaultDelegate.__init__(self)
    self.idx = -1 #we use this value for checking data was received correctly;
    self.mqtt = mqtt
    self.name = name
    self.place = place

  def handleNotification(self, cHandle, data):
    cal = binascii.b2a_hex(data)
    if int((cal[0:2]), 16) == 0xE0:# receive status notification p.44
      print("receive status notification")
      battery = int((cal[16:18]+ cal[14:16]), 16)
      rssi = int(cal[12:14], 16)
      stError = int(cal[6:8], 16)
      ack = int(cal[20:22], 16)
      rssi = readRSSI(rssi)
      error = detectError(stError) 
      if(len(error)!=0):
        self.publish("error", "{} sensors' error has been detected".format(",".join(error)))
      sendData = {
        "battery": battery, 
        "rssi": rssi,
        "sensor": self.name,
        "place": self.place
      }
      self.mqtt.publish("status", json.dumps(sendData))
      detectNACK(ack)

    if int((cal[0:2]), 16) == 0xf2:#data packet 1 p.42
      # I do not write code for calculating value of geo-magnetic and acceleration because we do not use them;
      # we need this packet information in order to get hour and minute
      print("data packet 1 received")
      hour = int(cal[36:38], 16)
      minute = int(cal[34:36], 16)
      second = int(cal[32:34], 16)
      idx = int(cal[38:40], 16)
      self.idx = idx
      self.hms = [hour, minute, second]

    if int((cal[0:2]), 16) == 0xf3:#data packet 2 p.43
      print("data packet 2 received")
      Pressure = int((cal[6:8] + cal[4:6]), 16) * 860.0/65535 + 250
      Humidity = 1.0 * (int((cal[10:12] + cal[8:10]), 16) - 896 )/64
      Temperature = 1.0*((int((cal[14:16] + cal[12:14]), 16) -2096)/50)
      UV = int((cal[18:20] + cal[16:18]), 16) / (100*0.388)
      AmbientLight = int((cal[22:24] + cal[20:22]), 16) / (0.05*0.928)
      day = int(cal[32:34],16)
      month = int(cal[34:36], 16)
      year = int(cal[36:38], 16) + 2000
      idx = int(cal[38:40], 16)

      if idx != self.idx:
        #this data is discarded
        return 0;  

      data = {
          "pressure": Pressure,
          "humidity": Humidity,
          "temperature": Temperature,
          "uv": UV,
          "ambientlight":AmbientLight
         }
      timestamp = datetime.datetime(year, month, day, *self.hms).strftime('%Y-%m-%dT%H:%M:%S+09:00')
      sendData = {
        "data": data,
        "sensor": self.name,
        "timestamp": timestamp,
        "place": self.place
      }

      self.mqtt.publish("data", json.dumps(sendData))
    return 0

class AlpsSensor(Peripheral):
  def __init__(self, addr):
    Peripheral.__init__(self, addr)  
    self.result = 1

class Sensor():
  def __init__(self, addr, name=None, mqtt=None, place=None):
    self.alps= AlpsSensor(addr)
    self.addr = addr
    if name == None:
      name = addr
    self.alps.setDelegate(NtfyDelegate(btle.DefaultDelegate, name, mqtt, place))
    self.sendCommand(1, [0x01, 0x00])#custom1 enable
    self.sendCommand(2, [0x01, 0x00])#custom2 enable
    self.count = 0 # we can use this for some purpose like fixing time automatically
    self.mqtt = mqtt
    sendDate = {
      "sensor": name,
      "pid": str(os.getpid()),
      "place": place
    }
    self.mqtt.publish("state", json.dumps(sendDate))
    #with open('state/{}.txt'.format(name), mode='w') as f:
      #f.write(str(os.getpid()))
  
  def initialize(self):
    self.controlMeasurement()#stop measuring
    self.sendCommand(3, [0x2F, 0x03, 0x03])#initialize sensor
    print("Initialized Sensor {}".format(self.addr))

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

  def selectSamplingDevices(self, devices:list):
    sensors = ['unused', 'ambient light', 'uv', 'temperature', 'humidity', 'pressure', 'geo-magnetic', 'acceleraiton']
    device_names = []
    selected_devices = 0
    for idx, device in enumerate(devices):
      if(device):
        selected_devices += 1 << (7-idx)
        device_names.append(sensors[idx])
    self.sendCommand(3, [0x01, 0x03, selected_devices])#select environment sensor
    print("{} were selected".format(", ".join(device_names)))
    

  def setSlowMode(self, interval:int):
    high = (interval & 0xff00) >> 8
    low = (interval & 0xff)
    self.sendCommand(3, [0x04, 0x03, 0x00])#set slow mode
    self.sendCommand(3, [0x05, 0x04, low, high])#set interval to "interval"
    print("Set Slow Mode. interval is {}, which is {} {}".format(interval, low, high))

  def setAutoStatus(self):
    self.sendCommand(3, [0x24, 0x03, 0x01])
    print("Auto Status Request is on")

  def controlMeasurement(self, command:str = "stop"):
    control = 0x01 if command == "start" else 0x00
    self.sendCommand(3, [0x20, 0x03, control])
    print("contorlled measurement")
   
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

  def setSensorBeaconMode(self):
    self.sendCommand(3, [0x16, 0x07, 0x01, 0x00, 0x00, 0x00, 0x00])
    self.sendCommand(3, [0x12, 0x06, 0x20, 0x03, 0x00, 0x00])
    print("Set Sensor Beacon mode")

  def disconnect(self):
    self.alps.disconnet()
    print("Device Disconnected")

  def main(self, interval):
    self.setTime()
    self.selectSamplingDevices([0,1,1,1,1,1,0,0])
    self.setSlowMode(interval)
    self.setAutoStatus()
    self.controlMeasurement("start")

    while True:
      self.count += 1
      if self.alps.waitForNotifications(1.0):
        pass
      if self.count == 600: # fixing time every 10 minutes
        self.setTime()
        self.count = 0
      print("waiting...")

def generateMacAddr(addr: str):
  ans = []
  for i in range(6):
    ans.append(addr[i*2:i*2+2])
  return ":".join(ans)


#sensor = "48F07B784B6B"
#sensor = "48F07B784B69"
#sensor = generateMacAddr(sensor)
#sensor = Sensor(sensor)
#sensor.main()
