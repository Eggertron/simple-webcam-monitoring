import cv2

class MotionDetectorContour:
    def __init__(self,ceil=15):
        self.ceil = ceil
        self.url = "http://192.168.50.238:8080/video"
        self.capture = cv2.CaptureFromCAM(url)
        cv2.NamedWindow("Target", 1)

    def run(self):
        # Capture first frame to get size
        frame = cv2.QueryFrame(self.capture)
        frame_size = cv2.GetSize(frame)

        width = frame.width
        height = frame.height
        surface = width * height #Surface area of the image
        cursurface = 0 #Hold the current surface that have changed

        grey_image = cv2.CreateImage(cv2.GetSize(frame), cv2.IPL_DEPTH_8U, 1)
        moving_average = cv2.CreateImage(cv2.GetSize(frame), cv2.IPL_DEPTH_32F, 3)
        difference = None

        while True:
            color_image = cv2.QueryFrame(self.capture)

            cv2.Smooth(color_image, color_image, cv2.CV_GAUSSIAN, 3, 0) #Remove false positives

            if not difference: #For the first time put values in difference, temp and moving_average
                difference = cv2.CloneImage(color_image)
                temp = cv2.CloneImage(color_image)
                cv2.ConvertScale(color_image, moving_average, 1.0, 0.0)
            else:
                cv2.RunningAvg(color_image, moving_average, 0.020, None) #Compute the average

            # Convert the scale of the moving average.
            cv2.ConvertScale(moving_average, temp, 1.0, 0.0)

            # Minus the current frame from the moving average.
            cv2.AbsDiff(color_image, temp, difference)

            #Convert the image so that it can be thresholded
            cv2.CvtColor(difference, grey_image, cv2.CV_RGB2GRAY)
            cv2.Threshold(grey_image, grey_image, 70, 255, cv2.CV_THRESH_BINARY)

            cv2.Dilate(grey_image, grey_image, None, 18) #to get object blobs
            cv2.Erode(grey_image, grey_image, None, 10)

            # Find contours
            storage = cv2.CreateMemStorage(0)
            contours = cv2.FindContours(grey_image, storage, cv2.CV_RETR_EXTERNAL, cv2.CV_CHAIN_APPROX_SIMPLE)

            backcontours = contours #Save contours

            while contours: #For all contours compute the area
                cursurface += cv2.ContourArea(contours)
                contours = contours.h_next()

            avg = (cursurface*100)/surface #Calculate the average of contour area on the total size
            if avg > self.ceil:
                print ("Something is moving !")
            #print avg,"%"
            cursurface = 0 #Put back the current surface to 0

            #Draw the contours on the image
            _red =  (0, 0, 255); #Red for external contours
            _green =  (0, 255, 0);# Gren internal contours
            levels=1 #1 contours drawn, 2 internal contours as well, 3 ...
            cv2.DrawContours (color_image, backcontours,  _red, _green, levels, 2, cv2.CV_FILLED)

            cv2.ShowImage("Target", color_image)

            # Listen for ESC or ENTER key
            c = cv2.WaitKey(7) % 0x100
            if c == 27 or c == 10:
                break

if __name__=="__main__":
    t = MotionDetectorContour()
    t.run()
