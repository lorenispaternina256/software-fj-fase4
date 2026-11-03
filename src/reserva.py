"""
Clase ``Reserva``: une un cliente, un servicio, una duración y un estado.

Ciclo de vida de una reserva:

    PENDIENTE --confirmar()--> CONFIRMADA --procesar()--> PROCESADA
        |                          |
        +-------cancelar()---------+--> CANCELADA

Cualquier transición distinta lanza ``OperacionNoPermitidaError``.
"""

from enum import Enum

from src.cliente import Cliente
from src.entidad_base import EntidadBase
from src.excepciones import (CalculoInconsistenteError,
                             OperacionNoPermitidaError,
                             ParametroServicioInvalidoError,
                             ReservaInvalidaError)
from src.logger_config import obtener_logger
from src.servicios import Servicio

# Logger de este módulo
logger = obtener_logger(__name__)


class EstadoReserva(Enum):
    """Estados posibles de una reserva."""

    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"


class Reserva(EntidadBase):
    """Reserva de un servicio hecha por un cliente."""

    def __init__(self, cliente: Cliente, servicio: Servicio, duracion: float,
                 **opciones: object) -> None:
        """
        Crea la reserva en estado PENDIENTE tras validar todo.

        Args:
            cliente: cliente que reserva (instancia de ``Cliente``).
            servicio: servicio reservado (instancia de ``Servicio``).
            duracion: horas o días, según el servicio.
            **opciones: parámetros extra del servicio (personas, cantidad...).

        Raises:
            ReservaInvalidaError: datos de la reserva incorrectos.
            ServicioNoDisponibleError: el servicio no se puede reservar.
        """
        # El cliente debe ser un objeto Cliente real
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva necesita un cliente válido")
        # El servicio debe ser un objeto Servicio real (cualquier subclase)
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva necesita un servicio válido")
        # La duración debe ser numérica y mayor que cero
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)) \
                or duracion <= 0:
            raise ReservaInvalidaError(
                f"La duración de la reserva debe ser mayor que cero "
                f"(recibido: {duracion})")
        # El servicio debe estar disponible (puede lanzar ServicioNoDisponibleError)
        servicio.verificar_disponibilidad()
        try:
            # Validación específica de cada servicio (polimorfismo)
            servicio.validar_parametros(duracion, **opciones)
        except ParametroServicioInvalidoError as error:
            # Encadenamiento: el error del servicio se convierte en error de reserva
            raise ReservaInvalidaError(
                f"Parámetros de reserva inválidos: {error.mensaje}") from error

        # Todo es válido: se crea la entidad
        super().__init__()
        self._cliente: Cliente = cliente
        self._servicio: Servicio = servicio
        self._duracion: float = duracion
        self._opciones: dict = dict(opciones)
        self._estado: EstadoReserva = EstadoReserva.PENDIENTE
        # El costo se conoce solo cuando la reserva se procesa
        self._costo_final: float | None = None

    # ------------------------------------------------------------------
    # Propiedades de solo lectura
    # ------------------------------------------------------------------
    @property
    def cliente(self) -> Cliente:
        """Cliente que hizo la reserva."""
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        """Servicio reservado."""
        return self._servicio

    @property
    def duracion(self) -> float:
        """Duración reservada."""
        return self._duracion

    @property
    def estado(self) -> EstadoReserva:
        """Estado actual."""
        return self._estado

    @property
    def costo_final(self) -> float | None:
        """Costo calculado al procesar (``None`` si aún no se procesa)."""
        return self._costo_final

    # ------------------------------------------------------------------
    # Operaciones del ciclo de vida
    # ------------------------------------------------------------------
    def confirmar(self) -> None:
        """Pasa de PENDIENTE a CONFIRMADA."""
        # Solo una reserva pendiente se puede confirmar
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar la reserva #{self.id}: está "
                f"{self._estado.value}")
        # Antes de confirmar se verifica otra vez la disponibilidad
        self._servicio.verificar_disponibilidad()
        self._estado = EstadoReserva.CONFIRMADA

    def cancelar(self) -> None:
        """Cancela la reserva si aún no está cancelada ni procesada."""
        if self._estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar la reserva #{self.id}: ya está "
                f"{self._estado.value}")
        self._estado = EstadoReserva.CANCELADA

    def procesar(self, impuesto: float | None = None,
                 descuento: float | None = None) -> float:
        """
        Calcula el costo final y deja la reserva en estado PROCESADA.

        Usa el bloque completo ``try/except/else/finally``:
            * try     -> intenta calcular el costo.
            * except  -> si el cálculo es inconsistente, ENCADENA el error
                         como ``ReservaInvalidaError`` (``raise ... from``).
            * else    -> solo si no hubo error: cambia el estado y guarda costo.
            * finally -> siempre deja constancia en el log de que el intento
                         terminó, haya salido bien o mal.

        Returns:
            Costo final de la reserva.
        """
        # Solo se procesan reservas confirmadas
        if self._estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"No se puede procesar la reserva #{self.id}: está "
                f"{self._estado.value} (debe estar Confirmada)")
        try:
            # El cálculo depende del tipo de servicio (polimorfismo)
            costo = self._servicio.calcular_costo(
                self._duracion, impuesto=impuesto, descuento=descuento,
                **self._opciones)
        except CalculoInconsistenteError as error:
            # Se relanza como error de reserva conservando la causa original
            raise ReservaInvalidaError(
                f"No se pudo procesar la reserva #{self.id}: cálculo "
                f"inconsistente") from error
        else:
            # Solo llega aquí si el cálculo fue exitoso
            self._costo_final = costo
            self._estado = EstadoReserva.PROCESADA
            return costo
        finally:
            # Se ejecuta SIEMPRE: con éxito, con error o con return
            logger.info("Intento de procesamiento de la reserva #%s finalizado "
                        "(estado actual: %s)", self.id, self._estado.value)

    # ------------------------------------------------------------------
    # Métodos abstractos implementados
    # ------------------------------------------------------------------
    def validar(self) -> bool:
        """Verifica la coherencia interna de la reserva."""
        if self._duracion <= 0:
            raise ReservaInvalidaError("Duración inválida")
        if self._estado is EstadoReserva.PROCESADA and self._costo_final is None:
            raise ReservaInvalidaError("Reserva procesada sin costo final")
        return True

    def describir(self) -> str:
        """Resumen de la reserva."""
        costo = (f"${self._costo_final:,.2f}" if self._costo_final is not None
                 else "por calcular")
        return (f"Reserva #{self.id}: {self._cliente.nombre} -> "
                f"{self._servicio.nombre} | duración {self._duracion} | "
                f"estado {self._estado.value} | costo {costo}")
