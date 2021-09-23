from django.shortcuts import render
from mp42sld.forms import linkform
import cv2
import youtube_dl
import pafy 
from PIL import Image
import numpy as np
from numpy import linalg as LA
import time

intensity_threshold=10
num_threshold = 5 #in percentage
freq = 10

remove_this = True
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


    if num > (f.shape[0]*f.shape[1]*num_threshold)/100:
        return False
    else:
        return True










# Create your views here.
def index(request):
    if request.method == 'POST':
        form = linkform(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data.get('link')
            
            # print("video",video_url)
            video = pafy.new(video_url)
            bestaudio = video.getbestaudio()
            bestaudio.download()

            ydl_opts = {}

            # create youtube-dl object
            ydl = youtube_dl.YoutubeDL(ydl_opts)

            # set video url, extract video information
            info_dict = ydl.extract_info(video_url, download=False)

            # get video formats available
            formats = info_dict.get('formats',None)
            # print("a")
            for f in formats:
                # print(f)
                # print(f.get('format_note',None))
                # I want the lowest resolution, so I set resolution as 144p
                if f.get('format_note',None) == '360p':

                    #get the video url
                    url = f.get('url',None)

                    # print("this",url)
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
                    while True:
                        # read frame
                        ret, frame = cap.read()
                        s+=freq
                        # print(s)
                        # check if frame is empty
                        if not ret:
                            t.append(s)
                            print(t)
                            prev_frame = prev_frame[:,:,::-1]
                            img = Image.fromarray(prev_frame, 'RGB')
                            img.save(str(freq)+'_'+str(intensity_threshold)+'_'+str(num_threshold)+'_'+'output_'+str(s)+'.png')
                            img.show()
                            break

                        # display frame
                        # print(1)
                        # t1 = time.time()
                        cv2.imshow('frame', frame)
                        # t2 = time.time()
                        # print("imshow",t2-t1)
                        if remove:
                            print(frame.shape)
                            remove = False
                        # print(2)
                        # t = time.time()
                        if s==0:
                            prev_frame = frame
                        # t1 = time.time()
                        isSF = isSameFrame(frame,prev_frame,s)
                        # t2 = time.time()
                        # print("isSameFrame",t2-t1)
                        if not isSF:
                            t.append(s)
                            print(t)
                            prev_frame = prev_frame[:,:,::-1]
                            img = Image.fromarray(prev_frame, 'RGB')
                            img.save(str(freq)+'_'+str(intensity_threshold)+'_'+str(num_threshold)+'_'+'output_'+str(s)+'.png')
                            img.show()
                        # tt = time.time()
                        # print(tt-t)

                        prev_frame = frame
                    
                        count += freq*fps # i.e.this advances one second
                        cap.set(1, count)



                        if cv2.waitKey(30)&0xFF == ord('q'):
                            break

                    # release VideoCapture
                    cap.release()

                    # if multiple cases of same format is there
                    break

            cv2.destroyAllWindows()
    return render(request, 'home.html', {'form': linkform()})

