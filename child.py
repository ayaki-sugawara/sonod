import signal
import sys
from parent import Sensor, generateMacAddr
from publish import Pub

def sig_handler(signum, frame) -> None:
  sys.exit(1)

def errorDetected(name, mqtt, place):
  sendData = {
    "sensor": name,
    "pid": 0,
    "place": place
  }
  mqtt.publish("state", jsondumps(sendData))
  #with open("state/{}.txt".format(name), mode="w") as f:
    #f.write("0") 

def main(sensor, plance=None, name=None, mode="init", interval=60):
  mqtt = Pub()
  if place == None:
    print("Please fill place name")
    return 0
  if len(sensor) == 12:
    addr = generateMacAddr(sensor)
  else:
    addr = sensor
  if name == None:
    name = addr
  signal.signal(signal.SIGTERM, sig_handler)
  try:
    sensor = Sensor(addr, name, mqtt, place)
    if mode == "init":
      sensor.initialize()
    sensor.main(interval)
  finally:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    errorDetected(name, mqtt, place)
    try:
      sensor.disconnect()
    except Exception as e:
      pass
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__=="__main__":
  argv = sys.argv
  main(*argv[1:])
