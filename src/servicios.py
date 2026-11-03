"""
Servicios ofrecidos por Software FJ.

* ``Servicio`` es una clase ABSTRACTA: define qué debe saber hacer cualquier
  servicio (calcular costo, describirse y validar parámetros), pero no cómo.
* ``ReservaSala``, ``AlquilerEquipo`` y ``AsesoriaEspecializada`` HEREDAN de
  ``Servicio`` y SOBRESCRIBEN esos métodos con su propia lógica
  (POLIMORFISMO: la misma llamada produce resultados distintos).

Nota sobre "métodos sobrecargados":
    Python no permite definir varias funciones con el mismo nombre y distinta
    firma (como Java). La sobrecarga se SIMULA de dos formas:
      1. Parámetros opcionales con valor por defecto en ``calcular_costo``
         (``impuesto=None``, ``descuento=None``, ``**opciones``).
      2. Métodos variantes que reutilizan el cálculo base:
         ``calcular_costo_con_impuesto``, ``calcular_costo_con_descuento`` y
         ``calcular_costo_completo``.
"""

from abc import abstractmethod

from src.entidad_base import EntidadBase
from src.excepciones import (CalculoInconsistenteError,
                             ParametroServicioInvalidoError,
                             ServicioNoDisponibleError)

# IVA vigente en Colombia, en porcentaje
IVA_COLOMBIA: float = 19.0


class Servicio(EntidadBase):
    """Servicio genérico. No se puede instanciar directamente."""

    def __init__(self, nombre: str, tarifa_base: float,
                 disponible: bool = True) -> None:
        """
        Args:
            nombre: nombre comercial del servicio (único en el sistema).
            tarifa_base: valor por unidad de tiempo, mayor que cero.
            disponible: indica si el servicio se puede reservar.

        Raises:
            ParametroServicioInvalidoError: si el nombre o la tarifa son inválidos.
        """
        # Se inicializa id y fecha heredados
        super().__init__()
        # Se validan y guardan los atributos comunes (protegidos)
        self._nombre: str = self._validar_nombre(nombre)
        self._tarifa_base: float = self._validar_tarifa(tarifa_base)
        self._disponible: bool = bool(disponible)

    # ------------------------------------------------------------------
    # Validaciones comunes
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        """Verifica que el nombre sea un texto no vacío."""
        # None, otro tipo o texto vacío no son válidos
        if not isinstance(nombre, str) or not nombre.strip():
            raise ParametroServicioInvalidoError(
                "El nombre del servicio es obligatorio")
        return nombre.strip()

    @staticmethod
    def _validar_tarifa(tarifa: float) -> float:
        """
        Convierte la tarifa a número y verifica que sea positiva.

        Usa ENCADENAMIENTO: el ``TypeError``/``ValueError`` de ``float()`` se
        relanza como ``ParametroServicioInvalidoError`` con ``from``.
        """
        try:
            # Intenta convertir cualquier entrada a número decimal
            valor = float(tarifa)
        except (TypeError, ValueError) as error:
            # Se conserva la causa original para el log
            raise ParametroServicioInvalidoError(
                f"La tarifa '{tarifa}' no es un número válido") from error
        # Una tarifa cero o negativa no tiene sentido comercial
        if valor <= 0:
            raise ParametroServicioInvalidoError(
                f"La tarifa debe ser mayor que cero (recibido: {valor})")
        return valor

    @staticmethod
    def _validar_duracion(duracion: float) -> float:
        """Verifica que la duración sea un número mayor que cero."""
        # Se rechazan bool (True/False son int en Python) y tipos no numéricos
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)):
            raise ParametroServicioInvalidoError(
                f"La duración '{duracion}' debe ser numérica")
        # La duración debe ser positiva
        if duracion <= 0:
            raise ParametroServicioInvalidoError(
                f"La duración debe ser mayor que cero (recibido: {duracion})")
        return float(duracion)

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:
        """Nombre del servicio."""
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        """Tarifa base por unidad de tiempo."""
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        """Indica si el servicio se puede reservar."""
        return self._disponible

    @disponible.setter
    def disponible(self, valor: bool) -> None:
        """Permite habilitar o deshabilitar el servicio."""
        self._disponible = bool(valor)

    # ------------------------------------------------------------------
    # Métodos concretos compartidos
    # ------------------------------------------------------------------
    def verificar_disponibilidad(self) -> None:
        """Lanza ``ServicioNoDisponibleError`` si el servicio está deshabilitado."""
        if not self._disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._nombre}' no está disponible")

    def validar(self) -> bool:
        """Revalida los atributos comunes del servicio."""
        self._validar_nombre(self._nombre)
        self._validar_tarifa(self._tarifa_base)
        return True

    @staticmethod
    def _aplicar_ajustes(subtotal: float, impuesto: float | None = None,
                         descuento: float | None = None) -> float:
        """
        Aplica descuento e impuesto (ambos en porcentaje) a un subtotal.

        El descuento se aplica primero y luego el impuesto sobre el valor
        con descuento, como en una factura real.

        Raises:
            CalculoInconsistenteError: si los porcentajes no son números,
                el descuento no está entre 0 y 100, el impuesto es negativo
                o el resultado final es negativo.
        """
        try:
            # Valores ausentes equivalen a 0 %
            porcentaje_desc = float(descuento) if descuento is not None else 0.0
            porcentaje_imp = float(impuesto) if impuesto is not None else 0.0
        except (TypeError, ValueError) as error:
            # Encadenamiento: se informa el error de dominio con su causa
            raise CalculoInconsistenteError(
                "El impuesto y el descuento deben ser números") from error
        # Un descuento fuera de 0-100 % es incoherente
        if not 0 <= porcentaje_desc <= 100:
            raise CalculoInconsistenteError(
                f"Descuento inválido: {porcentaje_desc}% (debe estar entre 0 y 100)")
        # Un impuesto negativo es incoherente
        if porcentaje_imp < 0:
            raise CalculoInconsistenteError(
                f"Impuesto inválido: {porcentaje_imp}% (no puede ser negativo)")
        # Se aplica primero el descuento
        con_descuento = subtotal * (1 - porcentaje_desc / 100)
        # Luego el impuesto sobre el valor ya descontado
        total = con_descuento * (1 + porcentaje_imp / 100)
        # Comprobación final de coherencia
        if total < 0:
            raise CalculoInconsistenteError(
                f"El costo calculado es negativo ({total:.2f})")
        # Se redondea a 2 decimales (pesos con centavos)
        return round(total, 2)

    # ------------------------------------------------------------------
    # Variantes "sobrecargadas" del cálculo de costo
    # ------------------------------------------------------------------
    def calcular_costo_con_impuesto(self, duracion: float,
                                    impuesto: float = IVA_COLOMBIA,
                                    **opciones: object) -> float:
        """Variante: costo base + impuesto (IVA 19 % por defecto)."""
        return self.calcular_costo(duracion, impuesto=impuesto, **opciones)

    def calcular_costo_con_descuento(self, duracion: float, descuento: float,
                                     **opciones: object) -> float:
        """Variante: costo base con descuento y sin impuesto."""
        return self.calcular_costo(duracion, descuento=descuento, **opciones)

    def calcular_costo_completo(self, duracion: float, descuento: float,
                                impuesto: float = IVA_COLOMBIA,
                                **opciones: object) -> float:
        """Variante: costo con descuento e impuesto combinados."""
        return self.calcular_costo(duracion, impuesto=impuesto,
                                   descuento=descuento, **opciones)

    # ------------------------------------------------------------------
    # Métodos abstractos (cada subclase los sobrescribe)
    # ------------------------------------------------------------------
    @abstractmethod
    def calcular_costo(self, duracion: float, impuesto: float | None = None,
                       descuento: float | None = None,
                       **opciones: object) -> float:
        """Calcula el costo del servicio para la duración indicada."""

    @abstractmethod
    def validar_parametros(self, duracion: float, **opciones: object) -> None:
        """Valida que los parámetros de uso del servicio sean correctos."""

    @abstractmethod
    def describir(self) -> str:
        """Descripción legible del servicio."""
