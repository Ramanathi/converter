from django.shortcuts import render, redirect
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
import time


def return_flag(title, file):
    with open(title+'/'+file, 'r') as file:
        line = file.readlines()[0].split()[0]
        if line == "False":
            return False
        else:
            return True

def write_to_file(title, file, content):
    f = open(title+'/'+file, "w")
    f.write(content)
    f.close()

def canceled(title):
    return return_flag(title, 'cancel.txt')

def write_cancel(title, cancel):
    write_to_file(title, 'cancel.txt', cancel)

##helper functions
def isSameFrame(f,f1,s, intensity_threshold, sensitivity, freq):
    if f.shape != f1.shape:
        print("ERROR!! two frames of video are having different shapes")

    f_int = np.sqrt(np.sum(np.square(f),axis=2))
    f1_int = np.sqrt(np.sum(np.square(f1),axis=2))
    v = abs(f_int-f1_int)

    num = sum(sum((v > intensity_threshold) * np.ones(v.shape)))


    if num > (f.shape[0]*f.shape[1]*sensitivity)/100:
        return False
    else:
        return True

def rmfiles(title):
    subprocess.run(["rm", "-r", title])

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

def save_image(t, s, prev_frame, imageList):
    
    prev_frame = prev_frame[:,:,::-1]
    img = Image.fromarray(prev_frame, 'RGB')
    imageList.append(img)
    t.append(s)
    print(t)
    # img.show()
    return t, prev_frame, imageList

def rescale_frame(frame_input):
    if frame_input.shape[0] > 480 :
        percent = 480/frame_input.shape[0]
        width = int(frame_input.shape[1] * percent)
        height = int(frame_input.shape[0] * percent)
        dim = (width, height)
        return cv2.resize(frame_input, dim, interpolation=cv2.INTER_AREA)
    else:
        return frame_input

def read_frames(f, intensity_threshold, sensitivity, freq, title, is_link):

    #get the video url
    if is_link:
        url = f.get('url',None)
        cap = cv2.VideoCapture(url)
    else:
        cap = cv2.VideoCapture(f)
    # open url with opencv
    
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
    imageList = []

    while True:
        # read frame
        if not canceled(title):
            ret, frame = cap.read()
            s+=freq

            # check if frame is empty
            if not ret:
                t, prev_frame, imageList = save_image(t, s, prev_frame, imageList)
                break

            frame = rescale_frame(frame)
            # display frame
            # cv2.imshow('frame', frame)

            if remove:
                shape = frame.shape
                remove = False
                prev_frame = frame

            isSF = isSameFrame(frame,prev_frame,s, intensity_threshold, sensitivity, freq)

            if not isSF:
                t, prev_frame, imageList = save_image(t, s, prev_frame, imageList)
                key_actions.append([s, "RIGHT"])

            prev_frame = frame
                        
            count += freq*fps # i.e.this advances freq seconds
            cap.set(1, count)

            if cv2.waitKey(30)&0xFF == ord('q'):
                break
        else:
            break

    # release VideoCapture
    cap.release()
    cv2.destroyAllWindows()

    # creating pdf
    if not canceled(title):
        pdf_gen(imageList, title)
    else:
        return

    # keyboard actions
    if not canceled(title):
        with open(title+"/keyboard.json", 'w') as f:
            json.dump(key_actions, f)
    else:
        return

    #metadata
    if not canceled(title):
        with open(title+"/metadata", 'w') as f:
            json.dump({"width":shape[1],"height":shape[0]}, f)
    else:
        return

    #mouse
    if not canceled(title):
        mouse(s, title)

def mouse(max_time, title):
    mouse_actions = []
    i = 0
    while i < max_time:
        i = i + 0.1
        mouse_actions.append([i, [0, 0]])
    with open(title+"/mouse.json", 'w') as f:
        json.dump(mouse_actions, f)

def pdf_gen(imageList, title):
    imageList[0].save(title+"/slides.pdf",save_all=True,append_images=imageList[1:])


def audio(video_id, title, bitrate="20k"):

    video = pafy.new(video_id)
    bestaudio = video.getbestaudio()
    file_name = title + "." + bestaudio.extension
    bestaudio.download(filepath = title+"/"+file_name)

    if not canceled(title):
        subprocess.run(["ffmpeg", "-y", "-i", title+"/"+file_name, "-b:a", bitrate, title+"/audio.mp3"])

def remove_redundant():
    arr = os.listdir('./')
    for name in arr:
        if int(time.time()) - int(os.path.getmtime(name)) > 10000:
            try:
                foldername = int(name)
                rmfiles(name)
            except:
                if name[-3:] == 'zip':
                    subprocess.run(['rm', name])

# Create your views here.
def index(request):

    title = str(int(time.time()))
    params = {'title' : title, 'done' : False}

    remove_redundant()

    if request.method == 'POST':
        form = linkform(request.POST)
        form.is_valid()

        if form.cleaned_data.get('link') or request.FILES.get('myfile'):

            title = form.cleaned_data.get('title')
            params['title'] = title

            if 'convert' in request.POST:
                
                bitrate = str(form.cleaned_data.get('bitrate'))+"k"
                intensity_threshold = 10
                freq = float(form.cleaned_data.get('freq'))
                sensitivity = form.cleaned_data.get('sensitivity')
                is_link = True

                
                subprocess.run(["mkdir", title])
                write_cancel(title, 'False')

                # set video url, extract video information
                if form.cleaned_data.get('link'):

                    ydl = youtube_dl.YoutubeDL({})
                    video_id = get_yt_link(form.cleaned_data.get('link'))
                    info_dict = ydl.extract_info(video_id, download=False)
                    audio(video_id, title, bitrate)

                    # get video formats available
                    formats = info_dict.get('formats',None)

                    max_px = '000p'
                    for f in formats:
                        px = f.get('format_note',None)
                        if px[0] >= '0' and px[0] <= '9' and px <= '480p':
                            if px > max_px:
                                max_px = px
                                format = f
                else:
                    is_link = False
                    f = request.FILES['myfile']
                    format = title+'/'+title+'.mp4'
                    with open(format, 'wb+') as destination:
                        for chunk in f.chunks():
                            destination.write(chunk)
                    command = "ffmpeg -i "+ format +" -ab "+bitrate+" -ac 2 -ar 44100 -vn " +title+"/audio.mp3"
                    subprocess.run(command.split())
                
                if not canceled(title):
                    read_frames(format, intensity_threshold, sensitivity, freq, title, is_link)

                if not canceled(title):
                    with ZipFile(title+'.zip', 'w') as zipObj:
                        # Add multiple files to the zip
                        zipObj.write(title+'/slides.pdf')
                        zipObj.write(title+'/mouse.json')
                        zipObj.write(title+'/keyboard.json')
                        zipObj.write(title+'/metadata')
                        zipObj.write(title+'/audio.mp3')

                    params['done'] = True

            elif 'cancel' in request.POST:
                write_cancel(title, 'True')
            
        elif 'download' in request.POST :
            title = form.cleaned_data.get('title')
            if title+'.zip' in os.listdir('./'):
                return redirect('/mp42sld/download/' + title)
            else:
                return HttpResponse("<html><body>Session Expired/File not Found, <a href="+'"'+"/mp42sld"+'"'+">Reload</a></body></html>")
            
    return render(request, 'mp42sld/home.html', params)#, {'form': linkform()})

def download_file(request, title):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    filename = title + ".zip"
    filepath = BASE_DIR +'/'+ filename
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    print(filename)
    response['Content-Disposition'] = "attachment; filename=%s" % filename

    return response
