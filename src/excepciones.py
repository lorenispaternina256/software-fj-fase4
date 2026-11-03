"""
Módulo de excepciones personalizadas del sistema Software FJ.

Aquí se define una jerarquía propia de excepciones que hereda de ``Exception``.
Tener una jerarquía permite:
    * Capturar errores de forma específica (por ejemplo, solo ``ReservaError``).
    * Capturar todos los errores del dominio con una sola cláusula
      (``except SoftwareFJError``) sin atrapar errores ajenos al sistema.
    * Adjuntar información extra (código y campo) útil para el archivo de logs.

Jerarquía:
    SoftwareFJError
    ├── ValidacionError
    │   ├── ClienteInvalidoError
    │   └── ParametroFaltanteError
    ├── ServicioError
    │   ├── ServicioNoDisponibleError
    │   └── ParametroServicioInvalidoError
    ├── ReservaError
    │   ├── ReservaInvalidaError
    │   └── OperacionNoPermitidaError
    └── CalculoInconsistenteError
"""


class SoftwareFJError(Exception):
    """Excepción base de la que heredan todos los errores del sistema."""

    # Código genérico que usan las subclases que no definen uno propio
    codigo_por_defecto: str = "SFJ-000"

    def __init__(self, mensaje: str, codigo: str | None = None) -> None:
        """
        Crea la excepción con un mensaje legible y un código de error.

        Args:
            mensaje: descripción clara del problema.
            codigo: código corto para identificar el error en los logs.
        """
        # Se llama al constructor de Exception para conservar el comportamiento estándar
        super().__init__(mensaje)
        # Se guarda el mensaje como atributo para poder consultarlo después
        self.mensaje = mensaje
        # Si no se envía un código se usa el código por defecto de la clase
        self.codigo = codigo or self.codigo_por_defecto

    def __str__(self) -> str:
        """Devuelve el error con el formato ``[CODIGO] mensaje``."""
        return f"[{self.codigo}] {self.mensaje}"


# ---------------------------------------------------------------------------
# Errores de validación de datos
# ---------------------------------------------------------------------------
class ValidacionError(SoftwareFJError):
    """Error producido cuando un dato no cumple el formato o rango esperado."""

    codigo_por_defecto = "VAL-001"

    def __init__(self, mensaje: str, campo: str | None = None,
                 codigo: str | None = None) -> None:
        """
        Args:
            mensaje: descripción del error.
            campo: nombre del campo que falló la validación.
            codigo: código de error opcional.
        """
        # Se reutiliza el constructor de la clase base
        super().__init__(mensaje, codigo)
        # Se guarda el campo para saber exactamente qué dato estaba mal
        self.campo = campo

    def __str__(self) -> str:
        """Incluye el campo inválido en el texto cuando se conoce."""
        # Texto base heredado: "[CODIGO] mensaje"
        texto = super().__str__()
        # Si hay campo se agrega al final para dar más contexto
        return f"{texto} (campo: {self.campo})" if self.campo else texto


class ClienteInvalidoError(ValidacionError):
    """Los datos personales de un cliente no son válidos."""

    codigo_por_defecto = "CLI-001"


class ParametroFaltanteError(ValidacionError):
    """Falta un parámetro obligatorio (llega ``None`` o vacío)."""

    codigo_por_defecto = "VAL-002"


# ---------------------------------------------------------------------------
# Errores relacionados con servicios
# ---------------------------------------------------------------------------
class ServicioError(SoftwareFJError):
    """Error general relacionado con los servicios ofrecidos."""

    codigo_por_defecto = "SRV-000"


class ServicioNoDisponibleError(ServicioError):
    """Se intentó usar un servicio que no está disponible o sin cupo."""

    codigo_por_defecto = "SRV-001"


class ParametroServicioInvalidoError(ServicioError):
    """Un parámetro de creación o uso de un servicio es inválido."""

    codigo_por_defecto = "SRV-002"


# ---------------------------------------------------------------------------
# Errores relacionados con reservas
# ---------------------------------------------------------------------------
class ReservaError(SoftwareFJError):
    """Error general relacionado con reservas."""

    codigo_por_defecto = "RES-000"


class ReservaInvalidaError(ReservaError):
    """La reserva no se puede crear o procesar con los datos recibidos."""

    codigo_por_defecto = "RES-001"


class OperacionNoPermitidaError(ReservaError):
    """La operación no es válida para el estado actual de la reserva."""

    codigo_por_defecto = "RES-002"


# ---------------------------------------------------------------------------
# Errores de cálculo
# ---------------------------------------------------------------------------
class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo de un costo produjo o recibió valores incoherentes."""

    codigo_por_defecto = "CAL-001"
