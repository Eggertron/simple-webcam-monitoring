import numpy as np
import cv2

def main():

    webcam_urls = [
        'http://192.168.50.240:8080/video',
        'http://192.168.50.238:8080/video',
        'http://192.168.50.249:8080/video'
    ]

    # Setup the video capture source objects
    cap_list = []
    for url in webcam_urls:
        cap = cv2.VideoCapture(url)
        cap_list.append(cap)

    while(True):
        if len(cap_list) < 1:
            break
		
        show_cap_list(cap_list)
	
        # Check if q key was pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    for cap in cap_list:
        cap.release()
	
    cv2.destroyAllWindows()


def show_cap_list(cap_list):
    counter = 0
    for cap in cap_list:
        ret, frame = cap.read()

        # Our operations on the frame come here
        frame = process_frame(frame)

        # Display the resulting frame
        cv2.imshow("window-{}".format(counter), frame)
        counter += 1


def get_max_size_of_caps(cap_list):
    # Find the largest width and height
    max_height = 0
    max_width = 0
    for cap in cap_list:
        ret, frame = cap.read()
        height, width = frame.shape[:2]
        if height > max_height:
            max_height = height
        if width > max_width:
            max_width = width
    print("{} is max height".format(max_height))
    print("{} is max widht".format(max_width))
    return (max_height, max_width)

def concat_caps_to_frame(cap_list, height, width):
    # Create blank frame large enough for the all streams
    output = np.zeros( (height, width, 3), dtype=np.uint8)
    # Capture frame-by-frame from each camera
    current_x = 0
    for cap in cap_list:
        ret, frame = cap.read()
        output[0:frame.shape[0], current_x:frame.shape[1] + current_x,:] = frame
        current_x += frame.shape[1]
    return output

def process_frame(frame):
    # reduce the frame to half size
    processed_frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
    # convert frame to grayscale
    processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
    
    return processed_frame

if __name__ == "__main__":
    main()
