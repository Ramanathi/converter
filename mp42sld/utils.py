import subprocess
import pafy 
from PIL import Image
import numpy as np
import urllib.parse as urlparse 
import json
import cv2

# returns whether the file conversion is hindered 
def canceled(title):
    with open(title+'/'+'cancel.txt', 'r') as file:
        line = file.readlines()[0].split()[0]
        if line == "False":
            return False
        else:
            return True

# writes the status of cancel into the file cancel.txt
def write_cancel(title, cancel):
    f = open(title+'/'+'cancel.txt', "w")
    f.write(cancel)
    f.close()

# remove all files in a folder named <title>
def rmfiles(title):
    subprocess.run(["rm", "-r", title])

# A walkaround to decide whether two frames are same
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

# using the library urllib, we get the id of youtube video from any possible format, as per given if else conditions
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

# helper function to update the variables
def save_image(t, s, prev_frame, imageList):
    
    prev_frame = prev_frame[:,:,::-1]
    img = Image.fromarray(prev_frame, 'RGB')
    imageList.append(img)
    t.append(s)
    print(t)
    return t, prev_frame, imageList

# reducing the image resolution with upper bound of 480p
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

    
    if is_link:
        #get the video url
        url = f.get('url',None)
        # open url with opencv
        cap = cv2.VideoCapture(url)
    else:
        # open video file with opencv
        cap = cv2.VideoCapture(f)
    
    
    fps = cap.get(cv2.CAP_PROP_FPS)

    # check if video capture was successful
    if not cap.isOpened():
        print('video not opened')
        exit(-1)

    init_flag = True
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

            # this is applicable when the video capture is done by a existing video file, rather than link 
            frame = rescale_frame(frame)

            if init_flag:
                shape = frame.shape
                init_flag = False
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

# redudant mouse.json file to be created in compatible with slidecast viewer 
def mouse(max_time, title):
    ''' Extension possible - moving object detection'''
    mouse_actions = []
    i = 0
    while i < max_time:
        i = i + 0.1
        mouse_actions.append([i, [0, 0]])
    with open(title+"/mouse.json", 'w') as f:
        json.dump(mouse_actions, f)

# all images are saved to slides.pdf file
''' Preprocessing may reduce number of slides and accordingly keyboard.json - unique slide detection'''
def pdf_gen(imageList, title):
    imageList[0].save(title+"/slides.pdf",save_all=True,append_images=imageList[1:])


# gets audio at desired bit rate from bestaudio possible
def audio(video_id, title, bitrate="20k"):

    video = pafy.new(video_id)
    bestaudio = video.getbestaudio()
    file_name = title + "." + bestaudio.extension
    bestaudio.download(filepath = title+"/"+file_name)

    if not canceled(title):
        subprocess.run(["ffmpeg", "-y", "-i", title+"/"+file_name, "-b:a", bitrate, title+"/audio.mp3"])