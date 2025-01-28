import cv2
import numpy as np
from src.libs.shared_memory import SharedMemory


class StreamUDP:
    def __init__(self, shmem: SharedMemory):
        self.shmem = shmem
        self.host = self.shmem.config["udp_host"]
        self.port = self.shmem.config["udp_port"]
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

    def wait_for_param(self):
        while True:
            self.width = self.shmem.read_dict("frame_width")
            self.height = self.shmem.read_dict("frame_height")
            if self.width and self.height:
                break

    def listen(self):
        self.wait_for_param()

        self.out = self.create_stream(self.host, self.port, self.width, self.height)
        # gray background
        self.frame = np.full((self.width, self.height, 3), 128, dtype=np.uint8)

        while True:
            if not self.shmem.is_empty("frame_out"):
                self.frame = self.shmem.get_queue("frame_out")
            self.out.write(self.frame)
