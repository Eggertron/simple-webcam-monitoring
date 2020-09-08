import cv2, time, threading
from flask import (
    Flask,
    Response,
    render_template
)


class VideoStreamer():
    def __init__(self, src=0, fps=30):
        self.fps = fps
        self.frame_count =0
        self.cap = cv2.VideoCapture(src)
        self.lock = threading.Lock()
        self.frame = None
        self.thread = Thread(target-self.start_show_frame, args=())
        self.thread.start()
        self.start_flask()
        self.app = Flask(__name__)

    def start_flask(self):
        vs = []
        self.app.run(host="0.0.0.0", port=8888, debug=True, threaded=True, use_reloader=False)

    @self.app.route("/")
    def index(self):
        return render_template("index.html")

    @self.app.route("/video_feed")
    def video_feed(self):
        return Reponse(self.generate(),
                mimetype = "multipart/x-mixed-replace; boundary=frame")

    def generate(self):
        global vs
        lock = vs[0].getlock
        while True:
            with lock:
                if outputFrame is None:
                    continue
                flag, encodedImage = cv2.imencode(".jpg", outputFrame)
                if not flag:
                    continue
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n{}\r\n'.format(bytearray(encodedImage)))

    def get_frame(self):
        with self.lock:
            result = self.frame.copy()
        return result

    def set_fps(self, fps):
        self.fps = fps

    def start_show_frame(self):
        is_show_frame = True
        sleep_time = 1/self.fps
        frame = None
        prev_frame = None
        diff_frame = None
        while is_show_frame:
            if self.cap.isOpened():
                if frame is not None:
                    prev_frame = frame
                (status, frame) = self.cap.read()
                with self.lock:
                    self.frame = frame.copy()

            if status:
                if prev_frame is not None:
                    diff_frame = cv2.absdiff(
                            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                            cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                            )
                    diff_frame = cv2.threshold(diff_frame, 25, 150, cv2.THRESH_BINARY)[1] 
                    white_ratio = cv2.countNonZero(diff_frame) / diff_frame.size
                    if white_ratio > 0.1:
                        print("Motion>10%: {}".format(white_ratio))
                self.frame_count += 1
                #print("Frame count: {}".format(self.frame_count))
                cv2.imshow('IP Camera Video Streaming', frame)
                if diff_frame is not None:
                    cv2.imshow('diff frame', diff_frame)

            key = cv2.waitKey(1)
            if key == ord('q'):
                self.cap.release()
                cv2.destroyAllWindows()
                is_show_frame = False

            time.sleep(sleep_time)


if __name__ == '__main__':
    vs = VideoStreamer(0, 10)
