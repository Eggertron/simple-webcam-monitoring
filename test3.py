import os, cv2, time, threading, yaml, hashlib, shutil, datetime
from flask import (
    Flask,
    Response,
    render_template
)

# Read Settings file
config_file = "config.yaml"
default_settings = '''---
fps: 10
record_duration: 5
streams:
  - source: 2
    name: usb-cam
    fps: 10
    record_duration: 5
    pixels_diff_ratio: 0.001
    pixel_detect_thresh: 25
  - source: 0
    name: front-face
record_path: ./
pixels_diff_ratio: 0.001
pixel_detect_thresh: 25
storage_min_mb: 1000
debug: False
web_port: 8080
width: 640
height: 480
'''
streams_optional_keys = [
    "name",
    "fps",
    "record_duration",
    "pixels_diff_ratio",
    "pixel_detect_thresh"
]
default_keys = {}

try:
    with open(config_file, 'r') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)
except Exception as e:
    with open(config_file, 'w') as f:
        print("Error: {0} not found. Creating a default {0}".format(config_file))
        f.write(default_settings)
        print("INFO: Please check {} and restart.".format(config_file))
        exit(1)

try:
    default_keys['fps']                 = configs['fps']
    default_keys['record_duration']     = configs['record_duration'] # seconds
    default_keys['pixels_diff_ratio']   = configs['pixels_diff_ratio']
    default_keys['pixel_detect_thresh'] = configs['pixel_detect_thresh']
    streams                             = configs['streams']
    storage_min_mb                      = configs['storage_min_mb']
    record_path                         = configs['record_path']
    debug                               = configs['debug']
    web_port                            = configs['web_port']
    width                               = configs['width']
    height                              = configs['height']
except Exception as e:
    print(e)
    print("Error: unable to load {}. Might be corrupt.".format(config_file))
    exit(1)

# first record_path
if not record_path.endswith("/"):
    record_path = "{}/".format(record_path)

# Set Global Vars
fps = default_keys['fps']
storage_min_bytes = storage_min_mb * 1000 * 1000
out_frames = {}
lock = threading.Lock()
video_cap_retries = 20
video_cap_sleep = 5

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

def generate():
    global fps, lock, out_frames
    sleep_time = 1/fps
    while True:
        img_list = []
        with lock:
            for frame in out_frames.values():
                if frame is None:
                    continue
                img_list.append(frame)
        w_max = max([im.shape[1] for im in img_list])
        #im_list_resize = [cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=cv2.INTER_CUBIC) for im in img_list]
        im_list_resize = [ cv2.copyMakeBorder(im, 0, 0, 0, w_max - im.shape[1], cv2.BORDER_CONSTANT, value=0) for im in img_list ]
        img_result = cv2.vconcat(im_list_resize)
        flag, encoded_image = cv2.imencode(".jpg", img_result)
        if flag:
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
	        bytearray(encoded_image) + b'\r\n')
        time.sleep(sleep_time)

def debug_print(msg):
    global debug
    if debug:
        print("DEBUG: {}".format(msg))

def info_print(msg):
    print("INFO: {}".format(msg))

def warn_print(msg):
    print("WARN: {}".format(msg))

def error_print(msg):
    print("ERROR: {}".format(msg))

def record_frame(recorder, frame, close=False):
    recorder.write(frame)
    if close:
        debug_print("Recording saved.")
        recorder.release()

def storage_rotate(prefix):
    global record_path, storage_min_bytes
    '''check storage space and delete old videos'''
    bytes_free = shutil.disk_usage(record_path).free
    if bytes_free < storage_min_bytes:
        delete_old_video(prefix)

def delete_old_video(prefix):
    global record_path
    debug_print("Making room!")
    fp_list = [fp for fp in os.listdir(record_path) if prefix in fp]
    print(fp_list)
    fp_to_del = min(fp_list)
    debug_print("Removing video {}".format(fp_to_del))
    os.remove("{}{}".format(record_path, fp_to_del))

def init_record(frame, prefix):
    global fps, record_path
    suffix = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = "{}{}-{}.mp4".format(record_path, prefix, suffix)
    width = frame.shape[1]
    height = frame.shape[0]
    storage_rotate(prefix)
    debug_print("Motion Capture started: {}".format(filename))
    return cv2.VideoWriter(filename,
            cv2.VideoWriter_fourcc('m', 'p', '4', 'v'),
            fps,
            (width, height))

def set_capture_res(cap, x,y):
    # this should only be called if capture source is an Integer
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(x))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(y))

def resize_frame(frame, width=None, height=None):
    # Resize only if needed
    if width is None and height is None:
        return frame

    # check image size against desired width and height
    (frame_height, frame_width) = frame.shape[:2]

    # return image if below the max dimensions
    if (width is None or (width is not None and frame_width <= width)) and (height is None or (height is not None and frame_height <= width)):
        return frame

    # width is priority for our use case
    if width is not None and frame_width > width:
        r = width / float(frame_width)
        new_height = int(r * frame_height)
        debug_print("Resizing frame to {}x{}".format(width, new_height))
        return cv2.resize(frame, (width, new_height), interpolation=cv2.INTER_LINEAR)

    # height is secondary
    if height is not None and frame_height > height:
        r = height / float(frame_height)
        new_width = int(r * frame_width)
        debug_print("Resizing frame to {}x{}".format(new_width, height))
        return cv2.resize(frame, (new_width, height), interpolation=cv2.INTER_LINEAR)

def get_video_capture(src):
    global video_cap_retries, width, height, video_cap_sleep
    retries = 0
    info_print("Connecting to Capture Device...")
    while retries < video_cap_retries:
        cap = cv2.VideoCapture(src)
        if cap.isOpened():
            if isinstance(src, int) and width is not None and height is not None:
                set_capture_res(cap, width, height)
            info_print("Connected to {} successfully.".format(src))
            info_print("{} cap res set to {}x{}".format(src, width, height))))
            return cap
        else:
            retries += 1
            warn_print("Unable to connect to {}".format(src))
            info_print("Retry connection: {}".format(retries))
            time.sleep(video_cap_sleep)
    error_print("Permanant failure to connect with {}".format(src))
    exit(1)

def start_cap(stream):
    global width, height,debug, lock, out_frames
    src = stream['source']
    record_duration = stream['record_duration']
    pixel_detect_thresh = stream['pixel_detect_thresh']
    pixel_diff_ratio = stream['pixels_diff_ratio']
    fps = stream['fps']
    prefix = stream['name']
    cap = get_video_capture(src)
    is_show = True
    sleep_time = 1/fps
    frame = None
    prev_frame = None
    diff_frame = None
    recorder = None
    rframe_count = 0
    min_pixels_trigger = None
    status = None
    while is_show:
        try:
            if cap.isOpened():
                if frame is not None:
                    prev_frame = frame
                (status, frame) = cap.read()
                frame = resize_frame(frame, width, height)
        except Exception as e:
            info_print("Lost connection to {}.\nAttempting to reestablish connection...".format(src))
            cap = get_video_capture(src)

        if status:
            if min_pixels_trigger is None:
                min_pixels_trigger = frame.size * pixel_diff_ratio
                debug_print("Setting min_pixels_trigger to {}".format(min_pixels_trigger))
            if prev_frame is not None:
                out_frames[str(src)] = frame.copy()
                diff_frame = cv2.absdiff(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                        cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                        )
                diff_frame = cv2.threshold(diff_frame, pixel_detect_thresh, 255, cv2.THRESH_BINARY)[1]
                detected_pixels = cv2.countNonZero(diff_frame)
                if   detected_pixels > min_pixels_trigger:
                    debug_print("Motion Detected! Detected Pixels Ratio: {}".format(detected_pixels))
                    if recorder is None:
                        recorder = init_record(frame, prefix)
                        rframe_count = record_duration * fps
            #cv2.imshow('frame {}'.format(src), frame)
            if diff_frame is not None and debug:
                cv2.imshow('diff {}'.format(prefix), diff_frame)
            if recorder is not None:
                debug_print("Frames left to capture: {}".format(rframe_count))
                if rframe_count < 1:
                    record_frame(recorder, frame, True)
                    recorder = None
                else:
                    record_frame(recorder, frame)
                    rframe_count -= 1

            

        key = cv2.waitKey(1)
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            is_show = False

        time.sleep(sleep_time) # fps sleep


if __name__ == "__main__":
    for stream in streams:
        src = stream['source']
        for key in streams_optional_keys:
            if key not in stream:
                if key == 'name':
                    stream[key] = "video-{}".format(hashlib.sha1(str(src).encode("UTF-8")).hexdigest()[:6])
                else:
                    stream[key] = default_keys[key]
        threading.Thread(target=start_cap, args=(stream,)).start()
        out_frames[str(src)] = None
    app.run(host="0.0.0.0", port=web_port, debug=True, threaded=True, use_reloader=False)
