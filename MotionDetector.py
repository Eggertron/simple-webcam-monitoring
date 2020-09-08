import cv2, time, threading
import numpy as np
from datetime import datetime
from flask import (
    Flask,
    Response,
    render_template
)

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()

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
        self.fps            = 2
        self.run()

    def run(self):
        frame_counter = 0
        proc_frame = None
        while True:
            # Grab Frame from capture source
            check, frame = self.cap.read()

            print(check)
            frame_counter += 1
            print("Frames processed: {}".format(frame_counter))

            # Process Frame
            #frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
            if frame is not None:
                proc_frame = self.process_frame(frame)
            if proc_frame is None:
                continue

            # Check for 'q' key press to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
               break

    def process_frame(self, frame):
        global outputFrame, lock
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

        # acquire the lock, set the output frame, and release the
	# lock
        with lock:
            outputFrame = frame.copy()

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

### Flask

# initialize a flask object
app = Flask(__name__)

@app.route("/")
def index():
	# return the rendered template
	return render_template("index.html")

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

def generate():
	# grab global references to the output frame and lock variables
	global outputFrame, lock
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame is None:
				continue
			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			# ensure the frame was successfully encoded
			if not flag:
				continue
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

### End of Flask
if __name__=="__main__":
    #url = "http://192.168.50.241:8888/video?.mjpg"
    url = "0"
    t = MotionDetector(url)
    # start the flask app
    app.run(host='0.0.0.0', port='8888', debug=True,
        threaded=True, use_reloader=False)
