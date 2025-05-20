from flask import Flask, request
import cv2
import threading
import requests
import time
import queue

app = Flask(__name__)

CAMERA_URL = 'http://172.20.10.10:4747/video'
ESP32_NOTIFY_URL = 'http://172.20.10.14:8080/notify'

streaming = False
lock = threading.Lock()

# Notificación controlada
notification_queue = queue.Queue()
NOTIFICATION_COOLDOWN = 3  # segundos

def notify_worker():
    while True:
        notification_queue.get()  # Espera por una tarea
        try:
            requests.get(ESP32_NOTIFY_URL, timeout=2)
            print("Notificación enviada al ESP32.")
        except requests.RequestException as e:
            print(f"Error al notificar al ESP32: {e}")
        time.sleep(NOTIFICATION_COOLDOWN)
        notification_queue.task_done()

# Lanza el hilo de notificación único
notifier_thread = threading.Thread(target=notify_worker, daemon=True)
notifier_thread.start()

def detect_and_stream():
    global streaming
    cap = cv2.VideoCapture(CAMERA_URL)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    if not cap.isOpened():
        print("Error abriendo la cámara.")
        return

    face_detected = False

    while streaming:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) > 0 and not face_detected:
            face_detected = True
            notification_queue.put(True)

        if len(faces) == 0:
            face_detected = False  # Reset para detectar nuevo rostro

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        cv2.imshow('Stream con Detección', frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Stream detenido.")

@app.route('/video', methods=['GET'])
def start_stream():
    global streaming
    with lock:
        if not streaming:
            streaming = True
            threading.Thread(target=detect_and_stream, daemon=True).start()
    return "Streaming iniciado", 200

@app.route('/stop', methods=['GET'])
def stop_stream():
    global streaming
    with lock:
        streaming = False
    return "Streaming detenido", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
