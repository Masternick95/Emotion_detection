import cognitive_face as CF
import requests
import json
import numpy as np

from picamera import PiCamera
from time import sleep

KEY = '259c231550944ccbac666e1592deff23'
CF.Key.set(KEY)
BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)

headers = {'Ocp-Apim-Subscription-Key': KEY, 'content-Type': 'application/octet-stream'}
params = {'returnFaceAttributes': 'emotion'}

camera = PiCamera()
#camera.start_preview()

EMOTIONS = ['fear', 'happy', 'neutral', 'contempt', 'surprise', 'sadness', 'anger', 'disgust']

for i in range(0, 5):
    sleep(3)
    img_path = '/home/pi/Industrial/Images/image_' + str(i) + '.jpg'
    camera.capture(img_path)
    img_data = open(img_path, "rb").read()

    response = requests.post(BASE_URL + 'detect', params=params, headers=headers, data=img_data)
    print("[DEBUG] ", response, " payload: ", response.json())

    json_resp = response.json()
    for person in json_resp:
        #for each person(face) found
        emotions = person['faceAttributes']['emotion']
        fear = emotions['fear']
        happyness = emotions['happiness']
        neutral = emotions['neutral']
        contempt = emotions['contempt']
        surprise = emotions['surprise']
        sadness = emotions['sadness']
        anger = emotions['anger']
        disgust = emotions['disgust']
        
        max_emotion = np.argmax([fear, happyness, neutral, contempt, surprise, sadness, anger, disgust])
        print('this person is ', EMOTIONS[max_emotion]) 

#camera.stop_preview()
