from django.shortcuts import render, redirect
from mp42sld.forms import linkform
import youtube_dl
from zipfile import ZipFile
import mimetypes
import os
from django.http.response import HttpResponse
import time
from mp42sld.Instance import *

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

                if form.cleaned_data.get('link'):

                    ydl = youtube_dl.YoutubeDL({})
                    video_id = get_yt_link(form.cleaned_data.get('link'))
                    info_dict = ydl.extract_info(video_id, download=False)
                    audio(video_id, title, bitrate)

                    # get video formats available
                    formats = info_dict.get('formats',None)

                    # chosing a format with upper bound of 480p
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
                    Instance(format, intensity_threshold, sensitivity, freq, title, is_link)

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
