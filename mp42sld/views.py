from django.shortcuts import render
from mp42sld.forms import linkform
import cv2
import youtube_dl
import pafy 

# Create your views here.
def index(request):
    if request.method == 'POST':
        form = linkform(request.POST)
        if form.is_valid():
            video_url = form.cleaned_data.get('link')
            
            print(video_url)
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

            for f in formats:

                # I want the lowest resolution, so I set resolution as 144p
                if f.get('format_note',None) == '144p':

                    #get the video url
                    url = f.get('url',None)

                    print(url)
                    # open url with opencv
                    cap = cv2.VideoCapture(url)

                    # check if url was opened
                    if not cap.isOpened():
                        print('video not opened')
                        exit(-1)

                    while True:
                        # read frame
                        ret, frame = cap.read()

                        # check if frame is empty
                        if not ret:
                            break

                        # display frame
                        cv2.imshow('frame', frame)

                        if cv2.waitKey(30)&0xFF == ord('q'):
                            break

                    # release VideoCapture
                    cap.release()

                    print(1)

            cv2.destroyAllWindows()
    return render(request, 'home.html', {'form': linkform()})