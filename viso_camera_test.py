import cognitive_face as CF
import requests

from picamera import PiCamera
from time import sleep

KEY = '259c231550944ccbac666e1592deff23'
CF.Key.set(KEY)
BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)

headers = {'Ocp-Apim-Subscription-Key': KEY, 'content-Type': 'application/octet-stream'}
params = {'returnFaceAttributes': 'emotion'}

camera = PiCamera()
camera.start_preview()

for i in range(0, 5):
    sleep(3)
    img_path = '/home/pi/Industrial/Images/image_' + str(i) + '.jpg'
    camera.capture(img_path)
    img_data = open(img_path, "rb").read()

    response = requests.post(BASE_URL + 'detect', params=params, headers=headers, data=img_data)
    print(response)
    print(response.json())

camera.stop_preview()