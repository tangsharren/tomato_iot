import nest_asyncio
nest_asyncio.apply()
import time
import grovepi
import pyrebase
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from httpcore import ConnectTimeout
from datetime import datetime

async def simulate_moisture_input():
    # Simulate moisture input with random values between 0 and 1023
    return random.randint(0, 90)

async def send_telegram_message(bot, chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
    except ConnectTimeout as e:
        print(f"ConnectTimeout error: {e}. Retrying...")
        await asyncio.sleep(5)  # Add a delay before retrying
        await send_telegram_message(bot, chat_id, message)  # Retry the send_telegram_message function

async def main():

    moisturesensor = 14
    relay = 7
    moisture_threshold = 70
    watering_duration = 3

    grovepi.pinMode(moisturesensor, "INPUT")
    grovepi.pinMode(relay, "OUTPUT")

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

    # Telegram Bot API configuration
    telegram_bot_token = "6036050735:AAGJsi5abZ69ObmAYuW4vHNuEqVzx7kvxJI"
    chat_id = "5748990713"

    bot = Bot(token=telegram_bot_token)

    while True:
        try:
            moistureinput = grovepi.analogRead(moisturesensor)
            # Simulate moisture input for testing purposes
            # moistureinput = await simulate_moisture_input()

            if moistureinput < moisture_threshold:
                print('relay on')
                grovepi.digitalWrite(relay, 1)

                # Start the watering timer
                watering_start_time = time.time()

                while time.time() - watering_start_time < watering_duration:
                    # Continue watering for the specified duration
                    pass

                # Turn off the relay after the watering duration
                grovepi.digitalWrite(relay, 0)
                moistureinput = grovepi.analogRead(moisturesensor)
                print("Done watering: ", moistureinput)

                # Check moisture level after watering
                # Send Telegram notification
                if moistureinput < moisture_threshold:
                    print("Moisture level still low after watering. Sending Telegram notification.")
                    # Format the timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    message = f"Low Moisture Alert!\nThe moisture level is still low ({moistureinput}) even after watering for {watering_duration} seconds. Timestamp: {timestamp}"
                    # Retry sending the Telegram message in case of a timeout
                    try:
                        await send_telegram_message(bot, chat_id, message)
                    except asyncio.CancelledError:
                        print("Task was cancelled. Retrying...")
                        continue

                else:
                    grovepi.digitalWrite(relay, 0)

            print("Current moisture: ", moistureinput)

            # Update moisture sensors data
            # Current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            node_path = "moisture-test"
            moisture_data = {
                    f"{node_path}/{timestamp}": moistureinput,
            }
            db.update(moisture_data)
            print("updated")

            await asyncio.sleep(0.5)  # Add an asynchronous sleep

        except KeyboardInterrupt:
            break
        except IOError as e:
            print("Error: {}".format(e))

if __name__ == "__main__":
    asyncio.run(main())
