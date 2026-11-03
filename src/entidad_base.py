"""
Clase abstracta ``EntidadBase``: representa cualquier entidad del sistema.

Clientes, servicios y reservas comparten un identificador y una fecha de
creación, y todos deben saber describirse y validarse. Por eso esa parte
común se define una sola vez aquí (abstracción + herencia).
"""

from abc import ABC, abstractmethod
from datetime import datetime


class EntidadBase(ABC):
    """Entidad general del sistema. No se puede instanciar directamente."""

    # Contador compartido por todas las entidades para generar ids únicos
    _contador_ids: int = 0

    def __init__(self) -> None:
        """Asigna un id autoincremental y la fecha de creación."""
        # Se incrementa el contador de la clase base (compartido por todas)
        EntidadBase._contador_ids += 1
        # Id protegido: solo se lee mediante la propiedad ``id``
        self._id: int = EntidadBase._contador_ids
        # Momento exacto en que se creó la entidad
        self._fecha_creacion: datetime = datetime.now()

    @property
    def id(self) -> int:
        """Identificador único de la entidad (solo lectura)."""
        return self._id

    @property
    def fecha_creacion(self) -> datetime:
        """Fecha y hora de creación (solo lectura)."""
        return self._fecha_creacion

    @abstractmethod
    def describir(self) -> str:
        """Devuelve un texto legible con la información de la entidad."""

    @abstractmethod
    def validar(self) -> bool:
        """
        Verifica que el estado interno de la entidad sea coherente.

        Debe lanzar una excepción del sistema si algo es inválido.
        """

    def __str__(self) -> str:
        """Representación amigable: reutiliza ``describir`` (polimorfismo)."""
        return self.describir()

    def __repr__(self) -> str:
        """Representación técnica, útil para depurar."""
        return f"<{self.__class__.__name__} id={self._id}>"
