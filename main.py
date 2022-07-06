from flask import Flask, render_template, Response, make_response, redirect, request, url_for, jsonify
import cv2
from subprocess import check_output

import RPi.GPIO as GPIO
import time
import os
import numpy as np

mode = GPIO.getmode()
GPIO.setmode(GPIO.BCM)

GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_UP)
def shutdownrpi(channel):
    print("Shutting down")
    time.sleep(5)
    os.system("sudo shutdown -h now")
    
GPIO.add_event_detect(21, GPIO.FALLING, callback=shutdownrpi, bouncetime=2000)

speed = 25 #Starting PWM % value for wheels
sleepturn = 0.3

imgcount = 0

Apin1 = 15
Apin2 = 14
Bpin1 = 26
Bpin2 = 19
Aen = 18   #PWM pin
Ben = 13   #PWM pin

GPIO.setup(Apin1, GPIO.OUT)
GPIO.setup(Apin2, GPIO.OUT)
GPIO.setup(Bpin1, GPIO.OUT)
GPIO.setup(Bpin2, GPIO.OUT)
GPIO.setup(Aen, GPIO.OUT)
GPIO.setup(Ben, GPIO.OUT)

#GPIO.output(Aen, GPIO.HIGH)
#GPIO.output(Ben, GPIO.HIGH)
Ap = GPIO.PWM(Aen, 1000)
Bp = GPIO.PWM(Ben, 1000)
Ap.start(speed)
Bp.start(speed)

def forward():
    GPIO.output(Apin1, GPIO.LOW)
    GPIO.output(Apin2, GPIO.HIGH)
    GPIO.output(Bpin1, GPIO.LOW)
    GPIO.output(Bpin2, GPIO.HIGH)
    print("MF")
    
def backward():
    GPIO.output(Bpin1, GPIO.HIGH)
    GPIO.output(Bpin2, GPIO.LOW)
    GPIO.output(Apin1, GPIO.HIGH)
    GPIO.output(Apin2, GPIO.LOW)
    print("MB")
    
def stop():
    GPIO.output(Apin1, GPIO.HIGH)
    GPIO.output(Apin2, GPIO.HIGH)
    GPIO.output(Bpin1, GPIO.HIGH)
    GPIO.output(Bpin2, GPIO.HIGH)
    print("S")
    
def turnleft():
    GPIO.output(Bpin1, GPIO.LOW)
    GPIO.output(Bpin2, GPIO.HIGH)
    GPIO.output(Apin1, GPIO.HIGH)
    GPIO.output(Apin2, GPIO.LOW)
    print("ML")
    time.sleep(sleepturn)
    stop()
    
def turnright():
    GPIO.output(Apin1, GPIO.LOW)
    GPIO.output(Apin2, GPIO.HIGH)
    GPIO.output(Bpin1, GPIO.HIGH)
    GPIO.output(Bpin2, GPIO.LOW)
    print("MR")
    time.sleep(sleepturn)
    stop()

def created_imgs():
    global imgcount
    cv2.imwrite('/home/agn/Pictures/createdimgs/{}.jpg'.format(imgcount), simg)
    imgcount += 1
    

def check_wifi():
    wifi_ip = check_output(['hostname', '-I'])
    wifi_str = str(wifi_ip.decode())
    if len(wifi_ip) > 4:
        wifi_str = wifi_str[:-2]
        print(len(wifi_str))
        print('connected')
        return wifi_str
    print("not connected")
    return None

ip_adr = check_wifi()
print(ip_adr)
print(type(ip_adr))

img_size = (240,320)
if ip_adr is not None:
    app = Flask(__name__)
    
    simg = np.empty(shape = (img_size[0],img_size[1],3))
    
    def gen_frames():
        camera = cv2.VideoCapture(0)
        while True:
            success, frame = camera.read()  # read the camera frame
            if not success:
                break
            else:
                #w = int(frame.shape[1]/2)
                #h = int(frame.shape[0]/2)
                global simg
                simg = cv2.resize(frame, (img_size[1],img_size[0]))
                ret, buffer = cv2.imencode('.jpg', simg)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
    
    def gen_seq(): 
        while True:
            imginv = cv2.bitwise_not(simg)
            ret, buffer = cv2.imencode('.jpg', imginv)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
                

    @app.route("/")
    def main_page():
        print("Page is working")
        return render_template("index.html")

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/seq_feed')
    def seq_feed():
        return Response(gen_seq(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/process', methods=["GET", "POST"])
    def background_process_test():
        if request.method == "POST":
            data = request.get_json()
            print (type(data))
            if data == "F" : 
                print("the machine moves forward")
                forward()
            elif data == "B" : 
                print("the machine moves back")
                backward()
            elif data == "L" : 
                print("the machine moves left")
                turnleft()
            elif data == "R" : 
                print("the machine moves right")
                turnright()
            elif data == "S" : 
                print("the machine stops")
                stop()
            elif data == "C" : 
                print("recording frames turned ON/OFF")
                created_imgs()
        return ("nothing")

    if __name__ == "__main__":
        app.run(debug=True, host = ip_adr, port=8030, threaded = True)

