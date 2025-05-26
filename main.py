#Main
#Objetivo:  El objetivo práctico de este código es implementar un sistema
            #embebido que se conecta a una red Wi-Fi, escucha peticiones desde un servidor
            #local a través del puerto 8080 y, al recibir una notificación, activa un buzzer
            #como alerta y envía una solicitud HTTP a un servidor remoto, simulando así un
            #mecanismo de monitoreo y respuesta en tiempo real útil para aplicaciones de seguridad
            #o control remoto.
#Encargado de Entrega de Equipo: Barroso Vázquez Fernando
#Integrantes: Barroso Vázquez Fernando  - Cesar Ramses Avila Gutierrez

import machine  # Módulo para controlar pines y hardware
import time     # Módulo para gestionar tiempos y retardos
import network  # Módulo para conectividad Wi-Fi
import socket   # Módulo para manejar conexiones de red
import urequests  # Módulo para hacer peticiones HTTP
import _thread    # Módulo para ejecutar hilos (multitarea)
import gc         # Módulo de recolección de basura (memoria)

# Configuración de red Wi-Fi
SSID = 'iPhone'  # Nombre de la red Wi-Fi
PASSWORD = 'bandicoot234'  # Contraseña del Wi-Fi

# Configuración de pines del sensor ultrasónico
TRIG = machine.Pin(26, machine.Pin.OUT)  # Pin de disparo del sensor
ECHO = machine.Pin(25, machine.Pin.IN)   # Pin de eco del sensor

# Pin para controlar el buzzer
BUZZER = machine.Pin(27, machine.Pin.OUT)  # Pin conectado al zumbador

# URL del servidor al que se notificará
SERVER_URL = 'http://172.20.10.3:8000/video'

# Cola de notificaciones simulada
notification_queue = []        # Lista que almacena las notificaciones pendientes
MAX_QUEUE_SIZE = 5             # Tamaño máximo de la cola

# Hilo que procesa las notificaciones en segundo plano
def process_notifications():
    global notification_queue
    while True:
        if notification_queue:
            notification_queue.pop(0)  # Elimina la notificación más antigua
            try:
                urequests.get(SERVER_URL)  # Envía solicitud al servidor
                print("Notificación enviada al servidor")
            except Exception as e:
                print("Error al notificar al servidor:", e)
        time.sleep(1)  # Espera un segundo antes de revisar de nuevo

# Servidor local que escucha en el puerto 8080
def servidor_local():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]  # Dirección IP y puerto
    s = socket.socket()  # Crea un socket de red
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reutilizar la dirección
    s.bind(addr)  # Enlaza el socket a la dirección
    s.listen(1)   # Comienza a escuchar conexiones entrantes
    print("Servidor escuchando en", addr)

    while True:
        try:
            cl, addr = s.accept()  # Acepta una conexión entrante
            cl.settimeout(2)       # Tiempo de espera para la conexión
            print("Conexión desde", addr)

            try:
                cl.recv(512)  # Intenta recibir datos del cliente (no se usan)
            except:
                pass  # Ignora errores si no se reciben datos

            # Envía una respuesta simple al cliente
            cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nNotificado")

            # Activa el buzzer brevemente como señal de notificación
            BUZZER.on()
            time.sleep_ms(500)
            BUZZER.off()

            cl.close()  # Cierra la conexión
            gc.collect()  # Limpia memoria basura
        except Exception as e:
            print("Error en servidor local:", e)

# Función principal del programa
def main():
    global notification_queue

    # Conexión a red Wi-Fi
    wlan = network.WLAN(network.STA_IF)  # Activa interfaz de estación
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)  # Conecta a la red

    # Espera hasta que esté conectado
    while not wlan.isconnected():
        print("Conectando a WiFi...")
        time.sleep(1)

    print("WiFi conectado:", wlan.ifconfig())  # Imprime dirección IP

    # Inicia los hilos: servidor local y procesador de notificaciones
    _thread.start_new_thread(servidor_local, ())
    _thread.start_new_thread(process_notifications, ())

    last_notification_time = 0
    notification_interval = 5  # Intervalo entre notificaciones (en segundos)

    while True:
        now = time.time()  # Tiempo actual en segundos desde el arranque

        # Verifica si ha pasado el intervalo definido para enviar una notificación
        if now - last_notification_time >= notification_interval:
            if len(notification_queue) < MAX_QUEUE_SIZE:
                # Si hay espacio en la cola, agrega una notificación
                notification_queue.append("Notificación")
                print("Agregada notificación. Cola:", len(notification_queue))
            else:
                print("Cola llena. No se agregó notificación.")
            last_notification_time = now  # Actualiza el tiempo de última notificación

        time.sleep(2)  # Espera antes de la siguiente iteración

# Punto de entrada del programa
if __name__ == '__main__':
    main()



