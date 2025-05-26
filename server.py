#Server
#Objetivo:  Este proyecto sirve como base para sistemas de visión por
            #computadora aplicados a IoT, combinando detección de rostros,
            #comunicación en red y control remoto. Es escalable y puede adaptarse
            #a diferentes casos de uso en seguridad, automatización o análisis de datos.
#Encargado de Entrega de Equipo: Barroso Vázquez Fernando
#Integrantes: Barroso Vázquez Fernando  - Cesar Ramses Avila Gutierrez


"""
Sistema de Detección de Rostros con Flask y OpenCV

Este sistema proporciona:
1. Streaming de video desde una cámara IP
2. Detección de rostros en tiempo real usando Haar Cascade
3. Notificaciones a un dispositivo ESP32 cuando se detectan rostros
4. Endpoints REST para controlar el servicio
"""

from flask import Flask, request
import cv2
import threading
import requests
import time
import queue

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de URLs (deberían ser variables de entorno en producción)
CAMERA_URL = 'http://172.20.10.10:4747/video'  # URL del stream de la cámara
ESP32_NOTIFY_URL = 'http://172.20.10.14:8080/notify'  # Endpoint de notificación del ESP32

# Variables de estado globales
streaming = False  # Controla si el streaming está activo
lock = threading.Lock()  # Semaforo para control de concurrencia

# Sistema de cola para notificaciones con cooldown
notification_queue = queue.Queue()
NOTIFICATION_COOLDOWN = 3  # Tiempo mínimo entre notificaciones (segundos)

def notify_worker():
    """
    Hilo worker que maneja las notificaciones al ESP32.
    
    Funcionamiento:
    - Espera en la cola de notificaciones
    - Cuando recibe una notificación, hace HTTP GET al ESP32
    - Espera el tiempo de cooldown antes de aceptar nuevas notificaciones
    - Maneja errores de conexión
    """
    while True:
        notification_queue.get()  # Espera bloqueante por una notificación
        try:
            # Intenta notificar al ESP32
            response = requests.get(ESP32_NOTIFY_URL, timeout=2)
            print(f"Notificación enviada al ESP32. Respuesta: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error al notificar al ESP32: {e}")
        
        # Espera el cooldown antes de procesar la siguiente notificación
        time.sleep(NOTIFICATION_COOLDOWN)
        notification_queue.task_done()

# Inicialización del hilo de notificaciones (daemon=True para que termine con el programa)
notifier_thread = threading.Thread(target=notify_worker, daemon=True)
notifier_thread.start()

def detect_and_stream():
    """
    Función principal que maneja:
    - Captura del stream de video
    - Detección de rostros usando Haar Cascade
    - Visualización del video con detección
    - Notificación de rostros detectados
    
    Usa variables globales:
    - streaming: para controlar el bucle principal
    - notification_queue: para enviar notificaciones
    """
    global streaming
    
    # Inicialización de captura de video
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print("Error: No se pudo abrir el stream de la cámara")
        return

    # Carga el clasificador Haar Cascade para detección de rostros
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    face_detected = False  # Bandera para control de notificaciones

    # Bucle principal de procesamiento
    while streaming:
        # Captura frame por frame
        ret, frame = cap.read()
        if not ret:
            continue  # Si hay error, continuar con siguiente frame

        # Preprocesamiento para detección (convertir a escala de grises)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detección de rostros
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

        # Lógica de notificación (solo cuando aparece un nuevo rostro)
        if len(faces) > 0 and not face_detected:
            face_detected = True
            notification_queue.put(True)  # Encolar notificación
            print("Rostro detectado - Notificación encolada")
        
        # Resetear bandera si no hay rostros
        if len(faces) == 0:
            face_detected = False

        # Dibujar rectángulos alrededor de los rostros detectados
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Mostrar el frame resultante
        cv2.imshow('Detección de Rostros en Tiempo Real', frame)
        
        # Salir con ESC
        if cv2.waitKey(1) == 27:
            break

    # Liberación de recursos al terminar
    cap.release()
    cv2.destroyAllWindows()
    print("Streaming y detección detenidos")

# Endpoints de la API Flask
@app.route('/video', methods=['GET'])
def start_stream():
    """
    Endpoint para iniciar el streaming con detección
    
    Returns:
        tuple: (mensaje, código HTTP)
    """
    global streaming
    with lock:  # Bloqueo para evitar condiciones de carrera
        if not streaming:
            streaming = True
            # Iniciar hilo de detección
            threading.Thread(target=detect_and_stream, daemon=True).start()
            return "Streaming con detección iniciado", 200
        return "El streaming ya está en ejecución", 200

@app.route('/stop', methods=['GET'])
def stop_stream():
    """
    Endpoint para detener el streaming
    
    Returns:
        tuple: (mensaje, código HTTP)
    """
    global streaming
    with lock:
        streaming = False
        return "Streaming detenido", 200

# Punto de entrada principal
if __name__ == '__main__':
    # Ejecutar la aplicación en todas las interfaces, puerto 8000
    app.run(host='0.0.0.0', port=8000, debug=True)