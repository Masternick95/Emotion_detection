from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.start_preview()
for i in range(0, 5):
    sleep(2)
    camera.capture('/home/pi/Industrial/Images/image_%s.jpg' %i)
camera.stop_preview()