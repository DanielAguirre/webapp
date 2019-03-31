"""
This script runs the flask_controller application using a development server.
"""

try:
    import cStringIO as io
except ImportError:
    import io

import time
import base64
import os
from flask import Flask, g, render_template
from flask_socketio import SocketIO, emit
from inputs.GPSserial import GPS


on_raspi = False

if on_raspi:
    from outputs.biMotor_bool import biMotor # using High Amperage driver
    # from outputs.biMotor import biMotor # using a L298 or similar driver
    from outputs.BiPed import drivetrain 
    # from inputs.LSM9DS1 import LSM9DS1 # for 9oF (LSM9DS1)
    from inputs.mpu6050 import mpu6050 # for 6oF (GY-521)
    import picamera
    camera = picamera.PiCamera()
    camera.resolution = (256, 144)
    camera.start_preview(fullscreen=False, window=(100, 20, 650, 480))
    #sleep(1)
    #camera.stop_preview()
    d = drivetrain(17, 27, 22, 23)
    IMUsensor = mpu6050(0x68)
else:
    import cv2
    camera = cv2.VideoCapture(0)


gps = GPS(on_raspi)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, logger=True, engineio_logger=True, async_mode='eventlet')

@socketio.on('connect')
def handle_connect():
    print('websocket Client connected!')

@socketio.on('disconnect')
def handle_disconnect():
    print('websocket Client disconnected')

@socketio.on('webcam')
def handle_webcam_request():
    if on_raspi:
        sio = io.BytesIO()
        camera.capture(sio, "jpeg", use_video_port=True)
        buffer = sio.getvalue()
    else:
        _, frame = camera.read()
        _, buffer = cv2.imencode('.jpg', frame)

    b64 = base64.b64encode(buffer)
    print(len(b64))
    emit('webcam-response', base64.b64encode(buffer))

@socketio.on('gps')
def handle_gps_request():
    print('gps data sent')
    NESW = (0,0)
    if (on_raspi):
        gps.getData()
        NESW = (gps.NS, gps.EW)
    else:
        NESW = (37.967135, -122.071210)
    emit('gps-response', [NESW[0], NESW[1]])

@socketio.on('sensorDoF')
def handle_DoF_request():
    if (on_raspi):
        accel = IMUsensor.get_accel_data()
        gyro = IMUsensor.get_gyro_data()
        mag = IMUsensor.get_mag_data()
    else:
        gyro = [1,2,3]
        accel = [4,5,6]
        mag = [7,8,9]
    '''
    senses[0]gyro[0] = x
    senses[0]gyro[1] = y
    senses[0]gyro[2] = z
    senses[1]accel[0] = x
    senses[1]accel[1] = y
    senses[1]accel[2] = z
    senses[2]mag[0] = x
    senses[2]mag[1] = y
    senses[2]mag[2] = z
    '''
    senses = [gyro, accel, mag]
    print('DoF sensor data sent')
    emit('sensorDoF-response', senses)

@socketio.on('remoteOut')
def handle_remoteOut(args):
    if (on_raspi):
        d.go(args[0], args[1])
    print('remote =', repr(args))

@app.route('/')
@app.route('/remote')
def remote():
    """Renders the remote control page."""
    return render_template(
        'remote.html',
        title='Remote Control')

@app.route('/extras')
def extras():
    """Renders the features page."""
    return render_template(
        'extras.html',
        title='Extra Features',
        message='Try our more advanced features!'
    )

@app.route('/automode')
def automode():
    """Google maps API with coordinate selection for auto mode."""
    return render_template(
        'automode.html',
        title='Autonomous Navigation',
        message='Autonomous Nav Mode'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About this project:',
        message='This Web App is meant to control a robot powered by Raspberry Pi via WiFi or LAN. '
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5555, debug=False)
