import cv2
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GObject
import time


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(SensorFactory, self).__init__(**properties)
        # gst_str = "gst-launch-1.0 rtspsrc location=rtsp://0.0.0.0:8554/main.264 latency=0 buffer-mode=auto protocols=udp ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1"
        # self.cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        self.cap = cv2.VideoCapture(0)
        self.number_frames = 0
        self.fps = 30
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = (
            "appsrc name=source is-live=true block=true format=GST_FORMAT_TIME "
            "caps=video/x-raw,format=BGR,width=1280,height=720,framerate={}/1 "
            "! videoconvert ! video/x-raw,format=I420 "
            "! x264enc speed-preset=ultrafast tune=zerolatency "
            "! rtph264pay config-interval=1 name=pay0 pt=96".format(self.fps)
        )
        self.time_start = time.time()

    def on_need_data(self, src, lenght):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                data = frame.tostring()
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                buf.offset = timestamp
                self.number_frames += 1
                retval = src.emit("push-buffer", buf)
                print(
                    "pushed buffer, frame {}, duration {} ns, durations {} s".format(
                        self.number_frames, self.duration, self.duration / Gst.SECOND
                    )
                )
                if retval != Gst.FlowReturn.OK:
                    print(retval)

                print("Frame received: ", time.time() - self.time_start)
                self.time_start = time.time()

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name("source")
        appsrc.connect("need-data", self.on_need_data)


class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = SensorFactory()
        self.factory.set_shared(True)
        self.get_mount_points().add_factory("/stream", self.factory)
        self.attach(None)


def listen():
    GObject.threads_init()
    Gst.init(None)

    server = GstServer()

    loop = GObject.MainLoop()
    loop.run()


listen()


# import gi
# import numpy as np

# gi.require_version("Gst", "1.0")
# gi.require_version("GstRtspServer", "1.0")
# from gi.repository import Gst, GstRtspServer, GObject

# from src.libs.shared_memory import SharedMemory
# from src.cv_process.osd import OSDPrinter


# class SensorFactory(GstRtspServer.RTSPMediaFactory):
#     def __init__(self, shmem: SharedMemory, **properties):
#         super(SensorFactory, self).__init__(**properties)
#         self.shmem = shmem
#         self.osd = OSDPrinter(shmem)
#         self.number_frames = 0
#         self.fps = 30
#         self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
#         self.width = self.shmem.read_dict("frame_width")
#         self.height = self.shmem.read_dict("frame_height")
#         self.launch_string = (
#             f"appsrc name=source is-live=true block=true format=GST_FORMAT_TIME "
#             f"caps=video/x-raw,format=BGR,width={self.width},height={self.height},framerate={self.fps}/1 "
#             f"! videoconvert ! video/x-raw,format=I420 "
#             f"! x264enc speed-preset=ultrafast tune=zerolatency "
#             f"! rtph264pay config-interval=1 name=pay0 pt=96"
#         )
#         self.frame = np.full(
#             (self.width, self.height, 3), 128, dtype=np.uint8
#         )  # gray background

#     def on_need_data(self, src, length):
#         if not self.shmem.is_empty("frame_out"):
#             self.frame = self.shmem.get_queue("frame_out")
#             self.osd.put_osd(self.frame)

#         data = self.frame.tobytes()
#         buf = Gst.Buffer.new_allocate(None, len(data), None)
#         buf.fill(0, data)
#         buf.duration = self.duration
#         timestamp = self.number_frames * self.duration
#         buf.pts = buf.dts = int(timestamp)
#         buf.offset = timestamp
#         self.number_frames += 1
#         retval = src.emit("push-buffer", buf)
#         # print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
#         #                                                                         self.duration,
#         #                                                                         self.duration / Gst.SECOND))
#         if retval != Gst.FlowReturn.OK:
#             print(retval)

#     def do_create_element(self, url):
#         return Gst.parse_launch(self.launch_string)

#     def do_configure(self, rtsp_media):
#         self.number_frames = 0
#         appsrc = rtsp_media.get_element().get_child_by_name("source")
#         appsrc.connect("need-data", self.on_need_data)


# class GstServer(GstRtspServer.RTSPServer):
#     def __init__(self, shmem: SharedMemory, **properties):
#         super(GstServer, self).__init__(**properties)
#         self.factory = SensorFactory(shmem)
#         self.factory.set_shared(True)
#         self.get_mount_points().add_factory("/stream", self.factory)
#         self.attach(None)


# class ServerRTSP:

#     def __init__(self, shmem: SharedMemory):
#         self.shmem = shmem

#     def wait_for_param(self):
#         while True:
#             w = self.shmem.read_dict("frame_width")
#             h = self.shmem.read_dict("frame_height")
#             if w and h:
#                 break

#     def listen(self):
#         self.wait_for_param()
#         # GObject.threads_init()
#         Gst.init(None)

#         GstServer(self.shmem)

#         loop = GObject.MainLoop()
#         loop.run()
