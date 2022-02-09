import signal
import sys
from parent import Sensor, generateMacAddr

def sig_handler(signum, frame) -> None:
  sys.exit(1)

def errorDetected(sensor):
  with open("state/{}.txt".format(generateMacAddr(sensor)), mode="w") as f:
    f.write("0") 

def main(sensor, mode, interval=3, name=None):
  addr = sensor
  if name == None:
    name = addr
  signal.signal(signal.SIGTERM, sig_handler)
  try:
    sensor = Sensor(generateMacAddr(sensor), name)
    if mode == "init":
      sensor.initialize()
    sensor.main(interval)
  finally:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    errorDetected(addr)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__=="__main__":
  argv = sys.argv
  argv = ["child.py", "48F07B784B6B", "init", 60, "arashi"]
  main(*argv[1:])
