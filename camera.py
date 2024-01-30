import cv2
import pyrebase
import time

firebaseConfig = {
    "apiKey": "AIzaSyDteaOIQhTOOG_GoVruV69_cU3dzTRbALw",
    "authDomain": "iot-assignment-fd101.firebaseapp.com",
    "databaseURL": "https://iot-assignment-fd101-default-rtdb.firebaseio.com",
    "projectId": "iot-assignment-fd101",
    "storageBucket": "iot-assignment-fd101.appspot.com",
    "messagingSenderId": "19970132302",
    "appId": "1:19970132302:web:01c3bb61a993a9c32e361f"
}


firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
cam = cv2.VideoCapture(0)
local_path = 'C:/Users/TARUC/Downloads/testimage.jpg'
while True:

    # Capture a single image
    ret, image = cam.read()
    # Save the image to a file
    cv2.imwrite(local_path, image)
    # Print a message indicating that the image was captured
    print("Image captured and saved.")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    c_path = f"images/tomato_{timestamp}.jpg"
    storage.child(c_path).put(local_path)
    # Wait for 30 seconds before capturing the next image
    time.sleep(30)
   
# Release the camera
cam.release()
cv2.destroyAllWindows()