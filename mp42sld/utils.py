import subprocess
import pafy 
import urllib.parse as urlparse 
import cv2, os
import time

# all folders and zip files will be removed when a user tries to access this conversion tool if those were existing in the server for more than 3 hrs
def remove_redundant():
    arr = os.listdir('./')
    for name in arr:
        if int(time.time()) - int(os.path.getmtime(name)) > 10800:
            try:
                foldername = int(name)
                rmfiles(name)
            except:
                if name[-3:] == 'zip':
                    subprocess.run(['rm', name])

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

# gets audio at desired bit rate from bestaudio possible
def audio(video_id, title, bitrate="20k"):

    video = pafy.new(video_id)
    bestaudio = video.getbestaudio()
    file_name = title + "." + bestaudio.extension
    bestaudio.download(filepath = title+"/"+file_name)

    if not canceled(title):
        subprocess.run(["ffmpeg", "-y", "-i", title+"/"+file_name, "-b:a", bitrate, title+"/audio.mp3"])