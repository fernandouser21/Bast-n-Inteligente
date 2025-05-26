#Server
#Objetivo:  El objetivo práctico de este código es implementar
            #un sistema de medición de distancia con un sensor ultrasónico y activar
            #un buzzer de alerta cuando un objeto se aproxima a menos de 30 cm, variando
            #la frecuencia del sonido según la cercanía, lo cual es útil en aplicaciones
            #de detección de obstáculos o sistemas de asistencia de proximidad.
#Encargado de Entrega de Equipo: Barroso Vázquez Fernando
#Integrantes: Barroso Vázquez Fernando  - Cesar Ramses Avila Gutierrez

import machine  # Importa el módulo para controlar hardware como pines GPIO
import time     # Importa el módulo para gestionar retardos y tiempos

# Configuración de pines del sensor ultrasónico
TRIG = machine.Pin(26, machine.Pin.OUT)  # Pin de disparo del sensor ultrasónico
ECHO = machine.Pin(25, machine.Pin.IN)   # Pin de recepción del eco

# Configuración del pin del buzzer
BUZZER = machine.Pin(27, machine.Pin.OUT)  # Pin para activar/desactivar el buzzer

# Función para medir distancia usando el sensor ultrasónico, con manejo de timeout
def medir_distancia(timeout_us=100000):  # Timeout predeterminado de 100 milisegundos
    TRIG.off()
    time.sleep_us(2)     # Pulso corto de estabilización
    TRIG.on()
    time.sleep_us(10)    # Pulso de 10 microsegundos para disparar el sensor
    TRIG.off()
    
    # Espera a que el pin ECHO se active (inicio del eco), con control de timeout
    start = time.ticks_us()
    while not ECHO.value():
        if time.ticks_diff(time.ticks_us(), start) > timeout_us:
            return float('inf')  # Retorna infinito si no se detecta el inicio del eco
    
    # Mide cuánto tiempo permanece activo el pin ECHO
    time1 = time.ticks_us()
    while ECHO.value():
        if time.ticks_diff(time.ticks_us(), time1) > timeout_us:
            return float('inf')  # Retorna infinito si se excede el tiempo de respuesta
    
    time2 = time.ticks_us()
    duration = time.ticks_diff(time2, time1)  # Calcula duración del pulso de eco
    
    # Calcula la distancia en centímetros
    return duration * 340 / 2 / 10000  # Fórmula para calcular distancia con velocidad del sonido

# Función para activar el buzzer según la distancia medida
def alerta_proximidad():
    try:
        dist = medir_distancia()  # Obtiene la distancia
        print('Distancia: %.2f cm' % dist)  # Muestra la distancia por consola

        if dist <= 30:  # Si la distancia es menor o igual a 30 cm
            intervalo = int(dist * 50)  # Calcula el tiempo entre pitidos según la distancia
            BUZZER.on()
            time.sleep_ms(50)  # Sonido corto del buzzer
            BUZZER.off()
            time.sleep_ms(intervalo)  # Pausa según la proximidad
        else:
            BUZZER.off()  # Si no hay objeto cercano, mantener el buzzer apagado
            time.sleep_ms(300)  # Pausa general
    except Exception as e:
        print("Error:", e)
        BUZZER.off()  # Apaga el buzzer si ocurre un error

# Bucle principal protegido que ejecuta la alerta de proximidad de forma continua
def main():
    while True:
        alerta_proximidad()

# Verifica si este archivo es el programa principal a ejecutar
if __name__ == '__main__':  # (Corrige '_name_' a '__name__')
    main()
