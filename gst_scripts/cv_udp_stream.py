# Need to compile OpenCV with GStreamer support !

import cv2
import numpy as np

class StreamUDP:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.out: cv2.VideoWriter = None

        self.width = None
        self.height = None
        self.frame = None

    def create_stream(self, host, port, w, h, fps=60):
        gst_pipeline = (
            f"appsrc ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency ! "
            f"rtph264pay ! udpsink host={host} port={port}"
        )
        return cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, fps, (w, h), True)
    
    def set_video_param(self, w, h):
        self.width = w
        self.height = h
        # gray background
        self.frame = np.full((self.width, self.height, 3), 128, dtype=np.uint8)

    def set_frame(self, frame):
        self.frame = frame

    def send_frame(self):
        self.out.write(self.frame)
