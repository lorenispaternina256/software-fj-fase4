"""
``SistemaGestion``: gestor central de Software FJ.

Guarda clientes, servicios y reservas en LISTAS INTERNAS (sin base de datos).
Cada método público:
    1. Intenta la operación dentro de un ``try``.
    2. Captura las excepciones del dominio, las registra en el log y devuelve
       ``None``/``False`` para que el programa NUNCA se detenga.
    3. Usa ``else`` para registrar el éxito y ``finally`` para cerrar la
       operación en el log.
"""

from collections.abc import Callable
from typing import TypeVar

from src.cliente import Cliente
from src.excepciones import (ClienteInvalidoError, ParametroFaltanteError,
                             ParametroServicioInvalidoError,
                             ReservaInvalidaError, ServicioError,
                             SoftwareFJError, ValidacionError)
from src.logger_config import obtener_logger
from src.reserva import Reserva
from src.servicios import (AlquilerEquipo, AsesoriaEspecializada, ReservaSala,
                           Servicio)

# Logger de este módulo
logger = obtener_logger(__name__)
# Tipo genérico para el resultado de una operación
T = TypeVar("T")


class SistemaGestion:
    """Administra en memoria los clientes, servicios y reservas."""

    # Catálogo de tipos de servicio: agregar uno nuevo solo requiere
    # sumarlo aquí (diseño extensible)
    TIPOS_SERVICIO: dict[str, type[Servicio]] = {
        "sala": ReservaSala,
        "equipo": AlquilerEquipo,
        "asesoria": AsesoriaEspecializada,
    }

    def __init__(self) -> None:
        """Crea las listas internas vacías y los contadores."""
        # Listas internas: única "persistencia" del sistema (en memoria)
        self._clientes: list[Cliente] = []
        self._servicios: list[Servicio] = []
        self._reservas: list[Reserva] = []
        # Contadores para el resumen final
        self._exitosas: int = 0
        self._fallidas: int = 0
        logger.info("Sistema de gestión Software FJ iniciado")

    # ------------------------------------------------------------------
    # Ejecutor genérico de operaciones (try / except / else / finally)
    # ------------------------------------------------------------------
    def _ejecutar(self, descripcion: str, operacion: Callable[[], T]) -> T | None:
        """
        Ejecuta una operación de forma segura.

        * try     -> ejecuta la operación.
        * except  -> errores del dominio: se registran como WARNING/ERROR,
                     incluyendo la causa original si fueron encadenados.
                     Errores inesperados: se registran con traza completa.
        * else    -> solo si todo salió bien: registra el éxito.
        * finally -> siempre registra que la operación terminó.

        Returns:
            El resultado de la operación o ``None`` si falló.
        """
        resultado: T | None = None
        try:
            resultado = operacion()
        except ValidacionError as error:
            # Datos de entrada incorrectos: operación rechazada
            self._registrar_fallo(descripcion, error, nivel="warning")
        except SoftwareFJError as error:
            # Cualquier otro error del dominio (servicio, reserva, cálculo)
            self._registrar_fallo(descripcion, error, nivel="error")
        except Exception as error:  # noqa: BLE001 - red de seguridad final
            # Error no previsto: se guarda la traza completa y el sistema sigue
            self._fallidas += 1
            logger.exception("Error inesperado en '%s': %s", descripcion, error)
            print(f"   ✗ Error inesperado: {error}")
        else:
            # Solo se ejecuta si no hubo ninguna excepción
            self._exitosas += 1
            logger.info("ÉXITO - %s", descripcion)
            print(f"   ✓ {descripcion}: operación exitosa")
        finally:
            # Siempre se ejecuta, para dejar trazabilidad de cada operación
            logger.info("Fin de la operación: %s", descripcion)
        return resultado

    def _registrar_fallo(self, descripcion: str, error: SoftwareFJError,
                         nivel: str) -> None:
        """Registra un error del dominio y su causa encadenada, si existe."""
        self._fallidas += 1
        # Se elige el método del logger según el nivel pedido
        registrar = logger.warning if nivel == "warning" else logger.error
        registrar("FALLO - %s -> %s: %s", descripcion,
                  type(error).__name__, error)
        # Si el error fue encadenado con "from", se registra también la causa
        if error.__cause__ is not None:
            registrar("   Causa original: %s: %s",
                      type(error.__cause__).__name__, error.__cause__)
        print(f"   ✗ {type(error).__name__}: {error}")
        if error.__cause__ is not None:
            print(f"     ↳ causado por {type(error.__cause__).__name__}: "
                  f"{error.__cause__}")

    # ------------------------------------------------------------------
    # Clientes
    # ------------------------------------------------------------------
    def registrar_cliente(self, nombre: str, documento: str, correo: str,
                          telefono: str) -> Cliente | None:
        """Crea y guarda un cliente. Devuelve ``None`` si los datos son inválidos."""
        def operacion() -> Cliente:
            # No se permiten documentos repetidos
            if documento is not None and self.buscar_cliente(str(documento)):
                raise ClienteInvalidoError(
                    f"Ya existe un cliente con documento {documento}",
                    campo="documento")
            cliente = Cliente(nombre, documento, correo, telefono)
            self._clientes.append(cliente)
            logger.info("Cliente registrado: %s", cliente.describir())
            return cliente

        return self._ejecutar(f"Registrar cliente '{nombre}'", operacion)

    def buscar_cliente(self, documento: str) -> Cliente | None:
        """Busca un cliente por documento en la lista interna."""
        for cliente in self._clientes:
            if cliente.documento == str(documento).strip():
                return cliente
        return None

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------
    def crear_servicio(self, tipo: str, **datos: object) -> Servicio | None:
        """
        Crea un servicio del tipo indicado ("sala", "equipo" o "asesoria").

        Si el constructor falla por un ``TypeError`` (falta un argumento o
        sobra uno), se ENCADENA como ``ParametroServicioInvalidoError``.
        """
        def operacion() -> Servicio:
            clase = self.TIPOS_SERVICIO.get(str(tipo).lower())
            if clase is None:
                raise ParametroServicioInvalidoError(
                    f"Tipo de servicio desconocido: '{tipo}'")
            # No se permiten nombres de servicio repetidos
            if self.buscar_servicio(str(datos.get("nombre", ""))):
                raise ParametroServicioInvalidoError(
                    f"Ya existe un servicio llamado '{datos.get('nombre')}'")
            try:
                servicio = clase(**datos)
            except TypeError as error:
                # Parámetros faltantes o sobrantes en el constructor
                raise ParametroServicioInvalidoError(
                    f"Parámetros incorrectos para crear '{tipo}'") from error
            self._servicios.append(servicio)
            logger.info("Servicio creado: %s", servicio.describir())
            return servicio

        return self._ejecutar(f"Crear servicio {tipo} '{datos.get('nombre')}'",
                              operacion)

    def buscar_servicio(self, nombre: str) -> Servicio | None:
        """Busca un servicio por nombre (sin distinguir mayúsculas)."""
        for servicio in self._servicios:
            if servicio.nombre.lower() == nombre.strip().lower():
                return servicio
        return None

    def cambiar_disponibilidad(self, nombre: str, disponible: bool) -> bool:
        """Habilita o deshabilita un servicio. Devuelve ``True`` si lo logró."""
        def operacion() -> bool:
            servicio = self.buscar_servicio(nombre)
            if servicio is None:
                raise ServicioError(f"No existe el servicio '{nombre}'")
            servicio.disponible = disponible
            logger.info("Servicio '%s' marcado como %s", nombre,
                        "disponible" if disponible else "NO disponible")
            return True

        estado = "disponible" if disponible else "no disponible"
        return bool(self._ejecutar(f"Marcar '{nombre}' como {estado}", operacion))

    # ------------------------------------------------------------------
    # Reservas
    # ------------------------------------------------------------------
    def crear_reserva(self, documento: str, nombre_servicio: str,
                      duracion: float, **opciones: object) -> Reserva | None:
        """Crea una reserva PENDIENTE para un cliente y un servicio existentes."""
        def operacion() -> Reserva:
            if documento is None or nombre_servicio is None:
                raise ParametroFaltanteError(
                    "El documento y el servicio son obligatorios para reservar")
            cliente = self.buscar_cliente(documento)
            if cliente is None:
                raise ReservaInvalidaError(
                    f"No existe un cliente con documento {documento}")
            servicio = self.buscar_servicio(nombre_servicio)
            if servicio is None:
                raise ReservaInvalidaError(
                    f"No existe el servicio '{nombre_servicio}'")
            reserva = Reserva(cliente, servicio, duracion, **opciones)
            self._reservas.append(reserva)
            logger.info("Reserva creada: %s", reserva.describir())
            return reserva

        return self._ejecutar(
            f"Crear reserva de '{nombre_servicio}' para doc {documento}",
            operacion)

    def confirmar_reserva(self, reserva: Reserva | None) -> bool:
        """Confirma una reserva. Devuelve ``True`` si lo logró."""
        def operacion() -> bool:
            self._exigir_reserva(reserva).confirmar()
            logger.info("Reserva #%s confirmada", reserva.id)
            return True

        return bool(self._ejecutar(f"Confirmar reserva {self._ref(reserva)}",
                                   operacion))

    def cancelar_reserva(self, reserva: Reserva | None) -> bool:
        """Cancela una reserva. Devuelve ``True`` si lo logró."""
        def operacion() -> bool:
            self._exigir_reserva(reserva).cancelar()
            logger.info("Reserva #%s cancelada", reserva.id)
            return True

        return bool(self._ejecutar(f"Cancelar reserva {self._ref(reserva)}",
                                   operacion))

    def procesar_reserva(self, reserva: Reserva | None,
                         impuesto: float | None = None,
                         descuento: float | None = None) -> float | None:
        """Procesa una reserva confirmada y devuelve su costo final."""
        def operacion() -> float:
            costo = self._exigir_reserva(reserva).procesar(impuesto, descuento)
            logger.info("Reserva #%s procesada. Costo final: $%.2f",
                        reserva.id, costo)
            print(f"   → Costo final: ${costo:,.2f}")
            return costo

        return self._ejecutar(
            f"Procesar reserva {self._ref(reserva)} (impuesto={impuesto}, "
            f"descuento={descuento})", operacion)

    @staticmethod
    def _exigir_reserva(reserva: Reserva | None) -> Reserva:
        """Lanza ``ReservaInvalidaError`` si no se recibió una reserva real."""
        if not isinstance(reserva, Reserva):
            raise ReservaInvalidaError("No se recibió una reserva válida")
        return reserva

    @staticmethod
    def _ref(reserva: Reserva | None) -> str:
        """Texto corto para identificar una reserva en los mensajes."""
        return f"#{reserva.id}" if isinstance(reserva, Reserva) else "(inexistente)"

    # ------------------------------------------------------------------
    # Listados y resumen
    # ------------------------------------------------------------------
    def listar_clientes(self) -> list[Cliente]:
        """Copia de la lista de clientes (protege la lista interna)."""
        return list(self._clientes)

    def listar_servicios(self) -> list[Servicio]:
        """Copia de la lista de servicios."""
        return list(self._servicios)

    def listar_reservas(self) -> list[Reserva]:
        """Copia de la lista de reservas."""
        return list(self._reservas)

    @property
    def operaciones_exitosas(self) -> int:
        """Número de operaciones exitosas."""
        return self._exitosas

    @property
    def operaciones_fallidas(self) -> int:
        """Número de operaciones fallidas (controladas)."""
        return self._fallidas
