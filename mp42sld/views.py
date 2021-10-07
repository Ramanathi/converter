from django.shortcuts import render
from mp42sld.forms import linkform
import cv2
import youtube_dl
import pafy 
from PIL import Image
import numpy as np
import urllib.parse as urlparse 
import subprocess
import json
from zipfile import ZipFile
import mimetypes
import os
from django.http.response import HttpResponse



intensity_threshold=10
sensitivity = 5 #in percentage
freq = 1
title = ""
img1 = []
imageList = []

##helper functions
def isSameFrame(f,f1,s):
    if f.shape != f1.shape:
        print("ERROR!! two frames of video are having different shapes")

    f_int = np.sqrt(np.sum(np.square(f),axis=2))
    f1_int = np.sqrt(np.sum(np.square(f1),axis=2))
    v = abs(f_int-f1_int)

    num = sum(sum((v > intensity_threshold) * np.ones(v.shape)))
    # if (f==f1).all():
    #     print(v)
    #     print((v>intensity_threshold)*v)


    if num > (f.shape[0]*f.shape[1]*sensitivity)/100:
        return False
    else:
        return True

def get_yt_link(url):
    query = urlparse.urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = urlparse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None

def save_image(t, s, prev_frame):
    prev_frame = prev_frame[:,:,::-1]
    img = Image.fromarray(prev_frame, 'RGB')
    if not t:
        global img1
        img1=img
    else:
        imageList.append(img)
    t.append(s)
    print(t)
    # img.show()
    return t, prev_frame

def read_frames(f):

    #get the video url
    url = f.get('url',None)

    # open url with opencv
    cap = cv2.VideoCapture(url)
    fps = cap.get(cv2.CAP_PROP_FPS)

    # check if url was opened
    if not cap.isOpened():
        print('video not opened')
        exit(-1)

    remove = True
    prev_frame = []
    s=-freq
    t=[]
    count=0
    key_actions = []

    while True:
        # read frame
        ret, frame = cap.read()
        s+=freq

        # check if frame is empty
        if not ret:
            t, prev_frame = save_image(t, s, prev_frame)
            break

        # display frame
        # cv2.imshow('frame', frame)

        if remove:
            shape = frame.shape
            remove = False
        
        if s==0:
            prev_frame = frame

        isSF = isSameFrame(frame,prev_frame,s)

        if not isSF:
            t, prev_frame = save_image(t, s, prev_frame)
            key_actions.append([s, "RIGHT"])

        prev_frame = frame
                    
        count += freq*fps # i.e.this advances freq seconds
        cap.set(1, count)

        if cv2.waitKey(30)&0xFF == ord('q'):
            break

    # release VideoCapture
    cap.release()
    cv2.destroyAllWindows()

    # creating pdf
    pdf_gen(s, t)

    # keyboard actions
    with open("keyboard.json", 'w') as f:
        json.dump(key_actions, f)

    #metadata
    with open("metadata", 'w') as f:
        json.dump({"width":shape[0],"height":shape[1]}, f)

    #mouse
    mouse(s)

def mouse(max_time):
    mouse_actions = []
    i = 0
    while i < max_time:
        i = i + 0.1
        mouse_actions.append([i, [0, 0]])
    with open("mouse.json", 'w') as f:
        json.dump(mouse_actions, f)

def pdf_gen(s, t):
    img1.save("slides.pdf",save_all=True,append_images=imageList)


def audio(video_id, bitrate="20k"):

    global title
    video = pafy.new(video_id)
    bestaudio = video.getbestaudio()
    title = bestaudio.title
    file_name = title + "." + bestaudio.extension
    bestaudio.download()
    subprocess.run(["ffmpeg", "-y", "-i", file_name, "-b:a", bitrate, "audio.mp3"])
    subprocess.run(["rm", file_name])

# Create your views here.
def index(request):
    if request.method == 'POST':
        form = linkform(request.POST)

        if form.is_valid():
            video_id = get_yt_link(form.cleaned_data.get('link'))
            bitrate = str(form.cleaned_data.get('bitrate'))+"k"
            print("can")
            global intensity_threshold,freq,sensitivity
            intensity_threshold = form.cleaned_data.get('intensity')
            freq = float(form.cleaned_data.get('freq'))
            sensitivity = form.cleaned_data.get('sensitivity')
            print(intensity_threshold,freq,sensitivity)
            print("can you see?")

            audio(video_id, bitrate)
            # bestaudio = video.getbestaudio()
            # bestaudio.download()

            ydl_opts = {}

            # create youtube-dl object
            ydl = youtube_dl.YoutubeDL(ydl_opts)

            # set video url, extract video information
            info_dict = ydl.extract_info(video_id, download=False)

            # get video formats available
            formats = info_dict.get('formats',None)

            max_px = '000p'
            for f in formats:
                px = f.get('format_note',None)
                if px[0] >= '0' and px[0] <= '9' and px <= '480p':
                    if px > max_px:
                        max_px = px
                        format = f
            
            read_frames(format)
            
            with ZipFile(title+'.zip', 'w') as zipObj:
                # Add multiple files to the zip
                zipObj.write('slides.pdf')
                zipObj.write('mouse.json')
                zipObj.write('keyboard.json')
                zipObj.write('metadata')
                zipObj.write('audio.mp3')
            
            subprocess.run(["rm", "slides.pdf", "mouse.json", "keyboard.json", "metadata", "audio.mp3"])
            
    return render(request, 'mp42sld/home.html')#, {'form': linkform()})

def download_file(request):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    global title
    print(title)
    ## remove this
    if not title:
        title = "Operating Systems Lecture 5 Scheduling Policies"
    ##
    filename = "/"+title + ".zip"
    filepath = BASE_DIR + filename
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    print(filename)
    response['Content-Disposition'] = "attachment; filename=%s" % filename

    return response
