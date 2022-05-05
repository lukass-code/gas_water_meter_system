import paho.mqtt.client as mqtt 
import cv2 
import numpy as np
import mysql.connector as mysql
import cam_class as cam

point_gas = (120, 636)
point_water = (534, 320)
class MQTT_Server:
    def __init__(self, broker_address, mqtt_user, mqtt_passwd, mydb):
        self.control_cam = cam.Control_Cam(mydb)
        self.client = mqtt.Client("MQTT_Server")
        self.client.username_pw_set(mqtt_user, mqtt_passwd)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish

        self.connect_mqtt()
        self.start_mqtt()


    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe("/cam1/sleep")
        self.client.subscribe("/cam1/cam")
        self.client.subscribe("/cam2/sleep")
        self.client.subscribe("/cam2/cam")


  
    def on_message(self, client, userdata, message):
        #msg = str(message.payload.decode("utf-8"))
        print("message received ")
        print("message topic: ", message.topic)

        if message.topic == "/cam1/sleep":
            msg = str(message.payload.decode("utf-8"))
            if msg == "Sleep?":
                print("Cam1 Sleep?")
                self.control_cam.get_new_img_water(client)
 
        elif message.topic == "/cam2/sleep":
            msg = str(message.payload.decode("utf-8"))
            if msg == "Sleep?":
                print("Cam2 Sleep?")
                self.control_cam.get_new_img_gas(client)

        elif message.topic == "/cam1/cam":
            print("Picture Cam1")
            self.control_cam.on_photo_watermeter(message.payload, point_water, client)

        elif message.topic == "/cam2/cam":
            print("Picture Cam2")
            self.control_cam.on_photo_gasmeter(message.payload, point_gas, client)



    def on_publish(self, client,userdata,result):
        print("data published \n")

    def connect_mqtt(self):
        self.client.connect(broker_address)
    
    def disconnect_mqtt(self):
        self.client.disconnect()

    def start_mqtt(self):
        print("MQTT Start")
        self.client.loop_forever()
    

if __name__ == '__main__':
    broker_address=""
    mqtt_user = ""
    mqtt_passwd = ""

    server = ""
    mydb = mysql.connect(
      host= server,
      user="",
      password="",
      database = ""
    )

    client = MQTT_Server(broker_address, mqtt_user, mqtt_passwd, mydb)


