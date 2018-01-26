# import the necessary packages
from __future__ import print_function
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import imutils
import time
import cv2


def main(args):
    # created a *threaded *video stream, allow the camera sensor to warmup,
    # and start the FPS counter
    print("[INFO] sampling THREADED frames from `picamera` module...")
    vs = PiVideoStream().start()
    time.sleep(2.0)
    fps = FPS().start()

    # loop over some frames...this time using the threaded stream
    while fps._numFrames < args["num_frames"]:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # check to see if the frame should be displayed to our screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

        # update the FPS counter
        fps.update()

    # stop the timer and display FPS information
    fps.stop()
    print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True,
                        help="path to output video file")
    parser.add_argument("-p", "--picamera", type=int, default=-1,
                        help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-f", "--fps", type=int, default=30,
                        help="FPS of output video")
    parser.add_argument("-c", "--codec", type=str, default="MJPG",
                        help="codec of output video")

    parser.add_argument("-n", "--num-frames", type=int, default=100,
                        help="# of frames to loop over for FPS test")
    parser.add_argument("-d", "--display", type=int, default=-1,
                        help="Whether or not frames should be displayed")

    args = vars(parser.parse_args())

    main(args)
