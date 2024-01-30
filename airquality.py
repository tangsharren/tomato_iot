import threading
import asyncio
from paho.mqtt.client import *
import re
from datetime import datetime
import pyrebase
from telegram import Bot
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont, Image

# Set up OLED display
serial = i2c(port=1, address=0x3C)
device = sh1106(serial, rotate=2, height=128)
normal_img = Image.open("normal.png").resize((128, 128)).convert('1')
warning_img = Image.open("co2_warning.jpg").resize((128, 128)).convert('1')

# Your Telegram Bot Token
TELEGRAM_BOT_TOKEN = "6036050735:AAGJsi5abZ69ObmAYuW4vHNuEqVzx7kvxJI"
TELEGRAM_CHAT_ID = "5748990713"

# Define normal ranges for gas sensors
normal_ranges = {
    "co2": (2200, 3000),#mq811
    "o2": (2200, 2700),#mq2o2
    "o3": (2200, 3000),#mq131
    "air": (900, 1300),#mq135
}

# Initialize Telegram bot
telegram_bot = Bot(TELEGRAM_BOT_TOKEN)

# Firebase configuration
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
db = firebase.database()

# MQTT configuration
MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "TARUMT/BAIT2123/DEMO"
text = "MQ008=2975,MQ009=921,MQ135=1438,MQ131=2527,MQ811=2527,ME2O2=2454"

message_queue = asyncio.Queue()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code" + str(rc))
    client.subscribe(MQTT_TOPIC)

async def send_telegram_messages():
    while True:
        message = await message_queue.get()
        await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def process_sensor_data(message):
    await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def on_message(client, userdata, msg):
    text = msg.payload.decode("utf-8")
    print(msg.topic + "\n" + text)

    try:
        # Extract sensor values from MQTT message
        co2 = re.search(r'MQ811=(.*?),ME2O2', text).group(1)
        o2 = re.search(r'(?<=ME2O2=)[^,]*', text).group(0)
        o3 = re.search(r'MQ131=(.*?),MQ811', text).group(1)
        air = re.search(r'MQ135=(.*?),MQ131', text).group(1)

        # Update gas sensors data with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        node_path = "gas_sensors"
        gas_data = {
            f"{node_path}/co2/{timestamp}": co2,
            f"{node_path}/o2/{timestamp}": o2,
            f"{node_path}/o3/{timestamp}": o3,
            f"{node_path}/air/{timestamp}": air
        }
        db.update(gas_data)
        print("Updated gas sensors data")
        any_sensor_out_of_range = False
        # Check if values are within normal ranges
        for sensor, (lower, upper) in normal_ranges.items():
            try:
                sensor_value = int(eval(sensor))
                if not (lower <= sensor_value <= upper):
                    any_sensor_out_of_range = True
                    # Create a message indicating the out-of-range value
                    message = f"{sensor.upper()} concentration is out of normal range: {sensor_value}"
               
                    loop.call_soon_threadsafe(message_queue.put_nowait, message)
                    loop.create_task(process_sensor_data(message))
        
            except (ValueError, TypeError):
                print(f"Error converting {sensor} value to integer")
            
        if any_sensor_out_of_range:
            # Display warning image
            device.display(warning_img)
            device.show()
            print("Notified user")
        else:
            # Display normal image
            device.display(normal_img)
            device.show()



    except AttributeError:
        print("Incorrect RE")

# Create an instance of the MQTT client
client = Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)

# Start the MQTT loop in a separate thread
client.loop_start()

# Set up the asyncio event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create the asyncio queue in the same event loop
message_queue = asyncio.Queue()

# Start the asyncio event loop in a separate thread
event_loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
event_loop_thread.start()

# Run the coroutine for sending Telegram messages in the event loop
async def send_telegram_messages():
    while True:
        message = await message_queue.get()
        await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Run the coroutine for sending Telegram messages in the event loop
loop.create_task(send_telegram_messages())

try:
    # Loop indefinitely until a keyboard interrupt (Ctrl+C)
    loop.run_until_complete(main())
except KeyboardInterrupt:
    print("\nProgram terminated by user.")
    client.loop_stop()
    client.disconnect()