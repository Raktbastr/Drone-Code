# These two modules allow us to run a web server.
from contextlib import nullcontext
from flask import Flask, render_template
from flask_socketio import SocketIO
from tfluna import TFLuna
from bmp180 import BMP180
from mpu6050 import mpu6050
from picamera2 import Picamera2
import io
import base64
import random

# App initalization
app = Flask(__name__)
socketio = SocketIO(app)

# Sensor initialization
bmp = BMP180()
mpu = mpu6050(0x68)
tfluna = TFLuna()
tfluna.open()
tfluna.set_samp_rate(10)
picam2 = Picamera2
camera_config = picam2.create_preview_configuration(main={"size": (640,480)})
picam2.configure(camera_config)
picam2.start()

# tfl Class to format the getters like the other sensors.
class tfl:
    @staticmethod
    def get_distance():
        return tfluna.read()[0]
    @staticmethod
    def get_strength():
        return tfluna.read()[1]
    @staticmethod
    def get_temperature():
        return tfluna.read()[2]

# All the sensor data getters, for reference
# bmp.get_temperature()
# bmp.get_pressure()
# bmp.get_altitude()
# mpu.get_accel_data()
# mpu.get_gyro_data()
# tfl.get_distance()
# tfl.get_strength()
# tfl.get_temperature()

# When someone requests the root page from our web server, we return 'index.html'.
@app.route('/')
def index():
    return render_template('index.html')

# This function runs in the background to transmit data to connected clients.
def background_thread():
    while True:
        socketio.sleep(0.5)
        socketio.emit(
            'update_data',
            {
                'randomNumber': random.randint(1, 100), # Keeping this here to make sure the page is being updated
                'bmpTemp': bmp.get_temperature(),
                'bmpPressure': bmp.get_pressure(),
                'bmpAltitude': bmp.get_altitude(),
                'mpuAccel': mpu.get_accel_data(),
                'mpuGyro': mpu.get_gyro_data(),
                'tflDistance': tfl.get_distance(),
                'tflStrength': tfl.get_strength(),
                'tflTemp': tfl.get_temperature(),
            }
        )

# This function runs when someone connects to the server - and all we do is start the background thread to update the data.
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(target=background_thread)

@socketio.on('request_image')
def handle_image_request():
    stream = io.BytesIO()
    picam2.capture_file(stream, format='jpeg')
    stream.seek(0)
    b64_image = base64.b64encode(stream.read()).decode('utf-8')
    socketio.emit('new_image', {'image_data': b64_image})
    print("Image sent")

# This function is called
def main():
    # These specific arguments are required to make sure the webserver is hosted in a consistent spot, so don't change them unless you know what you're doing.
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
