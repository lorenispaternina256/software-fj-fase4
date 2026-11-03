"""
Clase ``Cliente``: datos personales encapsulados y validados.

Encapsulación: los atributos son privados (doble guion bajo) y solo se
acceden mediante propiedades. Cada *setter* valida el dato antes de
guardarlo, por lo que es imposible tener un cliente con datos inválidos.
"""

import re

from src.entidad_base import EntidadBase
from src.excepciones import ClienteInvalidoError, ParametroFaltanteError

# Expresión regular básica para correos: usuario@dominio.ext
PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)*\.[a-zA-Z]{2,}$")
# Nombre: solo letras (incluye tildes y ñ) y espacios
PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$")


class Cliente(EntidadBase):
    """Cliente de Software FJ."""

    def __init__(self, nombre: str, documento: str, correo: str,
                 telefono: str) -> None:
        """
        Crea un cliente validando todos sus datos.

        Raises:
            ParametroFaltanteError: si algún dato llega como ``None`` o vacío.
            ClienteInvalidoError: si algún dato tiene formato inválido.
        """
        # Primero se revisa que no falte ningún parámetro obligatorio
        self._verificar_obligatorios(nombre=nombre, documento=documento,
                                     correo=correo, telefono=telefono)
        # Se inicializa la parte común (id y fecha) heredada de EntidadBase
        super().__init__()
        # Cada asignación pasa por su setter, que valida el dato
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono

    # ------------------------------------------------------------------
    # Validación de parámetros obligatorios
    # ------------------------------------------------------------------
    @staticmethod
    def _verificar_obligatorios(**campos: object) -> None:
        """Lanza ``ParametroFaltanteError`` si algún campo es None o vacío."""
        # Se recorre cada par nombre/valor recibido
        for campo, valor in campos.items():
            # None o texto vacío se consideran parámetro faltante
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                raise ParametroFaltanteError(
                    f"El campo '{campo}' es obligatorio", campo=campo)

    # ------------------------------------------------------------------
    # Propiedades con validación (encapsulación)
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:
        """Nombre completo del cliente."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Valida que el nombre sea texto, con letras y mínimo 3 caracteres."""
        # Debe ser texto
        if not isinstance(valor, str):
            raise ClienteInvalidoError("El nombre debe ser texto", campo="nombre")
        # Se eliminan espacios sobrantes al inicio y al final
        valor = valor.strip()
        # Longitud mínima razonable para un nombre
        if len(valor) < 3:
            raise ClienteInvalidoError(
                "El nombre debe tener al menos 3 caracteres", campo="nombre")
        # Solo letras y espacios
        if not PATRON_NOMBRE.match(valor):
            raise ClienteInvalidoError(
                f"El nombre '{valor}' solo puede contener letras y espacios",
                campo="nombre")
        # Dato válido: se guarda en el atributo privado
        self.__nombre = valor

    @property
    def documento(self) -> str:
        """Número de documento (solo dígitos)."""
        return self.__documento

    @documento.setter
    def documento(self, valor: str | int) -> None:
        """Valida que el documento tenga solo dígitos y entre 6 y 12 caracteres."""
        # Se acepta número o texto, pero se guarda siempre como texto
        valor = str(valor).strip()
        # Solo dígitos: rechaza letras, puntos o guiones
        if not valor.isdigit():
            raise ClienteInvalidoError(
                f"El documento '{valor}' solo puede contener dígitos",
                campo="documento")
        # Rango de longitud permitido
        if not 6 <= len(valor) <= 12:
            raise ClienteInvalidoError(
                "El documento debe tener entre 6 y 12 dígitos",
                campo="documento")
        # Dato válido
        self.__documento = valor

    @property
    def correo(self) -> str:
        """Correo electrónico en minúsculas."""
        return self.__correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """Valida el formato del correo con una expresión regular."""
        # Se normaliza a minúsculas y sin espacios
        valor = str(valor).strip().lower()
        # Si no coincide con el patrón, el correo está mal formado
        if not PATRON_CORREO.match(valor):
            raise ClienteInvalidoError(
                f"El correo '{valor}' no tiene un formato válido",
                campo="correo")
        # Dato válido
        self.__correo = valor

    @property
    def telefono(self) -> str:
        """Teléfono celular colombiano de 10 dígitos."""
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str | int) -> None:
        """
        Valida el teléfono convirtiéndolo a entero.

        Aquí se usa ENCADENAMIENTO: si la conversión lanza ``ValueError`` se
        relanza como ``ClienteInvalidoError`` conservando el error original
        con ``from``, para que el log muestre la causa real.
        """
        # Se quitan espacios y guiones comunes al escribir teléfonos
        texto = str(valor).replace(" ", "").replace("-", "")
        try:
            # int() falla con ValueError si hay letras u otros símbolos
            int(texto)
        except ValueError as error:
            # Se traduce el error técnico a uno del dominio, encadenándolo
            raise ClienteInvalidoError(
                f"El teléfono '{valor}' debe contener solo números",
                campo="telefono") from error
        # Formato colombiano: exactamente 10 dígitos y sin signo
        if len(texto) != 10 or not texto.isdigit():
            raise ClienteInvalidoError(
                "El teléfono debe tener exactamente 10 dígitos",
                campo="telefono")
        # Dato válido
        self.__telefono = texto

    # ------------------------------------------------------------------
    # Métodos abstractos implementados
    # ------------------------------------------------------------------
    def validar(self) -> bool:
        """Revalida todos los datos reasignándolos a sus setters."""
        # Reasignar fuerza a cada setter a validar de nuevo
        self.nombre = self.__nombre
        self.documento = self.__documento
        self.correo = self.__correo
        self.telefono = self.__telefono
        return True

    def describir(self) -> str:
        """Texto con los datos del cliente."""
        return (f"Cliente #{self.id}: {self.nombre} | Doc: {self.documento} | "
                f"{self.correo} | Tel: {self.telefono}")
