#!/home/pi/.virtualenvs/cv/bin/python3.5

import cv2
import numpy as np
from picamera import PiCamera
from time import sleep
import time
import requests
import datetime
import os
import glob


def makeVideo(fps, imageList):
    height , width , layers =  imageList[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 'x264' doesn't work
    video = cv2.VideoWriter('timelapse2.avi',fourcc,fps,(width,height), True)
    fgbg= cv2.createBackgroundSubtractorMOG2()

    for image in imageList:
        # fgmask = fgbg.apply(image)
        frame = np.array(image)

        video.write(frame)
    cv2.destroyAllWindows()
    video.release()


def post_server(string):
    payload = {'status': string}
    requests.post('https://yorai.scripts.mit.edu/instapy_server/ping.py', params = payload)

def init_timelapse(slow_factor = 2):

    global fps
    fps = 30 # fixed
    defWait = 1/fps # fixed
    slowFactor = slow_factor # changeable from init --- acceleration should be more than X21, otherwise just X21
    wait = defWait*slowFactor # fixed, in seconds
    global wait_time_delta
    wait_time_delta = datetime.timedelta(seconds = wait)
    videoLen = 10 # in seconds # can be set, but usually fixed to 10 seconds
    global numImages
    numImages = videoLen*fps # fixed

    print('| Starting')
    print('| We will create a time lapse')
    print('| Duration = ', videoLen, 'seconds')
    print('| Slow Factor = ', slowFactor)
    print('| The process will take = ', videoLen*slowFactor , 'seconds, which are', videoLen*slowFactor/60 ,'minutes')

    global camera 
    camera = PiCamera()
    camera.vflip = True
    global last_capture_time 
    last_capture_time = datetime.datetime.now() - datetime.timedelta(days = 1)
    global image_counter 
    image_counter = 0

    # clear the folder where we will store images
    files = glob.glob('photos/*.jpg')
    for f in files:
        os.remove(f)


def get_sunrise_time():
    '''returns a datetime object with the sunrise time in UTC
    '''
    r = requests.get('https://api.sunrise-sunset.org/json?lat=42.361145&lng=-71.057083')
    time_string = r.json()['results']['sunrise']
    time_lst= time_string.split(':')
    hour = int(time_lst[0])
    minute = int(time_lst[1])

    # set so it is the next day
    start_time_utc = datetime.datetime.now() + datetime.timedelta(days = 1)
    start_time_utc = start_time_utc.replace(hour = hour, minute = minute, second = 0)

    # set to be 45 minutes before sunrise
    start_time_utc = start_time_utc - datetime.timedelta(minutes = 45)
    return start_time_utc




last_update_time = datetime.datetime.now() - datetime.timedelta(minutes = 3)







print('version of opencv is', cv2.__version__)

if __name__ == "__main__":
    # start the loop for the machine :
    '''states

    * get information from the web
        * sunrise time

    * send out an alive notice "preaparing"

    * check time constantly. If it is the same minute of the start time, then fall to the next state
        otherwise send out a "waiting to xx:xx:xx" time " every minute
    
    * start taking the photos, send out a "filming" notice every once in a while

    * send out "done"

    * export video to somewhere
    '''
    state = 0
    while True:
        # gather info from the web
        if state == 0:

            start_time_utc = get_sunrise_time()

            # start_hour = 23
            # start_min = 3
            # start_sec = 30

            # start_time = datetime.datetime.now()
            # start_time = start_time.replace(hour = start_hour, minute = start_min, second = 0)
            # start_time_utc = start_time + datetime.timedelta(hours = 5) - datetime.timedelta(days = 1)

            print('start time' ,start_time_utc)
            print('time now', datetime.datetime.now())

            if start_time_utc < datetime.datetime.now():
                # the time now is AFTER the start time. that's bad.
                post_server('ERROR - START TIME ' + str(start_time) +  ' ALREADY PASSED')
                raise InterruptedError('ERROR - START TIME ' + str(start_time) +  ' ALREADY PASSED')
                
            else:
                state = 1

        
        # send out an initializiing message
        if state == 1:
            print('Initializing Instapy')
            post_server('INITIALIZING INSTAPYY')
            print (datetime.datetime.now())
            state = 2
        
        # the waiting state.
        # if there is time, send a waiting message every minute
        # else, fall to next state - recording
        if state ==2:
            # check the time
            if datetime.datetime.now() >= start_time_utc:
                post_server('TIME TO START FILMING')
                init_timelapse(1)
                state = 3
            
            else:
                # we are still waiting, send out an update
                if datetime.datetime.now() - last_update_time > datetime.timedelta(minutes = 1):
                    post_server('WAITING... \nSTART TIME IS: ' + str(start_time_utc) + ' \nTIME NOW:' + str(datetime.datetime.now()))
                    last_update_time = datetime.datetime.now()
                
        if state == 3:
            # take photos
            # check that we still have photos to take and that enough time passed since last capture
            if image_counter < numImages and datetime.datetime.now() >= last_capture_time + wait_time_delta:
                print('pic num', str(image_counter))
                camera.capture('/home/pi/instapy/photos/' +str(image_counter)+ '.jpg')
                
                last_capture_time = datetime.datetime.now()
                image_counter += 1

            if datetime.datetime.now() >= last_update_time + datetime.timedelta(minutes = 1):

                post_server("CAPTURING,  " + str(image_counter)  +' / ' + str(numImages))
                last_update_time = datetime.datetime.now()
            
            if numImages == image_counter:
                # we captured all the photos, make a video and fall down to next state
                state = 4

        if state == 4:
            print('STATE 4')

            # create the image list
            imageList = []
            for index in range(numImages):
                img = cv2.imread('/home/pi/instapy/photos/'+ str(index) +'.jpg')
                imageList.append(img)

            # create the video
            makeVideo(fps, imageList)
            post_server("Done! In"  + str( datetime.datetime.now() - start_time_utc ) )

            break
