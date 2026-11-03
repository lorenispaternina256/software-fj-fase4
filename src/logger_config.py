"""
Configuración centralizada del registro de eventos (logging).

Todos los módulos piden su logger con ``obtener_logger(__name__)``. Los
mensajes se escriben en ``logs/sistema.log``, que es el ÚNICO archivo que usa
el sistema (los datos de negocio viven solo en memoria).

Niveles usados:
    * INFO    -> eventos normales (cliente registrado, reserva confirmada...).
    * WARNING -> operaciones rechazadas por reglas de negocio.
    * ERROR   -> excepciones capturadas.
"""

import logging
import os

# Carpeta donde se guardan los logs (relativa a la raíz del proyecto)
CARPETA_LOGS: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
# Ruta completa del archivo de logs
RUTA_LOG: str = os.path.join(CARPETA_LOGS, "sistema.log")
# Formato de cada línea: fecha | nivel | módulo | mensaje
FORMATO: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
# Nombre del logger raíz del proyecto; los demás cuelgan de él
NOMBRE_RAIZ: str = "software_fj"


def _configurar_raiz() -> logging.Logger:
    """
    Configura una sola vez el logger raíz del proyecto.

    Returns:
        El logger raíz ya configurado.
    """
    # Se obtiene (o crea) el logger raíz del proyecto
    raiz = logging.getLogger(NOMBRE_RAIZ)
    # Si ya tiene manejadores, ya fue configurado y no se duplica
    if raiz.handlers:
        return raiz
    # Se registra todo desde el nivel INFO hacia arriba
    raiz.setLevel(logging.INFO)
    # Se evita que los mensajes suban al logger raíz de Python (no se duplican)
    raiz.propagate = False
    # Objeto que da formato a cada línea del log
    formateador = logging.Formatter(FORMATO, datefmt="%Y-%m-%d %H:%M:%S")

    try:
        # Se crea la carpeta logs/ si no existe (exist_ok evita error si ya está)
        os.makedirs(CARPETA_LOGS, exist_ok=True)
        # Manejador que escribe en el archivo, en UTF-8 para soportar tildes
        manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    except OSError as error:
        # Si no se puede escribir en disco el sistema NO se detiene:
        # se usa la consola como respaldo para no perder los mensajes
        manejador = logging.StreamHandler()
        print(f"[AVISO] No se pudo crear el archivo de logs ({error}). "
              "Se usará la consola.")

    # Se asigna el formato al manejador elegido
    manejador.setFormatter(formateador)
    # Se conecta el manejador al logger raíz
    raiz.addHandler(manejador)
    return raiz


def obtener_logger(nombre: str) -> logging.Logger:
    """
    Devuelve un logger hijo del logger raíz del proyecto.

    Args:
        nombre: normalmente ``__name__`` del módulo que lo pide.

    Returns:
        Logger listo para usar.
    """
    # Se garantiza que la configuración exista antes de entregar el logger
    _configurar_raiz()
    # Se crea un logger hijo: "software_fj.<nombre>"
    return logging.getLogger(f"{NOMBRE_RAIZ}.{nombre}")


def cerrar_logger() -> None:
    """
    Vacía y cierra los manejadores del log al terminar el programa.

    Usa ``try/finally``: aunque falle el ``flush`` de un manejador, el
    ``finally`` garantiza que el manejador se cierre y se retire.
    """
    # Se obtiene el logger raíz del proyecto
    raiz = logging.getLogger(NOMBRE_RAIZ)
    # Se recorre una copia de la lista porque se modificará dentro del ciclo
    for manejador in list(raiz.handlers):
        try:
            # Se fuerza la escritura de lo pendiente en el archivo
            manejador.flush()
        finally:
            # Esto se ejecuta SIEMPRE, haya fallado o no el flush
            manejador.close()
            raiz.removeHandler(manejador)
