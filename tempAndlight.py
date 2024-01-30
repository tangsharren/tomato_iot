from time import sleep
from grovepi import *
from urllib.request import *
from pyrebase import pyrebase
from datetime import datetime, timedelta
import threading

dhtsensor = 2
relay = 7
led = 5
lightsensor = 15

pinMode(lightsensor, "INPUT")
pinMode(led, "OUTPUT")
pinMode(dhtsensor, "INPUT")
pinMode(relay, "OUTPUT")

config = {
    "apiKey": "AIzaSyDteaOIQhTOOG_GoVruV69_cU3dzTRbALw",
    "authDomain": "iot-assignment-fd101.firebaseapp.com",
    "databaseURL": "https://iot-assignment-fd101-default-rtdb.firebaseio.com",
    "projectId": "iot-assignment-fd101",
    "storageBucket": "iot-assignment-fd101.appspot.com",
    "messagingSenderId": "19970132302",
    "appId": "1:19970132302:web:01c3bb61a993a9c32e361f",
    "measurementId": "G-L2DV6GL4HF"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("pikapika9865@gmail.com", "Pika@636_chu")
db = firebase.database()

exit_flag = False
fan_user_control= False
light_user_control = False
time_space = timedelta(hours=2)

def remoteControl():
    global relay
    global fan_user_control
    global light_user_control
    global control_Time
    global light_control_Time
    global exit_flag
    global user_control
    
    while not exit_flag:
        try:
            time.sleep(0.5)
            light = analogRead(lightsensor)
            lightbrightness = light//4.0
            ledbrightness = 255.0 - lightbrightness
            light_result = db.child("Status").child("Light_Status").get()
            fan_result = db.child("Status").child("Fan_Status").get()
            light_c = db.child("Status").child("Control_Light").get()
            fan_c = db.child("Status").child("ControlFan").get()
            light_value = light_result.val()
            fan_value = fan_result.val()
            light_control = light_c.val()
            fan_control = fan_c.val()
                        
            if light_value == 1:
                if ledbrightness == 0 and light_control == 1:
                    print("User control light on")
                    light_user_control = True
                    light_control_Time = datetime.now()
                    db.child("Status").update({"Control_Light":0})
                analogWrite(led, 254)

            else :
                if ledbrightness > 0 and light_control == 1:
                    print("User control light off")
                    light_user_control = True
                    light_control_Time = datetime.now()
                    db.child("Status").update({"Control_Light":0})
                analogWrite(led, 0)

            if fan_value == 1:
                if digitalRead(relay) == 0 and fan_control == 1:
                    print("User control fan on")
                    fan_user_control = True
                    control_Time = datetime.now()
                    db.child("Status").update({"ControlFan":0})
                digitalWrite(relay, 1)

            else :
                if digitalRead(relay) == 1 and fan_control == 1:
                    print("User control fan off")
                    fan_user_control = True
                    control_Time = datetime.now()
                    db.child("Status").update({"ControlFan":0})
                digitalWrite(relay, 0)
                
        except KeyboardInterrupt:
            digitalWrite(led, 0)
            digitalWrite(relay, 0)
            print("breaK")
            exit_flag = True
            break
            
        except TypeError:
            print("Type Error occurs")

def tempSensor():
    global fan_user_control
    global light_user_control
    global control_Time
    global light_control_Time
    global time_space
    global auto_Time
    global exit_flag
    while not exit_flag:
        try:
            time.sleep(0.5)
            [temp, hum] = dht(dhtsensor, 0)
            t = str(temp)
            h = str(hum)
            if temp >= 0 or hum >= 0:
                print("Temp = ", temp, '\u00b0c', " Hum = ", hum, " %")
                if temp > 30:
                    print(fan_user_control)
                    print(digitalRead(relay))
                    auto_Time = datetime.now()
                    if fan_user_control and auto_Time > control_Time + time_space:
                        print("fan automatic on")
                        digitalWrite(relay,1)
                        db.child("Status").update({"Fan_Status":1})
                        fan_user_control = False
                    elif not fan_user_control:
                        digitalWrite(relay,1)
                        db.child("Status").update({"Fan_Status":1})
                
                elif temp < 26:
                    auto_Time = datetime.now()
                    if fan_user_control == True and auto_Time > control_Time + time_space:
                        print("fan automatic off")
                        digitalWrite(relay,0)
                        db.child("Status").update({"Fan_Status":0})
                        fan_user_control = False
                    elif not fan_user_control:
                        digitalWrite(relay,0)
                        db.child("Status").update({"Fan_Status":0})

                light = analogRead(lightsensor)
                light_brightness = light//4.0
                led_brightness = 255.0 - light_brightness
                
                if (light_brightness) < 125.0:
                    auto_Time = datetime.now()
                    if light_user_control == True and auto_Time > light_control_Time + time_space:
                        print("light automatic on")
                        analogWrite(led, led_brightness)
                        db.child("Status").update({"Light_Status":1})
                        light_user_control = False
                    elif not light_user_control:
                        analogWrite(led, led_brightness)
                        db.child("Status").update({"Light_Status":1})

                else:
                    auto_Time = datetime.now()
                    if light_user_control == True and auto_Time > light_control_Time + time_space:
                        print("light automatic off")
                        analogWrite(led, 0)
                        db.child("Status").update({"Light_Status":0})
                        light_user_control = False

                    elif not light_user_control:
                        analogWrite(led, 0)
                        db.child("Status").update({"Light_Status":0})
                        
                print("Light = ", light_brightness)
                lightBright = str(light_brightness)
                ledBright = str(led_brightness)
                data = {"temperature": t, "humidity": h, "Light" :lightBright, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") }
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.child("Temperature and Light").child(timestamp).set(data,user['idToken'])
            else:
                 print("Sensor Error")
            time.sleep(30)
        except KeyboardInterrupt:
            analogWrite(led, 0)
            digitalWrite(relay,0)
            exit_flag = True
            print("break")
            break

if __name__ == "__main__":
    
    threading.Thread(target=remoteControl).start()
    threading.Thread(target=tempSensor).start()

    try:
        while True:
            time.sleep(0)
           
    except KeyboardInterrupt:
        exit_flag = True
        threading.Thread(target=tempSensor).join()
        threading.Thread(target=remoteControl).join()
        analogWrite(led, 0)
        digitalWrite(relay,0)
        print("breaK")