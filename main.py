"""
Punto de entrada del Sistema Integral de Gestión de Software FJ.

Ejecuta una secuencia de simulaciones con operaciones válidas e inválidas
para demostrar que el sistema sigue funcionando aunque ocurran errores.
Todos los eventos y errores quedan registrados en ``logs/sistema.log``.

Ejecución:
    python main.py
"""

import sys

from src.excepciones import CalculoInconsistenteError, SoftwareFJError
from src.logger_config import RUTA_LOG, cerrar_logger, obtener_logger
from src.sistema import SistemaGestion

# Logger del programa principal
logger = obtener_logger("main")


def titulo(numero: int, texto: str) -> None:
    """Imprime el encabezado de una simulación y lo registra en el log."""
    print(f"\n[{numero:02d}] {texto}")
    logger.info("=== Simulación %d: %s ===", numero, texto)


def seccion(texto: str) -> None:
    """Imprime un separador de sección."""
    print("\n" + "=" * 72 + f"\n{texto}\n" + "=" * 72)


def simular_clientes(sistema: SistemaGestion) -> None:
    """Simulaciones 1 a 5: registros válidos e inválidos de clientes."""
    seccion("CLIENTES")
    titulo(1, "Registrar cliente válido (Ana)")
    sistema.registrar_cliente("Ana Gómez", "1012345678", "ana@mail.com",
                              "3001234567")

    titulo(2, "Registrar otro cliente válido (Carlos)")
    sistema.registrar_cliente("Carlos Pérez", "79856412", "carlos.perez@empresa.co",
                              "3159876543")

    titulo(3, "Registrar cliente con correo inválido ('ana@')")
    sistema.registrar_cliente("Laura Ruiz", "1098765432", "ana@", "3204567890")

    titulo(4, "Registrar cliente con documento con letras")
    sistema.registrar_cliente("Pedro Díaz", "10A2345B", "pedro@mail.com",
                              "3101112233")

    titulo(5, "Registrar cliente con parámetro faltante (correo = None)")
    sistema.registrar_cliente("María López", "52123456", None, "3112223344")

    titulo(6, "Registrar cliente con teléfono con letras (error encadenado)")
    sistema.registrar_cliente("Sofía Mora", "1023456789", "sofia@mail.com",
                              "300ABC4567")

    titulo(7, "Registrar cliente con documento duplicado")
    sistema.registrar_cliente("Ana Duplicada", "1012345678", "otra@mail.com",
                              "3009998877")


def simular_servicios(sistema: SistemaGestion) -> None:
    """Simulaciones de creación correcta e incorrecta de servicios."""
    seccion("SERVICIOS")
    titulo(8, "Crear servicio ReservaSala válido")
    sistema.crear_servicio("sala", nombre="Sala Innovación", tarifa_base=50000,
                           capacidad=10, tiene_proyector=True)

    titulo(9, "Crear servicio AlquilerEquipo válido")
    sistema.crear_servicio("equipo", nombre="Portátiles Dell", tarifa_base=80000,
                           tipo_equipo="Portátil", cantidad_disponible=5)

    titulo(10, "Crear servicio AsesoriaEspecializada válido")
    sistema.crear_servicio("asesoria", nombre="Asesoría Ciberseguridad",
                           tarifa_base=120000, area="Ciberseguridad",
                           nivel_experto="senior")

    titulo(11, "Crear servicio con tarifa negativa")
    sistema.crear_servicio("sala", nombre="Sala Barata", tarifa_base=-1000,
                           capacidad=4)

    titulo(12, "Crear asesoría con nivel de experto inexistente")
    sistema.crear_servicio("asesoria", nombre="Asesoría Cloud",
                           tarifa_base=100000, area="Nube", nivel_experto="master")

    titulo(13, "Crear servicio con parámetro faltante (error encadenado)")
    sistema.crear_servicio("equipo", nombre="Video Beam", tarifa_base=40000)

    titulo(14, "Crear un segundo servicio de sala (quedará no disponible)")
    sistema.crear_servicio("sala", nombre="Sala Auditorio", tarifa_base=200000,
                           capacidad=80, tiene_proyector=True)


def simular_reservas(sistema: SistemaGestion) -> None:
    """Simulaciones de reservas exitosas y fallidas."""
    seccion("RESERVAS")
    titulo(15, "Reserva válida de sala: crear, confirmar y procesar con IVA 19 %")
    reserva = sistema.crear_reserva("1012345678", "Sala Innovación", 3, personas=8)
    sistema.confirmar_reserva(reserva)
    sistema.procesar_reserva(reserva, impuesto=19)

    titulo(16, "Reservar un servicio NO disponible")
    sistema.cambiar_disponibilidad("Sala Auditorio", False)
    sistema.crear_reserva("79856412", "Sala Auditorio", 2, personas=50)

    titulo(17, "Reserva con duración 0")
    sistema.crear_reserva("79856412", "Asesoría Ciberseguridad", 0)

    titulo(18, "Reserva con duración negativa")
    sistema.crear_reserva("79856412", "Portátiles Dell", -2)

    titulo(19, "Reserva para un cliente inexistente")
    sistema.crear_reserva("999999999", "Sala Innovación", 2)

    titulo(20, "Reserva de sala que supera la capacidad (error encadenado)")
    sistema.crear_reserva("1012345678", "Sala Innovación", 2, personas=25)

    titulo(21, "Alquilar más equipos de los disponibles")
    sistema.crear_reserva("79856412", "Portátiles Dell", 2, cantidad=10)

    titulo(22, "Cancelar una reserva ya cancelada")
    reserva_cancelar = sistema.crear_reserva("79856412", "Portátiles Dell", 3,
                                             cantidad=2)
    sistema.cancelar_reserva(reserva_cancelar)
    sistema.cancelar_reserva(reserva_cancelar)

    titulo(23, "Procesar con descuento del 150 % (cálculo inconsistente encadenado)")
    reserva_desc = sistema.crear_reserva("79856412", "Asesoría Ciberseguridad", 2)
    sistema.confirmar_reserva(reserva_desc)
    sistema.procesar_reserva(reserva_desc, impuesto=19, descuento=150)

    titulo(24, "Misma reserva con descuento válido del 10 % + IVA → procesada")
    sistema.procesar_reserva(reserva_desc, impuesto=19, descuento=10)

    titulo(25, "Confirmar una reserva ya procesada")
    sistema.confirmar_reserva(reserva_desc)

    titulo(26, "Procesar una reserva que sigue pendiente (sin confirmar)")
    reserva_pend = sistema.crear_reserva("1012345678", "Portátiles Dell", 1)
    sistema.procesar_reserva(reserva_pend)


def demostrar_polimorfismo(sistema: SistemaGestion) -> None:
    """Recorre los servicios llamando los mismos métodos (polimorfismo)."""
    seccion("POLIMORFISMO: mismos métodos, distinto comportamiento")
    for servicio in sistema.listar_servicios():
        # describir() y calcular_costo() se resuelven según la clase real
        print(f" • {servicio.describir()}")
        try:
            costo = servicio.calcular_costo(2)
        except SoftwareFJError as error:
            logger.error("Polimorfismo - %s: %s", servicio.nombre, error)
            print(f"     Costo por 2 unidades de tiempo: no calculable ({error})")
        else:
            print(f"     Costo por 2 unidades de tiempo: ${costo:,.2f}")


def demostrar_sobrecarga(sistema: SistemaGestion) -> None:
    """Muestra las variantes 'sobrecargadas' del cálculo de costo."""
    seccion("SOBRECARGA SIMULADA: variantes de calcular_costo")
    asesoria = sistema.buscar_servicio("Asesoría Ciberseguridad")
    if asesoria is None:
        print("   No se encontró la asesoría para la demostración")
        return
    variantes = [
        ("Costo base (sin extras)", lambda: asesoria.calcular_costo(2)),
        ("Con IVA 19 %", lambda: asesoria.calcular_costo_con_impuesto(2)),
        ("Con descuento 20 %", lambda: asesoria.calcular_costo_con_descuento(2, 20)),
        ("Con descuento 20 % + IVA", lambda: asesoria.calcular_costo_completo(2, 20)),
        ("Parámetros opcionales (impuesto=5)",
         lambda: asesoria.calcular_costo(2, impuesto=5)),
        ("Impuesto negativo (inválido)",
         lambda: asesoria.calcular_costo(2, impuesto=-10)),
    ]
    for nombre, calculo in variantes:
        try:
            valor = calculo()
        except CalculoInconsistenteError as error:
            logger.error("Sobrecarga - %s: %s", nombre, error)
            print(f"   ✗ {nombre}: {error}")
        else:
            logger.info("Sobrecarga - %s: $%.2f", nombre, valor)
            print(f"   ✓ {nombre}: ${valor:,.2f}")


def mostrar_estado_final(sistema: SistemaGestion) -> None:
    """Imprime las listas internas y el resumen de operaciones."""
    seccion("ESTADO FINAL DEL SISTEMA (listas en memoria)")
    print("Clientes:")
    for cliente in sistema.listar_clientes():
        print(f"  - {cliente}")
    print("Reservas:")
    for reserva in sistema.listar_reservas():
        print(f"  - {reserva}")

    seccion("RESUMEN")
    total = sistema.operaciones_exitosas + sistema.operaciones_fallidas
    print(f"Operaciones ejecutadas : {total}")
    print(f"Exitosas               : {sistema.operaciones_exitosas}")
    print(f"Fallidas (controladas) : {sistema.operaciones_fallidas}")
    print(f"Detalle completo en    : {RUTA_LOG}")
    logger.info("Resumen: %d operaciones, %d exitosas, %d fallidas", total,
                sistema.operaciones_exitosas, sistema.operaciones_fallidas)


def main() -> None:
    """Ejecuta todas las simulaciones en orden."""
    # En Windows la consola puede no usar UTF-8; se ajusta para mostrar símbolos
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("SISTEMA INTEGRAL DE GESTIÓN - SOFTWARE FJ")
    logger.info("========== INICIO DE LA EJECUCIÓN ==========")
    sistema = SistemaGestion()
    try:
        simular_clientes(sistema)
        simular_servicios(sistema)
        simular_reservas(sistema)
        demostrar_polimorfismo(sistema)
        demostrar_sobrecarga(sistema)
        mostrar_estado_final(sistema)
    finally:
        # try/finally: pase lo que pase, se registra el cierre y se libera el log
        logger.info("========== FIN DE LA EJECUCIÓN ==========")
        cerrar_logger()
        print("\nEjecución finalizada. El sistema se mantuvo estable.")


if __name__ == "__main__":
    main()
