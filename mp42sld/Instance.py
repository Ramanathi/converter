import numpy as np
from PIL import Image
import cv2, json
from mp42sld.utils import *

class Instance:

    def __init__(self, format, intensity_threshold, sensitivity, freq, title, is_link) -> None:
        self.format = format
        self.intensity_threshold = intensity_threshold
        self.sensitivity = sensitivity
        self.freq = freq
        self.title = title
        self.is_link = is_link

        self.frame_at = -self.freq
        self.frames_at=[]
        self.key_actions = []
        self.imageList = []
        
        self.read_frames()

        # creating pdf
        if not canceled(title):
            self.pdf_gen()
        else:
            return

        # keyboard actions
        if not canceled(title):
            with open(title+"/keyboard.json", 'w') as f:
                json.dump(self.key_actions, f)
        else:
            return

        #metadata
        if not canceled(title):
            with open(title+"/metadata", 'w') as f:
                json.dump({"width":self.shape[1],"height":self.shape[0]}, f)
        else:
            return

        #mouse
        if not canceled(title):
            self.mouse()
    
    def read_frames(self):

        if self.is_link:
            #get the video url
            url = self.format.get('url',None)
            # open url with opencv
            cap = cv2.VideoCapture(url)
        else:
            # open video file with opencv
            cap = cv2.VideoCapture(self.format)
        
        
        fps = cap.get(cv2.CAP_PROP_FPS)

        # check if video capture was successful
        if not cap.isOpened():
            print('video not opened')
            exit(-1)

        init_flag = True
        prev_frame = []
        count=0

        while True:
            # read frame
            if not canceled(self.title):
                ret, frame = cap.read()
                self.frame_at = self.frame_at + self.freq

                # check if frame is empty
                if not ret:
                    self.save_image(prev_frame)
                    break

                # this is applicable when the video capture is done by a existing video file, rather than link 
                frame = rescale_frame(frame)

                if init_flag:
                    self.shape = frame.shape
                    init_flag = False
                    prev_frame = frame

                isSF = self.isSameFrame(frame, prev_frame)

                if not isSF:
                    self.save_image(prev_frame)
                    self.key_actions.append([self.frame_at, "RIGHT"])

                prev_frame = frame
                            
                count += self.freq*fps # i.e.this advances freq seconds
                cap.set(1, count)

                if cv2.waitKey(30)&0xFF == ord('q'):
                    break
            else:
                break

        # release VideoCapture
        cap.release()
        cv2.destroyAllWindows()
    
    # A walkaround to decide whether two frames are same
    def isSameFrame(self, frame1, frame2):
        if frame1.shape != frame2.shape:
            print("ERROR!! two frames of video are having different shapes")

        frame1_int = np.sqrt(np.sum(np.square(frame1),axis=2))
        frame2_int = np.sqrt(np.sum(np.square(frame2),axis=2))
        v = abs(frame1_int - frame2_int)

        num = sum(sum((v > self.intensity_threshold) * np.ones(v.shape)))


        if num > (frame1.shape[0]*frame1.shape[1]*self.sensitivity)/100:
            return False
        else:
            return True

    # update the variables and save image
    def save_image(self, prev_frame):
    
        prev_frame = prev_frame[:,:,::-1]
        img = Image.fromarray(prev_frame, 'RGB')
        self.imageList.append(img)
        self.frames_at.append(self.frame_at)
        print(self.frames_at)

    # redudant mouse.json file to be created in compatible with slidecast viewer
    def mouse(self):
        ''' Extension possible - moving object detection '''
        mouse_actions = []
        max_time = self.frame_at
        i = 0
        while i < max_time:
            i = i + 0.1
            mouse_actions.append([i, [0, 0]])
        with open(self.title+"/mouse.json", 'w') as f:
            json.dump(mouse_actions, f)

    # all images are saved to slides.pdf file
    ''' Preprocessing may reduce number of slides and accordingly keyboard.json - unique slide detection '''
    def pdf_gen(self):
        self.imageList[0].save(self.title+"/slides.pdf",save_all=True,append_images=self.imageList[1:])
    
