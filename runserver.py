"""
This script runs the flask_controller application using a development server.
"""

try:
    import cStringIO as io
except ImportError:
    import io

import base64
import os
from flask import Flask, g, render_template
from flask_socketio import SocketIO, emit
#from outputs.drivetrain import drivetrain

on_raspi = False

if on_raspi:
    import picamera
    camera = picamera.PiCamera()
    camera.start_preview()
else:
    import cv2
    camera = cv2.VideoCapture(0)

#d = drivetrain(17, 27, 22, 23)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=False)

@socketio.on('connect')
def handle_connect():
    print('websocket Client connected!')

@socketio.on('disconnect')
def handle_disconnect():
    print('websocket Client disconnected')


@socketio.on('webcam')
def handle_webcam_request():
    if on_raspi:
        sio = io.StringIO()
        camera.capture(sio, "jpeg", use_video_port=True)
        buffer = sio.getvalue()
    else:
        _, frame = camera.read()
        _, buffer = cv2.imencode('.jpg', frame)

    emit('webcam-response', base64.b64encode(buffer))

@socketio.on('remoteOut')
def handle_remoteOut(args):
    #d.go(args[0], args[1])
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
        message='This Web App is meant to control a robot powered by Raspberry Pi via WiFi hotspot. It uses various Python modules including Flask(web site server), HostAPD(hotspot), gpiozero(Robot and servo classes) and some custom written modules.'
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5555, debug=False)
