import tkinter as tk

labels = ["fear", "happiness", "neutral", "contempt", "surprise", "sadness", "anger", "disgust"]

def create_window(window, title, emotions_canvas, emotion_status):
    #setup window
    window = tk.Tk()
    window.geometry("650x100")
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
            emotions_canvas[i].create_oval(10, 10, 40, 40, width=3)

audio_window = None
audio_canvas = [None, None, None, None, None, None, None, None]
audio_status = [0, 0, 0, 0, 0, 0, 0, 0]
create_window(audio_window, "audio emotion recognition", audio_canvas, audio_status)

video_window = None
video_canvas = [None, None, None, None, None, None, None, None]
video_status = [0, 0, 0, 0, 0, 0, 0, 0]
create_window(video_window, "video emotion recognition", video_canvas, video_status)

heart_window = None
heart_canvas = [None, None, None, None, None, None, None, None]
heart_status = [0, 0, 0, 0, 0, 0, 0, 0]
create_window(heart_window, "heart emotion recognition", heart_canvas, heart_status)

global_window = None
global_canvas = [None, None, None, None, None, None, None, None]
global_status = [0, 0, 0, 0, 0, 0, 0, 0]
create_window(global_window, "Global emotion recognition", global_canvas, global_status)

update_window(audio_window, audio_canvas, [0, 0, 1, 0, 0, 0, 0, 0])
