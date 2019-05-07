import _thread
import time
import numpy as np

#libs required for face emotion recognition
import cognitive_face as CF
import requests
import json
from picamera import PiCamera
from time import sleep

#lib required for hearthrate emotion recognition
import RPi.GPIO as GPIO

#libs required for audio emotion recognition
import sys
import scipy.io.wavfile

sys.path.append("../lib/OpenVokaturi-3-0a/api")
print ("[AUDIO] Loading library...")
import Vokaturi
Vokaturi.load("../lib/OpenVokaturi-3-0a/lib/open/pi3b.so")
print ("[AUDIO] Analyzed by: %s" % Vokaturi.versionAndLicense())

import pyaudio
import wave

EMOTIONS = ['fear', 'happy', 'neutral', 'contempt', 'surprise', 'sadness', 'anger', 'disgust']

def evaluate_freq(bpm, avg_bpm):
    emotions = {
        "fear": 0,
        "happiness": 0,
        "neutral": 0,
        "contempt": 0,
        "surprise": 0,
        "sadness": 0,
        "anger": 0,
        "disgust": 0
    }
    
    if (bpm < avg_bpm*0.93) & (bpm > avg_bpm*0.85):
        emotions['sadness'] = 1
    if (bpm > avg_bpm*1.28) & (bpm < avg_bpm*1.40):
        emotions['fear'] = 1
    if (bpm > avg_bpm*1.13) & (bpm < avg_bpm*1.28):
        emotions['anger'] = 1
    if (bpm > avg_bpm*1.07) & (bpm < avg_bpm*1.13):
        emotions['happiness'] = 1
        emotions['surprise'] = 1
    if (bpm > avg_bpm*0.93) & (bpm < avg_bpm*1.07):
        emotions['neutral'] = 1
        emotions['disgust'] = 1
        emotions['contempt'] = 1
        
    return emotions

#HEART RATE THREAD
def heart_thread():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    i = 0
    j = 0
    sum = 0

    #record beats to compute mean bpm
    while (j < 3):
        count = 0
        sample = 0
        old_sample = sample
        timer = time.time()
        while ((time.time() - timer)<20):
            if (GPIO.input(26) == GPIO.HIGH):
                sample = 1
            else:
                sample = 0
            
            if (sample and (old_sample != sample)):
                count = count +1
            old_sample = sample 
        bpm = 3*count
        sum = sum + bpm
        print("[HEART] ", bpm)
        
        j =  j+ 1

    avg_bpm = sum/3 #compute the average bpm
    print( "[HEART] avg_bpm: ", avg_bpm)

    #monitor emotions
    while True:
        count = 0
        sample = 0
        old_sample = sample
        timer = time.time()
        while ((time.time() - timer)<20):
            if (GPIO.input(26) == GPIO.HIGH):
                sample = 1
            else:
                sample = 0
            
            if (sample and (old_sample != sample)):
                count = count +1
            old_sample = sample
        bpm = 3*count
        print("[HEART] bpm: ", bpm)
        emotions = evaluate_freq(bpm, avg_bpm)
        max_emotion = 0
        detected_emotion = ""
        for emotion, value in emotions.items():
            if value > max_emotion:
                detected_emotion = emotion
        print('[HEART] emotion detected: ', detected_emotion)
        print('[HEART] response: ', emotions)

#VISO THREAD
def viso_thread():
    KEY = '259c231550944ccbac666e1592deff23'
    CF.Key.set(KEY)
    BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
    CF.BaseUrl.set(BASE_URL)

    headers = {'Ocp-Apim-Subscription-Key': KEY, 'content-Type': 'application/octet-stream'}
    params = {'returnFaceAttributes': 'emotion'}

    camera = PiCamera()

    while True:
        sleep(3)
        img_path = '/home/pi/Industrial/Images/image.jpg'
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
            print('[VISO] this person is ', EMOTIONS[max_emotion])
            
def audio_thread():
    p = pyaudio.PyAudio()
    for ii in range(p.get_device_count()):
        print(str(ii) + " " + p.get_device_info_by_index(ii).get('name'))
    
    form_1 = pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    chunk = 132096 # number of recorded samples for buffer
    record_secs = 3 # seconds to record
    dev_index = 2 # device index found by p.get_device_info_by_index(ii)
    
    i = 0;
    while (True):
        # create pyaudio stream
        i = i+1
        wav_output_filename = '../sounds/test' + str(i) + '.wav' # name of .wav file
        audio = pyaudio.PyAudio()
        stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                            input_device_index = dev_index,input = True, \
                            frames_per_buffer=chunk)
        #print("[AUDIO] recording")
        frames = []

        # loop through stream and append audio chunks to frame array
        for ii in range(0,int((samp_rate/chunk)*record_secs)):
            data = stream.read(chunk)
            frames.append(data)

        #print("[AUDIO] finished recording")

        # stop the stream, close it, and terminate the pyaudio instantiation
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # save the audio frames as .wav file
        wavefile = wave.open(wav_output_filename,'wb')
        wavefile.setnchannels(chans)
        wavefile.setsampwidth(audio.get_sample_size(form_1))
        wavefile.setframerate(samp_rate)
        wavefile.writeframes(b''.join(frames))
        wavefile.close()
      
        #print ("[AUDIO] Filename: " + wav_output_filename)
        (sample_rate, samples) = scipy.io.wavfile.read(wav_output_filename)
        #print ("[AUDIO] sample rate %.3f Hz" % sample_rate)

        buffer_length = len(samples)
        #print ("[AUDIO] %d samples, %d channels" % (buffer_length, samples.ndim))
        c_buffer = Vokaturi.SampleArrayC(buffer_length)
        if samples.ndim == 1:  # mono
            c_buffer[:] = samples[:] / 32768.0
        else:  # stereo
            c_buffer[:] = 0.5*(samples[:,0]+0.0+samples[:,1]) / 32768.0

       
        voice = Vokaturi.Voice (sample_rate, buffer_length)

        
        voice.fill(buffer_length, c_buffer)

       
        quality = Vokaturi.Quality()
        emotionProbabilities = Vokaturi.EmotionProbabilities()
        voice.extract(quality, emotionProbabilities)

        if quality.valid:
            print ("[AUDIO] Neutral: %.3f" % emotionProbabilities.neutrality)
            print ("[AUDIO] Happy: %.3f" % emotionProbabilities.happiness)
            print ("[AUDIO] Sad: %.3f" % emotionProbabilities.sadness)
            print ("[AUDIO] Angry: %.3f" % emotionProbabilities.anger)
            print ("[AUDIO] Fear: %.3f" % emotionProbabilities.fear)
        else:
            print ("[AUDIO] Not enough sonorancy to determine emotions")

        voice.destroy()

heart_emotion = {}
viso_emotion = {}
audio_emotion = {}

try:
    _thread.start_new_thread(heart_thread, ())
    _thread.start_new_thread(viso_thread, ())
    _thread.start_new_thread(audio_thread, ())
except:
    print("[ERROR] unable to start thread")
    
while True:
    pass