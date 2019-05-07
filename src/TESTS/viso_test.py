import cognitive_face as CF
import requests

KEY = '259c231550944ccbac666e1592deff23'
CF.Key.set(KEY)
BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
CF.BaseUrl.set(BASE_URL)
#happy gnocca
#img_url = 'https://raw.githubusercontent.com/Microsoft/Cognitive-Face-Windows/master/Data/detection1.jpg'

#anger man
#img_url = 'http://lyceum2017.altervista.org/wp-content/uploads/2018/01/Rage.jpg'

#hulk
#img_url = 'https://www.chiarafrancesconi.it/images/dominare-la-rabbia.png'

#nero felice
#img_url = 'https://mobile-cdn.123rf.com/300wm/mimagephotography/mimagephotography1411/mimagephotography141100065/33352476-close-up-ritratto-di-un-uomo-di-colore-alla-moda-sorridente-su-sfondo-grigio.jpg?ver=6'

#contempt man
img_url = 'https://upload.wikimedia.org/wikipedia/commons/3/31/Contempt.jpg'

headers = {'Ocp-Apim-Subscription-Key': KEY}
params = {'returnFaceAttributes': 'emotion'}

response = requests.post(BASE_URL + 'detect', params=params, headers=headers, json={"url": img_url})
print(response.json())