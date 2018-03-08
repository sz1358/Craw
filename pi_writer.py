# import the necessary packages
from imutils.video.pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
from Xlib.display import Display
from Xlib import X
from threading import Thread
from queue import Queue
import argparse
import imutils
import time
import cv2
import os

q = Queue()
out_name = "result"
buffer_name = "temp"


def main(args):
    # created a *threaded *video stream, allow the camera sensor to warmup,
    # and start the FPS counter
    print("[INFO] warming up camera...")
    vs = PiVideoStream().start()
    time.sleep(2.0)

    # initialize the FourCC, video writer, dimensions of the frame, and
    # zeros array
    fourcc = cv2.VideoWriter_fourcc(*args["codec"])
    writer = None
    (h, w) = (None, None)
    length = args["length"]
    temp = list()
    counter = 0
    timeframe = 0
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    params = {
        "output": args["output"],
        "length": length,
        "fps": args["fps"],
        "idx": 0
    }

    tempfile = os.path.join(args["output"], buffer_name)
    # loop over some frames...this time using the threaded stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        if writer is None:
            # store the image dimensions, initialzie the video writer,
            # and construct the zeros array
            (h, w) = frame.shape[:2]
            writer = cv2.VideoWriter(tempfile + "_" + str(timeframe) + ".avi",
                                     fourcc, args["fps"], (w, h), True)
            params["writer"] = writer
            # cv2.setMouseCallback("Frame", click, params)

        temp.append(frame)
        counter += 1
        params["counter"] = counter
        params["temp"] = temp
        params["frame"] = frame
        if counter >= args["fps"]:
            for img in temp:
                writer.write(img)
            temp = list()
            counter = 0
            timeframe = (timeframe + 1) % length
            params["timeframe"] = timeframe
            print(writer)
            print(tempfile + "_" + str(timeframe) + ".avi")
            writer.release()
            writer = cv2.VideoWriter(tempfile + "_" + str(timeframe) + ".avi",
                                     fourcc, args["fps"], (w, h), True)

        if not q.empty():
            click(params)
            q.get()

        # check to see if the frame should be displayed to our screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)

        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            writer.release()
            break

    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    vs.stop()
    print("[INFO] done")


def watcher(display):
    while True:
        start = time.time()
        event = display.next_event()
        if event.type == X.ButtonPress and event.detail == 1:
            if time.time() - start > 5:
                q.put(1)
                print(q.empty())


def click(param):
    if param["counter"] != param["fps"] - 1 and param["writer"] is not None:
        for img in param["temp"]:
            param["writer"].write(img)
        for i in range(len(param["temp"]), param["fps"]):
            param["writer"].write(param["frame"])
    param["writer"].release()
    summary(param["output"], param["timeframe"], param["length"])


def summary(prefix, timeframe, length):
    print("[INFO] saving...")
    txt = open(prefix + ".txt", "w")
    for i in range(length - 1, -1, -1):
        idx = (length + timeframe - i) % length if i > timeframe else (timeframe - i) % length
        txt.write("file '" + prefix + "_" + str(idx) + ".avi'\n")
    txt.close()
    os.system("ffmpeg -y -f concat -safe 0 -i %s.txt -c copy %s.avi" % (prefix, out_name))


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
    parser.add_argument("-l", "--length", type=int, default=30,
                        help="length of seconds of summary")
    parser.add_argument("-d", "--display", type=int, default=-1,
                        help="Whether or not frames should be displayed")

    arg = vars(parser.parse_args())

    display = Display(':0')
    root = display.screen().root
    root.grab_pointer(True, X.ButtonPressMask | X.ButtonReleaseMask, X.GrabModeAsync,
                      X.GrabModeAsync, 0, 0, X.CurrentTime)
    watcher_thread = Thread(target=watcher, args=(display, ))
    main_thread = Thread(target=main, args=(arg, ))
    watcher_thread.start()
    main_thread.start()

