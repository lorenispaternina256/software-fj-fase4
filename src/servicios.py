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


# ===========================================================================
# Servicio 1: Reserva de salas
# ===========================================================================
class ReservaSala(Servicio):
    """Reserva de una sala de reuniones por horas."""

    # Recargo por hora si la sala incluye proyector
    RECARGO_PROYECTOR: float = 15000.0
    # Máximo de horas que se puede reservar una sala en un día
    MAX_HORAS: int = 12

    def __init__(self, nombre: str, tarifa_base: float, capacidad: int,
                 tiene_proyector: bool = False, disponible: bool = True) -> None:
        """
        Args:
            capacidad: número máximo de personas (entero mayor que cero).
            tiene_proyector: si la sala incluye proyector.
        """
        # Atributos comunes validados por la clase padre
        super().__init__(nombre, tarifa_base, disponible)
        # La capacidad debe ser un entero positivo
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) \
                or capacidad <= 0:
            raise ParametroServicioInvalidoError(
                f"La capacidad '{capacidad}' debe ser un entero mayor que cero")
        self._capacidad: int = capacidad
        self._tiene_proyector: bool = bool(tiene_proyector)

    def validar_parametros(self, duracion: float, **opciones: object) -> None:
        """Valida horas (1 a 12) y que las personas no superen la capacidad."""
        # Duración positiva (validación común)
        horas = self._validar_duracion(duracion)
        # Límite de horas por reserva
        if horas > self.MAX_HORAS:
            raise ParametroServicioInvalidoError(
                f"Una sala se reserva máximo {self.MAX_HORAS} horas")
        # Número de asistentes (1 si no se indica)
        personas = opciones.get("personas", 1)
        if not isinstance(personas, int) or personas <= 0:
            raise ParametroServicioInvalidoError(
                "El número de personas debe ser un entero positivo")
        # No puede superar la capacidad de la sala
        if personas > self._capacidad:
            raise ParametroServicioInvalidoError(
                f"{personas} personas superan la capacidad de la sala "
                f"({self._capacidad})")

    def calcular_costo(self, duracion: float, impuesto: float | None = None,
                       descuento: float | None = None,
                       **opciones: object) -> float:
        """Costo = (tarifa + recargo de proyector) x horas, con ajustes."""
        # Se validan los parámetros antes de calcular
        self.validar_parametros(duracion, **opciones)
        # Tarifa por hora, incluyendo recargo si hay proyector
        tarifa_hora = self._tarifa_base + (
            self.RECARGO_PROYECTOR if self._tiene_proyector else 0)
        # Subtotal antes de impuestos y descuentos
        subtotal = tarifa_hora * duracion
        # Se aplican los ajustes opcionales
        return self._aplicar_ajustes(subtotal, impuesto, descuento)

    def describir(self) -> str:
        """Descripción de la sala."""
        proyector = "con proyector" if self._tiene_proyector else "sin proyector"
        estado = "disponible" if self._disponible else "NO disponible"
        return (f"[Sala] {self._nombre}: capacidad {self._capacidad} personas, "
                f"{proyector}, ${self._tarifa_base:,.0f}/hora ({estado})")


# ===========================================================================
# Servicio 2: Alquiler de equipos
# ===========================================================================
class AlquilerEquipo(Servicio):
    """Alquiler de equipos tecnológicos por días."""

    def __init__(self, nombre: str, tarifa_base: float, tipo_equipo: str,
                 cantidad_disponible: int, disponible: bool = True) -> None:
        """
        Args:
            tipo_equipo: por ejemplo "Portátil" o "Video beam".
            cantidad_disponible: unidades en inventario (entero >= 0).
        """
        super().__init__(nombre, tarifa_base, disponible)
        # Tipo de equipo obligatorio
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise ParametroServicioInvalidoError(
                "El tipo de equipo es obligatorio")
        # Inventario no negativo
        if isinstance(cantidad_disponible, bool) \
                or not isinstance(cantidad_disponible, int) \
                or cantidad_disponible < 0:
            raise ParametroServicioInvalidoError(
                "La cantidad disponible debe ser un entero mayor o igual a 0")
        self._tipo_equipo: str = tipo_equipo.strip()
        self._cantidad_disponible: int = cantidad_disponible

    def verificar_disponibilidad(self) -> None:
        """Sobrescribe la verificación: además exige inventario > 0."""
        # Primero la verificación general de la clase padre
        super().verificar_disponibilidad()
        # Sin unidades no hay cupo
        if self._cantidad_disponible == 0:
            raise ServicioNoDisponibleError(
                f"No quedan unidades de '{self._nombre}'")

    def validar_parametros(self, duracion: float, **opciones: object) -> None:
        """Valida días y que la cantidad pedida exista en inventario."""
        self._validar_duracion(duracion)
        # Unidades solicitadas (1 por defecto)
        cantidad = opciones.get("cantidad", 1)
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ParametroServicioInvalidoError(
                "La cantidad solicitada debe ser un entero positivo")
        # No se puede alquilar más de lo que hay
        if cantidad > self._cantidad_disponible:
            raise ServicioNoDisponibleError(
                f"Se pidieron {cantidad} unidades de '{self._nombre}' y solo "
                f"hay {self._cantidad_disponible}")

    def calcular_costo(self, duracion: float, impuesto: float | None = None,
                       descuento: float | None = None,
                       **opciones: object) -> float:
        """Costo = tarifa x días x cantidad, con ajustes."""
        self.validar_parametros(duracion, **opciones)
        cantidad = opciones.get("cantidad", 1)
        subtotal = self._tarifa_base * duracion * cantidad
        return self._aplicar_ajustes(subtotal, impuesto, descuento)

    def describir(self) -> str:
        """Descripción del equipo."""
        estado = "disponible" if self._disponible else "NO disponible"
        return (f"[Equipo] {self._nombre}: tipo {self._tipo_equipo}, "
                f"{self._cantidad_disponible} unidades, "
                f"${self._tarifa_base:,.0f}/día ({estado})")


# ===========================================================================
# Servicio 3: Asesorías especializadas
# ===========================================================================
class AsesoriaEspecializada(Servicio):
    """Asesoría profesional por horas, con precio según el nivel del experto."""

    # Multiplicador de la tarifa según el nivel del asesor
    MULTIPLICADORES: dict[str, float] = {"junior": 1.0, "senior": 1.5,
                                         "experto": 2.0}

    def __init__(self, nombre: str, tarifa_base: float, area: str,
                 nivel_experto: str = "junior", disponible: bool = True) -> None:
        """
        Args:
            area: área de conocimiento, por ejemplo "Ciberseguridad".
            nivel_experto: "junior", "senior" o "experto".
        """
        super().__init__(nombre, tarifa_base, disponible)
        if not isinstance(area, str) or not area.strip():
            raise ParametroServicioInvalidoError("El área de asesoría es obligatoria")
        # Se normaliza el nivel para comparar sin importar mayúsculas
        nivel = str(nivel_experto).strip().lower()
        if nivel not in self.MULTIPLICADORES:
            raise ParametroServicioInvalidoError(
                f"Nivel '{nivel_experto}' inválido. Opciones: "
                f"{', '.join(self.MULTIPLICADORES)}")
        self._area: str = area.strip()
        self._nivel_experto: str = nivel

    def validar_parametros(self, duracion: float, **opciones: object) -> None:
        """Valida horas (máximo 8 por sesión)."""
        horas = self._validar_duracion(duracion)
        if horas > 8:
            raise ParametroServicioInvalidoError(
                "Una asesoría no puede superar 8 horas por sesión")

    def calcular_costo(self, duracion: float, impuesto: float | None = None,
                       descuento: float | None = None,
                       **opciones: object) -> float:
        """Costo = tarifa x horas x multiplicador del nivel, con ajustes."""
        self.validar_parametros(duracion, **opciones)
        multiplicador = self.MULTIPLICADORES[self._nivel_experto]
        subtotal = self._tarifa_base * duracion * multiplicador
        return self._aplicar_ajustes(subtotal, impuesto, descuento)

    def describir(self) -> str:
        """Descripción de la asesoría."""
        estado = "disponible" if self._disponible else "NO disponible"
        return (f"[Asesoría] {self._nombre}: área {self._area}, nivel "
                f"{self._nivel_experto}, ${self._tarifa_base:,.0f}/hora ({estado})")
