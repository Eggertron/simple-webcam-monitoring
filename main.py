import threading
from MotionDetector import MotionDetector 

def main():

    webcam_urls = [
        #'http://192.168.50.240:8080/video',
        'http://192.168.50.238:8080/video',
        'http://192.168.50.249:8080/video'
    ]

    motion_detectors = []
    for url in webcam_urls:
        motion_detector = threading.Thread(target=MotionDetector, args=(url,))
        motion_detector.start()
        motion_detectors.append(motion_detector)


if __name__ == "__main__":
    main()
