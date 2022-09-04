# Code written by Lap Doan for Psych 196B
#
# Largely derived from iViewXAPI.py
# https://github.com/esdalmaijer/PyGaze/blob/master/pygaze/_eyetracker/iViewXAPI.py

from ctypes import *
import time
import directkeys
import psychopy_logging as logging

import tkinter as tk

#===========================
#        Constants
#===========================

CONST_SAMPLING_RATE_HZ = 30.0
CONST_TIME_AWAY_SECONDS = 0.5

CONST_LEFT_BORDER = -0.1
CONST_RIGHT_BORDER = 0.106
CONST_TOP_BORDER = 0.416
CONST_BOTTOM_BORDER = 0.584

CONST_BUTTON_CODE = 0x01 #esc
CONST_BUTTON_PRESS_TIME_SECONDS = 0.1

CONST_SETUP_TIME_SECONDS = 10

CONST_IS_64_BIT = True

CONST_DEBUG = False


#===========================
#        Struct Definition
#===========================

class CSystem(Structure):
    _fields_ = [("samplerate", c_int),
    ("iV_MajorVersion", c_int),
    ("iV_MinorVersion", c_int),
    ("iV_Buildnumber", c_int),
    ("API_MajorVersion", c_int),
    ("API_MinorVersion", c_int),
    ("API_Buildnumber", c_int),
    ("iV_ETDevice", c_int)]

class CCalibration(Structure):
    _fields_ = [("method", c_int),
    ("visualization", c_int),
    ("displayDevice", c_int),
    ("speed", c_int),
    ("autoAccept", c_int),
    ("foregroundBrightness", c_int),
    ("backgroundBrightness", c_int),
    ("targetShape", c_int),
    ("targetSize", c_int),
    ("targetFilename", c_char * 256)]

class CEye(Structure):
    _fields_ = [("gazeX", c_double),
    ("gazeY", c_double),
    ("diam", c_double),
    ("eyePositionX", c_double),
    ("eyePositionY", c_double),
    ("eyePositionZ", c_double)]

class CSample(Structure):
    _fields_ = [("timestamp", c_longlong),
    ("leftEye", CEye),
    ("rightEye", CEye),
    ("planeNumber", c_int)]

class CEvent(Structure):
    _fields_ = [("eventType", c_char),
    ("eye", c_char),
    ("startTime", c_longlong),
    ("endTime", c_longlong),
    ("duration", c_longlong),
    ("positionX", c_double),
    ("positionY", c_double)]

class CAccuracy(Structure):
    _fields_ = [("deviationLX",c_double),
                ("deviationLY",c_double),                
                ("deviationRX",c_double),
                ("deviationRY",c_double)]
                
#===========================
#        Loading iViewX.dll 
#===========================

if CONST_IS_64_BIT:
    iViewXAPI = windll.LoadLibrary("./iViewXAPI64.dll")
else:
    iViewXAPI = windll.LoadLibrary("./iViewXAPI.dll")

#===========================
#        Get screen res
#===========================

root = tk.Tk()

width_px = root.winfo_screenwidth()
height_px = root.winfo_screenheight()

#===========================
#        Initializing Structs
#===========================

systemData = CSystem(0, 0, 0, 0, 0, 0, 0, 0)
calibrationData = CCalibration(5, 1, 0, 0, 1, 20, 239, 1, 15, b"")
leftEye = CEye(0,0,0)
rightEye = CEye(0,0,0)
sampleData = CSample(0,leftEye,rightEye,0)
eventData = CEvent(b'F', b'L', 0, 0, 0, 0, 0)
accuracyData = CAccuracy(0,0,0,0)

# Main loop
def main():
    # Initialize data logger
    logger = logging.DataLogger()

    connection_status = iViewXAPI.iV_ConnectLocal()

    if connection_status == 100:
        print("Error: could not connect")

    current_gaze_x = 0.0
    current_gaze_y = 0.0
    game_paused = False
    num_failed_readings = 0

    # Wait for setup time to complete
    print("Will unpause the game and begin tracking gaze in " + str(CONST_SETUP_TIME_SECONDS) + " seconds...")
    time.sleep(CONST_SETUP_TIME_SECONDS)
    directkeys.PressKey(CONST_BUTTON_CODE)
    time.sleep(CONST_BUTTON_PRESS_TIME_SECONDS)
    directkeys.ReleaseKey(CONST_BUTTON_CODE)
    time.sleep(CONST_BUTTON_PRESS_TIME_SECONDS)
    print("Game unpaused; tracking now!")
    
    time_of_current_state = time.time()
    last = time.time()

    while True:
        # record every 1 / CONST_SAMPLING_RATE_HZ seconds
        next = last + 1.0 / CONST_SAMPLING_RATE_HZ
        if next > time.time():
            time.sleep(next - time.time())
        last = next
        iViewXAPI.iV_GetSample(byref(sampleData))

        out_of_range = False # out of range in current frame
        reading_failed = False

        # Check the average gaze of left and right eye.
        # If either eye's gaze is 0.0 (outside of screen), treat this as out of range.
        # Otherwise, update current_gaze_x and current_gaze_y.
        if sampleData.leftEye.gazeX == 0.0 or sampleData.rightEye.gazeX == 0.0:
            current_gaze_x = -1.0 * width_px
            out_of_range = True
            reading_failed = True
        else:
            current_gaze_x = (sampleData.leftEye.gazeX + sampleData.rightEye.gazeX) / 2.0

        if sampleData.leftEye.gazeY == 0.0 or sampleData.rightEye.gazeY == 0.0:
            current_gaze_y = -1.0 * height_px
            out_of_range = True
            reading_failed = True
        else:
            current_gaze_y = (sampleData.leftEye.gazeY + sampleData.rightEye.gazeY) / 2.0

        if reading_failed:
            num_failed_readings += 1
        else:
            num_failed_readings = 0

        # if too many failed readings, give warning
        if num_failed_readings > 0 and num_failed_readings % 100 == 0:
            if iViewXAPI.iV_IsConnected() == 101:
                print("WARNING: Connection lost with iViewRED")
            else:
                print("WARNING: " + str(num_failed_readings) + " consecutive failed readings")

        # regular_x and regular_y range from 0.0 to 1.0.
        # -1.0 indicates some sort of error in getting gaze location.
        regular_x = current_gaze_x / width_px
        regular_y = current_gaze_y / height_px

        if regular_x < CONST_LEFT_BORDER or regular_x > CONST_RIGHT_BORDER or regular_y < CONST_TOP_BORDER or regular_y > CONST_BOTTOM_BORDER:
            out_of_range = True

        # At this point, out_of_range should be accurate for the frame.
        # Update time_of_current_state accordingly.

        current_time = time.time()

        if game_paused == out_of_range:
            time_of_current_state = current_time

        # If time_of_current_state is too far in the past, toggle game_paused and send a keypress.

        if current_time - time_of_current_state >= CONST_TIME_AWAY_SECONDS:
            game_paused = not game_paused
            directkeys.PressKey(CONST_BUTTON_CODE)
            time.sleep(CONST_BUTTON_PRESS_TIME_SECONDS)
            directkeys.ReleaseKey(CONST_BUTTON_CODE)
            time.sleep(CONST_BUTTON_PRESS_TIME_SECONDS)
            time_of_current_state = current_time

        # Test data logging
        logger.log_position(regular_x, regular_y)

        # DEBUG
        if CONST_DEBUG:
            print(str(regular_x) + "," + str(regular_y) + "," + str(out_of_range) + "," + str(game_paused))

    iViewXAPI.iV_Disconnect() 

if __name__ == "__main__":
    main()