import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GObject

Gst.init(None)


class RTSPServer(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        super(RTSPServer, self).__init__()
        self.set_launch(
            "( autovideosrc ! video/x-raw,width=640,height=480,framerate=30/1 ! videoconvert ! x264enc tune=zerolatency bitrate=1000  speed-preset=ultrafast ! rtph264pay name=pay0 pt=96 )"
        )


class Server:
    def __init__(self):
        self.port = "8554"
        self.path = "/main.264"

        self.server = GstRtspServer.RTSPServer()
        self.server.set_service(self.port)
        factory = RTSPServer()
        factory.set_shared(True)
        mount_points = self.server.get_mount_points()
        mount_points.add_factory(self.path, factory)
        self.server.attach(None)
        print(f"RTSP server is running at rtsp://0.0.0.0:{self.port}{self.path}")


if __name__ == "__main__":
    loop = GObject.MainLoop()
    server = Server()
    loop.run()
