import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

image_size_X = 512
image_size_Y = 512

class LineDetection(object):
    # def camera_callback():
    #     pass

    def build_mask(self, image):
        """Build a trapezoidal ROI that blacks out everything outside the shape
        Source: https://www.geeksforgeeks.org/machine-learning/opencv-real-time-road-lane-detection/"""

        #maybe build a dynamic ROI as explained in MDPI paper?
        #print(f"Frame shape: {image.shape}, dtype: {image.dtype}")
        #build a mask from an image to limit the ROI
        mask = np.zeros_like(image)
        #choose white as the mask shape color
        ignore_mask_color = 255
        #create a shape for the mask
        rows, cols = image.shape[:2]
        bottom_left = [cols * 0.2, rows * 0.95]
        top_left = [cols * 0.35, rows * 0.15]
        bottom_right = [cols * 0.8, rows * 0.95]
        top_right = [cols * 0.65, rows * 0.15]
        vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
        #fill mask with white
        cv.fillPoly(mask, vertices, ignore_mask_color) 
        #bitwise AND to ignore everything outside the mask
        masked_img = cv.bitwise_and(image, mask)
        return masked_img
    
    def houghP_transform(self, image):
        """
        Determine and cut the region of interest in the input image.
        Parameter:
            image: grayscale image which should be an output from the edge detector
        Source: https://www.geeksforgeeks.org/machine-learning/opencv-real-time-road-lane-detection/    
        """
        # Distance resolution of the accumulator in pixels.
        rho = 1   
        # Angle resolution of the accumulator in radians.
        theta = np.pi/180    
        # Only lines that are greater than threshold will be returned.
        threshold = 20       
        # Line segments shorter than that are rejected.
        minLineLength = 65  
        # Maximum allowed gap between points on the same line to link them
        maxLineGap = 10     
        # function returns an array containing dimensions of straight lines 
        # appearing in the input image
        lines = cv.HoughLinesP(image, rho = rho, theta = theta, threshold = threshold,
                            minLineLength = minLineLength, maxLineGap = maxLineGap)
        return lines
    
    def average_slope_intercept(self, houghlines):
        """find the slope and intercept of each line, categorize into left/right
            and return the average left/right lines as slope+intercept list
        Source: https://www.geeksforgeeks.org/machine-learning/opencv-real-time-road-lane-detection/"""

        left_lines = []     #slope, intercept
        #left_angles = []
        left_weights = []   #length
        right_lines = []    #slope, intercept
        #right_angles = []
        right_weights = []  #length

        if houghlines is not None:
            for i, line in enumerate(houghlines):
                
                x1, y1, x2, y2 = line[0]

                if x1 == x2:        #ignore vertical line since perspective is slanted
                    continue
                    
                #find slope of line
                dy = (y2 - y1)
                dx = (x2 - x1)
                slope = dy/dx

                if(dy == 0):        #ignore horizontal lines. consider threshold value
                    continue

                #find intercept of line
                intercept = y1 - (slope * x1)
                
                #find length of line
                length = np.sqrt(((y2 - y1) ** 2) + (x2 - x1) ** 2)

                if(slope < 0):   #left line is neg slope
                    left_lines.append((slope, intercept))
                    left_weights.append(length)     #longer length = higher confidence
                else:
                    right_lines.append((slope, intercept))
                    right_weights.append(length)

            left_line_arr = np.array(left_lines)
            right_line_arr = np.array(right_lines)

            #find the average values of left & right lanes
            left_line_avg = np.dot(left_weights, left_line_arr) / np.sum(left_weights) if(len(left_weights)) else None
            right_line_avg = np.dot(right_weights, right_line_arr) / np.sum(right_weights) if(len(right_weights)) else None

                # if(dx < 0):     #left angle
                #     # convert radian to degree and extract angle
                #     l_angle = np.rad2deg(np.arctan2(dy, dx))
                #     left_angles.append(l_angle)
                # else:
                #     r_angle = np.rad2deg(np.arctan2(dy, dx))
                #     right_angles.append(r_angle)
                
                #draw detected line on camera feed
                #cv.line(image,(x1,y1),(x2,y2),(0,255,0),thickness=3)

            return left_line_avg, right_line_avg
        
        return None, None
    
    def line_coords(self, y1, y2, line):
        """
        Converts the slope and intercept of each line into pixel (x, y) coordinates.
            Parameters:
                y1: y-value of the line's starting point.
                y2: y-value of the line's end point.
                line: The slope and intercept of the line.
            Returns:
                Two tuples (x1, y1) and (x2, y2) which define a line
        Source: https://www.geeksforgeeks.org/machine-learning/opencv-real-time-road-lane-detection/
        """
        if line is None:
            return None
        slope, intercept = line

        x1 = int((y1 - intercept)/slope)
        x2 = int((y2 - intercept)/slope)
        y1 = int(y1)
        y2 = int(y2)
        return ((x1, y1), (x2, y2))
  
    def lane_lines(self, image, lines):
        """
        Create full length lines from pixel points.
            Parameters:
                image: The input test image.
                lines: The output lines from Hough Transform.
            Returns:
                left_line: The output left line in format (x1, y1) (x2, y2) 
                right_lane: The output right line, see above
        Source: https://www.geeksforgeeks.org/machine-learning/opencv-real-time-road-lane-detection/
        """

        left_lane, right_lane = self.average_slope_intercept(lines)
        y1 = 0.95 * image.shape[0]     #bottom of image (height)
        y2 = 0.4 * y1          #top of trapezoid ROI

        left_line  = self.line_coords(y1, y2, left_lane)
        right_line = self.line_coords(y1, y2, right_lane)

        #draw lane lines
        draw_lines = (left_line, right_line)
        for line in draw_lines:
            if line is not None:
                cv.line(image, line[0], line[1], [255, 0, 0], thickness=3)

        return left_line, right_line

    def desired_lane(self, left_lane, right_lane):
        """
        Get the arithmetic mean of the left and right lanes 
            Parameters:
                left_lane: The line respresenting the left edge in format (x1, y1) (x2, y2) 
                right_lane: The line respresenting the right edge in format (x1, y1) (x2, y2)
            Returns:
                middle_lane: A line in format (x1, y1) (x2, y2) that goes through the middle of the line
        """
        if left_lane is not None and right_lane is not None:
            # Average each endpoint of the left and right lanes
            (x1_l, y1_l), (x2_l, y2_l) = left_lane
            (x1_r, y1_r), (x2_r, y2_r) = right_lane
            middle_lane = (
                (int((x1_l + x1_r) / 2), int((y1_l + y1_r) / 2)),
                (int((x2_l + x2_r) / 2), int((y2_l + y2_r) / 2))
            )
            return middle_lane
        
        return None
    
    def draw_desired_lane(self, frame, lane):
        if frame is not None and lane is not None:
            # middle lane is expected to be a tuple: ((x1, y1), (x2, y2))
            (x1, y1), (x2, y2) = lane
            cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), thickness=3)

    def get_error(self, frame, desired_lane):
        """
        Calculates the error between the actual center of the frame and the middle of L/R detected edges.
        """
        
        #define the centerline
        width = frame.shape[1]
        frame_center = int(width / 2.0)

        if desired_lane is not None:
            center_mean = np.average(desired_lane)      #gives x value of center of desired lane
            error = center_mean - frame_center
            print("error is:", error)
            return error
        
        return 0

    def steer_to_line(self, left_avg, right_avg, image):
        #invert the angle since y down is positive
        #angle = 180 - angle if angle > 0 else -angle
        # angle
        #cv.putText(image, str(round(l_angle, 1)),(x1 , int((y1+y2)/2)), cv.FONT_HERSHEY_SIMPLEX, 1, color, 3) 
        
        #https://www.mdpi.com/2075-1702/10/1/10
        
        # M = cv.moments(image)

        # #calculate x, y coordinates of center
        # cX, cY = image_size_X / 2, image_size_Y / 2

        # if M["m00"] is not None:
        #     cX = int(M["m10"] / M["m00"])
        #     cY = int(M["m01"] / M["m00"])

        #draw centerline of image
        cv.line(image, (256, 0), (256, 512), (0, 0, 255), 1)

        if left_avg is None and right_avg is None:
            error = 0
            angle = 0
            print("No lanes found")
        else:
            middle_line = self.desired_lane(left_avg, right_avg)
            x1, y1, x2, y2 = middle_line
            self.draw_desired_lane(image, middle_line)

            error = self.get_error(image, middle_line)
            angle = 90 - np.rad2deg(np.arctan2(y2 - y1))
            print("Angle is:", angle)

        return angle, error, image
    
    def process_frame(self):
        # If the input is the camera, pass 0 instead of the video file 2=webcam (sometimes its 3, 4)
        #TODO: implement fix for checking which index corresponds to the webcam
        cap = cv.VideoCapture(0)
        if cap.isOpened() == False:
            print("Error in opening video stream or file")

        while(cap.isOpened()):

            ret, frame = cap.read()

            #resize image to 512x512 and apply mask
            resized_frame = cv.resize(frame, (512, 512), interpolation = cv.INTER_AREA)
            frame = self.build_mask(resized_frame)

            #convert to grayscale
            gray = cv.cvtColor(resized_frame,cv.COLOR_BGR2GRAY)

            #apply blur   other options: bilaterial filtering, gaussian blur
            #blur = cv.medianBlur(gray, 5)
            blur = cv.GaussianBlur(gray, (9, 9), 0)

            #transform to binary image
            th = cv.adaptiveThreshold(blur,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY,11,2)
            
            #overlay black box on screen to block out everything not thresholded
                #TODO: we can do this only if we threshold out a certain color (e.g. white)
                #make sure th gets overlayed on the black box
            #cv.rectangle(th, (0, 0), (256, 512), (0,0,0), -1)

            #detect edges using Canny detection
            edges = cv.Canny(th, 50, 200, apertureSize = 3)
            #select region of interest
            region = self.build_mask(edges)
            # apply HoughLines - returns an array of lines detected in the image.
            houghlines = self.houghP_transform(region)

            left_lane, right_lane = self.lane_lines(frame, houghlines)
            desired_lane = self.desired_lane(left_lane, right_lane)
            #display middle of line
            self.draw_desired_lane(frame, desired_lane)
            #self.lane_lines(frame, houghlines)
            self.get_error(frame, desired_lane)

            if ret:
                # Display camera feed
                cv.imshow('Camera feed',resized_frame)
                # Display the resulting frame
                cv.imshow('Frame',frame)
                # Display mask
                #cv.imshow('Mask', region)
                # Display thresholding
                #cv.imshow('Threshold',th)
                # Display Canny edges
                cv.imshow('Canny edges',edges)
                # Display HoughP lines
                plt.imshow(frame)

            # Press esc to exit
            if cv.waitKey(20) & 0xFF == 27:
                break
        cap.release()
        cv.destroyAllWindows()

if __name__ == '__main__':
    line_detection = LineDetection()
    line_detection.process_frame()

# #probabalistic hough line detector
# lines = cv.HoughLinesP(BinaryImage(Canny),distanceResolution,angleResolution,threshold,minLineLength=integer,maxLineGap=integer)
# for line in lines:
#     x1,y1,x2,y2 = line[0]
#     cv.line(image,(x1,y1),(x2,y2),(0,255,0),thickness)
