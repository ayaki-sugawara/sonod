import paho.mqtt.client as mqtt

class Pub():
  def __init__(self, ip_addr="10.24.69.100", port=1883):
    self.client = mqtt.Client()
    self.client.on_connect = self.on_connect
    self.client.on_disconnect = self.on_disconnect
    self.client.connect(ip_addr, port, 60)
    self.client.loop_start()

  def on_connect(self, client, userdata, flag, rc):#process when we connect to broker
    print("Connected with result code " + str(rc))
    self.client.publish("topic", "message", 0)

  def on_disconnect(self, client, userdata, flag, rc):
    if rc!=0: 
       print("Unexpected disconnection.")

  def publish(self, topic, message):
    self.client.publish(topic, message, 0)

