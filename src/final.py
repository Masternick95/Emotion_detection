import _thread
import threading
import time
import numpy as np

#import custom module for Graphical Interface
#from modules import GUI

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
_FEAR = 0
_HAPPINESS = 1
_NEUTRAL = 2
_CONTEMPT = 3
_SURPRISE = 4
_SADNESS = 5
_ANGER = 6
_DISGUST = 7

#global shared variables containing estimated emotions
heart_emotions = [0, 0, 0, 0, 0, 0, 0, 0]
heart_emotions_mutex = threading.Lock()
viso_emotions = [0, 0, 0, 0, 0, 0, 0, 0]
viso_emotions_mutex = threading.Lock()
audio_emotions = [0, 0, 0, 0, 0, 0, 0, 0]
audio_emotions_mutex = threading.Lock()

#mutex locking waiting for hearth calibration
calibration_mutex = threading.Lock()

def evaluate_freq(bpm, avg_bpm):
    emotions = [0, 0, 0, 0, 0, 0, 0, 0]
    
    if (bpm < avg_bpm*0.93) & (bpm > avg_bpm*0.85):
        #emotions['sadness'] = 1
        emotions[_SADNESS] = 1
    if (bpm > avg_bpm*1.28) & (bpm < avg_bpm*1.35):
        #emotions['fear'] = 1
        emotions[_FEAR] = 1
    if (bpm > avg_bpm*1.35):
        #emotions['anger'] = 1
        emotions[_ANGER] = 1
    if (bpm > avg_bpm*1.07) & (bpm < avg_bpm*1.13):
        #emotions['happiness'] = 1
        #emotions['surprise'] = 1
        emotions[_HAPPINESS] = 1
        emotions[_SURPRISE] = 1
    if (bpm > avg_bpm*0.93) & (bpm < avg_bpm*1.07):
        #emotions['neutral'] = 1
        #emotions['disgust'] = 1
        #emotions['contempt'] = 1
        emotions[_NEUTRAL] = 1
        emotions[_DISGUST] = 1
        emotions[_CONTEMPT] = 1
        
    return emotions

#HEART RATE THREAD
def heart_thread():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    i = 0
    j = 0
    sum = 0

    #record beats to compute mean bpm
    while (sum/3) < 50:
        sum = 0
        j = 0
        print("[HEART] starting calibration")
        while (j < 3):
            count = 0
            sample = 0
            old_sample = sample
            timer = time.time()
            while ((time.time() - timer)<10):
                if (GPIO.input(26) == GPIO.HIGH):
                    sample = 1
                else:
                    sample = 0
                
                if (sample and (old_sample != sample)):
                    count = count +1
                old_sample = sample 
            bpm = 6*count
            sum = sum + bpm
            print("[HEART] ", bpm)
            
            j =  j+ 1

    avg_bpm = sum/3 #compute the average bpm
    print( "[HEART] avg_bpm: ", avg_bpm)

    calibration_mutex.release()
    
    #monitor emotions
    while True:
        sleep(1)
        count = 0
        sample = 0
        old_sample = sample
        timer = time.time()
        while ((time.time() - timer)<10):
            if (GPIO.input(26) == GPIO.HIGH):
                sample = 1
            else:
                sample = 0
            
            if (sample and (old_sample != sample)):
                count = count +1
            old_sample = sample
        bpm = 6*count
        print("[HEART] bpm: ", bpm)
        if bpm >= 50:
            emotions = evaluate_freq(bpm, avg_bpm)
                
            max_emotion = np.argmax(emotions)
            if emotions[max_emotion] == 0:
                print('[HEART] no emotion detected')
            else:
                print('[HEART] emotion detected: ', EMOTIONS[max_emotion])
        
            print('[HEART] response: ', emotions)
        
            heart_emotions_mutex.acquire()
            
            heart_emotions[_FEAR] = emotions[_FEAR]
            heart_emotions[_HAPPINESS] = emotions[_HAPPINESS]
            heart_emotions[_NEUTRAL] = emotions[_NEUTRAL]
            heart_emotions[_CONTEMPT] = emotions[_CONTEMPT]
            heart_emotions[_SURPRISE] = emotions[_SURPRISE]
            heart_emotions[_SADNESS] = emotions[_SADNESS]
            heart_emotions[_ANGER] = emotions[_ANGER]
            heart_emotions[_DISGUST] = emotions[_DISGUST]
            
            #copy results in global variable
            heart_emotions_mutex.release()
            
            print('[HEART] heart_emotions: ', heart_emotions)
        else:
            print("[HEART] error reading sensor")

#VISO THREAD
def viso_thread():
    KEY = '22ba697bd23945c0918d7cbfebf70533'
    CF.Key.set(KEY)
    BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'
    CF.BaseUrl.set(BASE_URL)

    headers = {'Ocp-Apim-Subscription-Key': KEY, 'content-Type': 'application/octet-stream'}
    params = {'returnFaceAttributes': 'emotion'}

    camera = PiCamera()
    camera.start_preview(fullscreen=False, window=(700, 100, 300, 400))

    while True:
        sleep(3)
        img_path = '/home/pi/Industrial/Images/image.jpg'
        camera.capture(img_path)
        img_data = open(img_path, "rb").read()

        response = requests.post(BASE_URL + 'detect', params=params, headers=headers, data=img_data)
        print("[DEBUG] ", response, " payload: ", response.json())

        json_resp = response.json()
        person_found = False
        for person in json_resp:
            person_found = True
            #for each person(face) found
            emotions = person['faceAttributes']['emotion']
            fear = emotions['fear']
            happiness = emotions['happiness']
            neutral = emotions['neutral']
            contempt = emotions['contempt']
            surprise = emotions['surprise']
            sadness = emotions['sadness']
            anger = emotions['anger']
            disgust = emotions['disgust']
            
            max_emotion = np.argmax([fear, happiness, neutral, contempt, surprise, sadness, anger, disgust])
            print('[VISO] this person is ', EMOTIONS[max_emotion])
        
        if person_found:
            viso_emotions_mutex.acquire()
            viso_emotions[_FEAR] = fear
            viso_emotions[_HAPPINESS] = happiness
            viso_emotions[_NEUTRAL] = neutral
            viso_emotions[_CONTEMPT] = contempt
            viso_emotions[_SURPRISE] = surprise
            viso_emotions[_SADNESS] = sadness
            viso_emotions[_ANGER] = anger
            viso_emotions[_DISGUST] = disgust
            viso_emotions_mutex.release()
            
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
        sleep(1)
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
            
            audio_emotions_mutex.acquire()
            audio_emotions[_NEUTRAL] = emotionProbabilities.neutrality
            audio_emotions[_HAPPINESS] = emotionProbabilities.happiness
            audio_emotions[_SADNESS] = emotionProbabilities.sadness
            audio_emotions[_ANGER] = emotionProbabilities.anger
            audio_emotions[_FEAR] = emotionProbabilities.fear
            audio_emotions_mutex.release()
        else:
            print ("[AUDIO] Not enough sonorancy to determine emotions")

        voice.destroy()



#GUI MANAGING

import tkinter as tk

labels = ["fear", "happiness", "neutral", "contempt", "surprise", "sadness", "anger", "disgust"]

def create_window(window, title, emotions_canvas, emotion_status):
    #setup window
    window = tk.Tk()
    window.geometry("800x100")
    window.title(title)
    window.configure(background="white")
    window.resizable(False, False)

    for i in range(0, 8):
        emotion_label = tk.Label(window, text=labels[i], font=("helvetica", 20))
        emotion_label.grid(row = 0, column = i)

        emotions_canvas[i] = tk.Canvas(window, width=50, height=50)
        emotions_canvas[i].grid(row = 1, column = i)

        if emotion_status[i] == 1:
            emotions_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
        else:
            emotions_canvas[i].create_oval(10, 10, 40, 40, width=3)
            

def update_window(window, emotions_canvas, emotion_status):

    for i in range(0, 8):
        if emotion_status[i] == 1:
            emotions_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
        else:
            emotions_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="white")



audio_window = None
audio_canvas = [None, None, None, None, None, None, None, None]
audio_status = [0, 0, 0, 0, 0, 0, 0, 0]
#-----

audio_window = tk.Tk()
audio_window.geometry("650x100")
audio_window.title("Audio emotion recognition")
audio_window.configure(background="white")
audio_window.resizable(False, False)

for i in range(0, 8):
    emotion_label = tk.Label(audio_window, text=labels[i], font=("helvetica", 20))
    emotion_label.grid(row = 0, column = i)

    audio_canvas[i] = tk.Canvas(audio_window, width=50, height=50)
    audio_canvas[i].grid(row = 1, column = i)

    if audio_status[i] == 1:
        audio_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
    else:
        audio_canvas[i].create_oval(10, 10, 40, 40, width=3)

#audio_window.bind("<<audioUpdateEvent>>", update_gui)
#-----


#create_window(audio_window, "audio emotion recognition", audio_canvas, audio_status)

video_window = None
video_canvas = [None, None, None, None, None, None, None, None]
video_status = [0, 0, 0, 0, 0, 0, 0, 0]

#-----

video_window = tk.Tk()
video_window.geometry("650x100")
video_window.title("Video emotion recognition")
video_window.configure(background="white")
video_window.resizable(False, False)

for i in range(0, 8):
    emotion_label = tk.Label(video_window, text=labels[i], font=("helvetica", 20))
    emotion_label.grid(row = 0, column = i)

    video_canvas[i] = tk.Canvas(video_window, width=50, height=50)
    video_canvas[i].grid(row = 1, column = i)

    if video_status[i] == 1:
        video_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
    else:
        video_canvas[i].create_oval(10, 10, 40, 40, width=3)

#video_window.bind("<<videoUpdateEvent>>", update_gui)
#-----

#create_window(video_window, "video emotion recognition", video_canvas, video_status)

heart_window = None
heart_canvas = [None, None, None, None, None, None, None, None]
heart_status = [0, 0, 0, 0, 0, 0, 0, 0]

#-----

heart_window = tk.Tk()
heart_window.geometry("650x100")
heart_window.title("Heart emotion recognition")
heart_window.configure(background="white")
heart_window.resizable(False, False)

for i in range(0, 8):
    emotion_label = tk.Label(heart_window, text=labels[i], font=("helvetica", 20))
    emotion_label.grid(row = 0, column = i)

    heart_canvas[i] = tk.Canvas(heart_window, width=50, height=50)
    heart_canvas[i].grid(row = 1, column = i)

    try:
        if heart_status[i] == 1:
            heart_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
        else:
            heart_canvas[i].create_oval(10, 10, 40, 40, width=3)  
    except:
        pass

#heart_window.bind("<<heartUpdateEvent>>", update_gui)
#-----
#create_window(heart_window, "heart emotion recognition", heart_canvas, heart_status)

global_window = None
global_canvas = [None, None, None, None, None, None, None, None]
global_status = [0, 0, 0, 0, 0, 0, 0, 0]
#-----

global_window = tk.Tk()
global_window.geometry("650x100")
global_window.title("Global emotion recognition")
global_window.configure(background="white")
global_window.resizable(False, False)

for i in range(0, 8):
    emotion_label = tk.Label(global_window, text=labels[i], font=("helvetica", 20))
    emotion_label.grid(row = 0, column = i)

    global_canvas[i] = tk.Canvas(global_window, width=50, height=50)
    global_canvas[i].grid(row = 1, column = i)

    if global_status[i] == 1:
        global_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="green")
    else:
        global_canvas[i].create_oval(10, 10, 40, 40, width=3, fill="white")

#global_window.bind("<<globalUpdateEvent>>", update_gui)
#-----
#create_window(global_window, "Global emotion recognition", global_canvas, global_status)

def update_gui():
    try:
        data = gui_queue.get(timeout=0.1)
        
        audio_status = [0, 0, 0, 0, 0, 0, 0, 0]
        if data['audio'][np.argmax(data['audio'])] != 0:
            audio_status[np.argmax(data['audio'])] = 1
        update_window(audio_window, audio_canvas, audio_status)
        
        video_status = [0, 0, 0, 0, 0, 0, 0, 0]
        if data['video'][np.argmax(data['video'])] != 0:
            video_status[np.argmax(data['video'])] = 1
        update_window(video_window, video_canvas, video_status)
            
        heart_status = data['heart']
        print('[UPDATE GUI] data: ', data['heart'])
        print('[UPDATE GUI] status: ', heart_status)
        update_window(heart_window, heart_canvas, heart_status)
        
        global_status = [0, 0, 0, 0, 0, 0, 0, 0]
        if data['global'][np.argmax(data['global'])] != 0:
            global_status[np.argmax(data['global'])] = 1
        update_window(global_window, global_canvas, global_status)
    except:
        #print("exception in callback")
        pass
    
    #global_window.event_generate("<<globalUpdateEvent>>")
    global_window.after(300, update_gui)

#END GUI MANAGING
import queue
gui_queue = queue.Queue()

def global_thread():
    try:
        _thread.start_new_thread(heart_thread, ())
        calibration_mutex.acquire()
        
        #wait end of calibration
        calibration_mutex.acquire()
        print("[MAIN] Starting viso and audio threads")
        _thread.start_new_thread(viso_thread, ())
        _thread.start_new_thread(audio_thread, ())
    except:
        print("[ERROR] unable to start thread")
        
    while True:
        sleep(3)
        #get a local copy of the last reading
        heart_emotions_mutex.acquire()
        heart = heart_emotions
        heart_emotions_mutex.release()
        viso_emotions_mutex.acquire()
        video = viso_emotions
        viso_emotions_mutex.release()
        audio_emotions_mutex.acquire()
        audio = audio_emotions
        audio_emotions_mutex.release()
        print("[MAIN] heart_emotions: ", heart_emotions)
        print("[MAIN] heart: ", heart)
        
        avg_emotions = np.multiply(video, 0.6) + np.multiply(heart, 0.3) + np.multiply(audio, 0.1)
        print("[MAIN] avg prediction: ", avg_emotions)
        max_emotion = np.argmax(avg_emotions)
        if avg_emotions[max_emotion] == 0:
            print("[MAIN] no emotion detected")
        else:
            print("[MAIN] the predicted emotion is: ", EMOTIONS[max_emotion])
        
        gui_queue.put({'audio': audio, 'video': video, 'heart': heart, 'global': avg_emotions})
        
        #update GUI
        '''
        audio_status = [0, 0, 0, 0, 0, 0, 0, 0]
        audio_status[np.argmax(audio)] = 1
        update_window(audio_window, audio_canvas, audio_status)
        
        video_status = [0, 0, 0, 0, 0, 0, 0, 0]
        video_status[np.argmax(video)] = 1
        update_window(video_window, video_canvas, video_status)
            
        heart_status = [0, 0, 0, 0, 0, 0, 0, 0]
        heart_status[np.argmax(heart)] = 1
        update_window(heart_window, heart_canvas, heart_status)
        
        global_status = [0, 0, 0, 0, 0, 0, 0, 0]
        global_status[np.argmax(avg_emotions)] = 1
        update_window(global_window, global_canvas, global_status)
        '''



try:
    _thread.start_new_thread(global_thread, ())
except:
    print("Unable to start main thread")
    exit()
    
global_window.after(300, update_gui)
#global_window.event_generate("<<globalUpdateEvent>>")
tk.mainloop()

'''
while True:
    #sleep(3)
    
    #get a local copy of the last reading
    heart_emotions_mutex.acquire()
    heart = heart_emotions
    heart_emotions_mutex.release()
    viso_emotions_mutex.acquire()
    video = viso_emotions
    viso_emotions_mutex.release()
    audio_emotions_mutex.acquire()
    audio = audio_emotions
    audio_emotions_mutex.release()
    
    
    avg_emotions = np.multiply(video, 0.6) + np.multiply(heart, 0.3) + np.multiply(audio, 0.1)
    print("[MAIN] avg prediction: ", avg_emotions)
    max_emotion = np.argmax(avg_emotions)
    if avg_emotions[max_emotion] == 0:
        print("[MAIN] no emotion detected")
    else:
        print("[MAIN] the predicted emotion is: ", EMOTIONS[max_emotion])
    
    
    #update GUI
    audio_status = [0, 0, 0, 0, 0, 0, 0, 0]
    audio_status[np.argmax(audio)] = 1
    update_window(audio_window, audio_canvas, audio_status)
    
    video_status = [0, 0, 0, 0, 0, 0, 0, 0]
    video_status[np.argmax(video)] = 1
    update_window(video_window, video_canvas, video_status)
        
    heart_status = [0, 0, 0, 0, 0, 0, 0, 0]
    heart_status[np.argmax(heart)] = 1
    update_window(heart_window, heart_canvas, heart_status)
    
    global_status = [0, 0, 0, 0, 0, 0, 0, 0]
    global_status[np.argmax(avg_emotions)] = 1
    update_window(global_window, global_canvas, global_status)
    '''