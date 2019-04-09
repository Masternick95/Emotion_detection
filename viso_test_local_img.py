import cognitive_face as CF
import requests

KEY = '259c231550944ccbac666e1592deff23'
CF.Key.set(KEY)
BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)

img_path = '/home/pi/Industrial/Images/image_1.jpg'
img_data = open(img_path, "rb").read()

headers = {'Ocp-Apim-Subscription-Key': KEY, 'content-Type': 'application/octet-stream'}
params = {'returnFaceAttributes': 'emotion'}

response = requests.post(BASE_URL + 'detect', params=params, headers=headers, data=img_data)
print(response)
print(response.json())
