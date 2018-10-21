#!/home/pi/.virtualenvs/cv/bin/python3.5

import cv2
import numpy as np
from picamera import PiCamera
from time import sleep



def makeVideo(fps, imageList):
    height , width , layers =  imageList[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 'x264' doesn't work
    video = cv2.VideoWriter('timelapse.avi',fourcc,fps,(width,height), True)
    fgbg= cv2.createBackgroundSubtractorMOG2()


    for image in imageList:
        # fgmask = fgbg.apply(image)
        frame = np.array(image)

        video.write(frame)
    cv2.destroyAllWindows()
    video.release()


fps = 30
defWait = 1/fps
slowFactor = 100
wait = defWait*slowFactor
videoLen = 10 # in seconds
numImages = videoLen*fps

print('| Starting')
print('| We will create a time lapse')
print('| Duration = ', videoLen, 'seconds')
print('| Slow Factor = ', slowFactor)
print('| The process will take = ', videoLen*slowFactor , 'seconds, which are', videoLen*slowFactor/60 ,'minutes')



# take the pictures

camera = PiCamera()
for index in range (numImages):
   camera.capture('/home/pi/Desktop/instapy/photos/' +str(index)+ '.jpg')
   sleep(wait)
   print('pic num', str(index))

# create the image list

imageList = []
for index in range(numImages):
    img = cv2.imread('/home/pi/Desktop/instapy/photos/'+ str(index) +'.jpg')
    imageList.append(img)

# create the video

makeVideo(fps, imageList)







print('version of opencv is', cv2.__version__)
