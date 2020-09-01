import cv2, time
import numpy as np
from datetime import datetime

class MotionDetector:
    def __init__(self, src):
        self.src            = src
        self.window_name    = "Window - {}".format(src)
        self.cap            = cv2.VideoCapture(self.src)
        self.video_out      = None
        self.prev_frame     = None
        self.moving_avg     = None
        self.duration       = 0
        self.is_recording   = False
        self.fps            = 3
        self.run()

    def run(self):
        frame_counter = 0
        while True:
            # Grab Frame from capture source
            check, frame = self.cap.read()

            #print(check)
            frame_counter += 1
            print("Frames processed: {}".format(frame_counter))

            # Process Frame
            #frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
            proc_frame = self.process_frame(frame)
            if proc_frame is None:
                continue

            # Check for 'q' key press to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
               break

    def process_frame(self, frame):
        # Change to gray scale and remove minor
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.prev_frame is None:
            self.prev_frame = gray
            self.moving_avg = np.float32(gray)
            return None


        # Get diff of previous frame and current frame
        #print(gray.shape, self.prev_frame.shape)
        diff_frame = cv2.absdiff(self.prev_frame, gray)

        # Change static areas to white for thresholds of 25
        thresh_frame = cv2.threshold(diff_frame, 25, 255, cv2.THRESH_BINARY)[1]
        thresh_frame = cv2.dilate(thresh_frame, None, iterations = 2)
        # Finding contour and hierarchy from a moving object.
        contours, hierachy = cv2.findContours(thresh_frame.copy(),
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) < 1000:
                continue
            ## MOTION HAS BEEN TRIGGERED
            fps = self.fps
            seconds = 3
            self.duration = seconds * fps
            self.init_record('video-{}.mp4'.format(time.time()), frame)
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        # Find average
        cv2.accumulateWeighted(gray, self.moving_avg, 0.05)
        self.prev_frame = cv2.convertScaleAbs(self.moving_avg)

        # Show Frames, this needs to move out
        #self.show_frame(gray, "Gray Frame")
        #self.show_frame(thresh_frame, "Threshold Frame")
        self.show_frame(frame, "Original Frame")
        #self.show_frame(self.prev_frame, "previous Frame")

        self.frame_record(frame)

        return frame 

    def init_record(self, filename, frame):
        if self.is_recording:
            return
        width = frame.shape[1]
        height = frame.shape[0]
        fps = self.fps
        self.video_out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc('m','p','4','v'), fps, (width, height))
        self.is_recording = True

    def frame_record(self, frame):
        if not self.is_recording:
            return
        self.video_out.write(frame)
        if self.duration == 0:
            self.is_recording = False
            self.video_out.write(frame)
            self.video_out.release()
        self.duration -= 1

    def show_frame(self, frame, win_title):
        cv2.imshow("{} - {}".format(self.window_name, win_title), frame)

if __name__=="__main__":
    url = "http://192.168.50.249:8080/video"
    t = MotionDetector(url)
