#!/usr/bin/env python
from flask import Flask, render_template, Response
import cv2
import numpy as np

from src.components.tracker import Tracker
from src.components.camera import Camera


type = "RealSense" 

app = Flask(__name__)


if type == "RealSense":
    cam = Camera()
elif type == "ZED":
    cam = Tracker()
else:
    print("Invalid type")


def get_frame():
    while True:
        if type == "RealSense":
            cam.wait_for_frames()
            image = cam.get_image()  
            depth = cam.get_depth()
        
            # Convert depth to 8-bit and BGR for OpenCV
            depth_image_8bit = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
            depth_image_8bit = np.uint8(depth_image_8bit)
            depth_colormap = cv2.applyColorMap(depth_image_8bit, cv2.COLORMAP_TURBO)
            depth_bgr = cv2.cvtColor(depth_colormap, cv2.COLOR_RGB2BGR)

            imgencode=cv2.imencode('.jpg',np.hstack((image, depth_bgr)))[1]
        elif type == "ZED":
            cam.grab_frame()
            _, image = cam.get_image()
            imgencode=cv2.imencode('.jpg',image)[1]
        
        stringData=imgencode.tostring()
        yield (b'--frame\r\n'
            b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True, threaded=True)