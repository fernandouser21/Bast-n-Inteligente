import machine
import time
import network
import socket
import urequests
import _thread
import gc

# Configuración Wi-Fi
SSID = 'iPhone'
PASSWORD = 'bandicoot234'

# Pines del sensor ultrasónico
TRIG = machine.Pin(26, machine.Pin.OUT)
ECHO = machine.Pin(25, machine.Pin.IN)

# Pin del buzzer
BUZZER = machine.Pin(27, machine.Pin.OUT)

# Dirección IP del servidor
SERVER_URL = 'http://172.20.10.3:8000/video'

# Cola de notificaciones simulada
notification_queue = []
MAX_QUEUE_SIZE = 5

# Procesador de notificaciones
def process_notifications():
    global notification_queue
    while True:
        if notification_queue:
            notification_queue.pop(0)  # Elimina la notificación más antigua
            try:
                urequests.get(SERVER_URL)
                print("Notificación enviada al servidor")
            except Exception as e:
                print("Error al notificar al servidor:", e)
        time.sleep(1)

# Servidor que escucha notificaciones desde el servidor Python
def servidor_local():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Servidor escuchando en", addr)

    while True:
        try:
            cl, addr = s.accept()
            cl.settimeout(2)
            print("Conexión desde", addr)

            try:
                cl.recv(512)
            except:
                pass  # Ignora errores de lectura

            cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nNotificado")

            BUZZER.on()
            time.sleep_ms(500)
            BUZZER.off()

            cl.close()
            gc.collect()
        except Exception as e:
            print("Error en servidor local:", e)

# Función principal
def main():
    global notification_queue
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        print("Conectando a WiFi...")
        time.sleep(1)

    print("WiFi conectado:", wlan.ifconfig())

    _thread.start_new_thread(servidor_local, ())
    _thread.start_new_thread(process_notifications, ())

    last_notification_time = 0
    notification_interval = 5  # segundos

    while True:
g        now = time.time()

        if now - last_notification_time >= notification_interval:
            if len(notification_queue) < MAX_QUEUE_SIZE:
                notification_queue.append("Notificación")
                print("Agregada notificación. Cola:", len(notification_queue))
            else:
                print("Cola llena. No se agregó notificación.")
            last_notification_time = now

        time.sleep(2)

if __name__ == '__main__':
    main()


