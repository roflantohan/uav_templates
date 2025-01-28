import cv2
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

# Инициализация GStreamer
Gst.init(None)


def gstreamer_pipeline():
    return (
        "appsrc name=app  ! "
        "x264enc tune=zerolatency bitrate=500 speed-preset=ultrafast ! "
        "rtph264pay ! udpsink host=127.0.0.1 port=5000"
    )


# Создание пайплайна
pipeline = Gst.parse_launch(gstreamer_pipeline())
appsrc = pipeline.get_by_name("app")

# Настройка свойств appsrc
appsrc.set_property(
    "caps",
    Gst.Caps.from_string("video/x-raw,format=BGR,width=640,height=480,framerate=30/1"),
)
appsrc.set_property("block", True)
pipeline.set_state(Gst.State.PLAYING)

# Захват видео через OpenCV
cap = cv2.VideoCapture(0)  # Можно использовать другой источник видео


# Функция для передачи фреймов в GStreamer
def send_frame(frame):
    # Конвертация фрейма в GStreamer буфер
    data = frame.tobytes()
    buf = Gst.Buffer.new_allocate(None, len(data), None)
    buf.fill(0, data)
    buf.duration = Gst.util_uint64_scale_int(
        1, Gst.SECOND, 30
    )  # Задаем длительность кадра
    timestamp = appsrc.get_current_running_time()
    buf.pts = timestamp
    buf.dts = buf.pts
    buf.offset = timestamp

    # Отправка буфера в пайплайн
    appsrc.emit("push-buffer", buf)


# Основной цикл
try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Отправка фрейма через GStreamer
        send_frame(frame)

        # Отображение фрейма
        # # cv2.imshow("Frame", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
finally:
    # Завершение пайплайна и освобождение ресурсов
    appsrc.emit("end-of-stream")
    pipeline.set_state(Gst.State.NULL)
    cap.release()
    cv2.destroyAllWindows()
