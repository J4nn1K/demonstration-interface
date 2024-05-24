#!/usr/bin/env python
from flask import Flask, render_template, Response
import cv2
import sys
import numpy

from src.components.camera import Camera

app = Flask(__name__)

cam = Camera()

def get_frame():
    while True:
        cam.grab_frame()
        _, image = cam.get_image()

        imgencode=cv2.imencode('.jpg',image)[1]
        stringData=imgencode.tostring()
        yield (b'--frame\r\n'
            b'Content-Type: text/plain\r\n\r\n'+stringData+b'\r\n')


@app.route('/')
def vid():
    return Response(get_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True, threaded=True)