"""
Registro de agentes disponibles para la linea de comandos.

Centraliza la construccion de agentes para que agregar uno nuevo no obligue a
modificar la capa de consola ni la interfaz grafica. Esto cumple el Principio
Abierto/Cerrado: el sistema se extiende registrando, no editando.
"""

from typing import Callable, Dict, List

from src.agentes.agente import Agente
from src.agentes.agente_aleatorio import AgenteAleatorio


# Firma que debe cumplir todo constructor registrado: recibe la semilla y
# devuelve una instancia lista para planificar.
ConstructorAgente = Callable[[int], Agente]


class ErrorAgenteDesconocido(Exception):
    """Se lanza cuando se solicita un agente que no esta registrado."""


class RegistroAgentes:
    """Tabla de agentes disponibles, indexada por su nombre en consola."""

    def __init__(self) -> None:
        """Crea el registro con los agentes disponibles en esta etapa."""
        self._constructores: Dict[str, ConstructorAgente] = {}
        self._registrar_agentes_disponibles()

    def _registrar_agentes_disponibles(self) -> None:
        """
        Inscribe cada agente implementado.

        Cuando el agente de busqueda y el evolutivo existan, se agregan aqui
        dos lineas y ningun otro archivo del sistema cambia.
        """
        self.registrar("aleatorio", self._construir_aleatorio)

    def registrar(self, nombre: str, constructor: ConstructorAgente) -> None:
        """Inscribe un constructor bajo el nombre indicado."""
        self._constructores[nombre] = constructor

    def construir(self, nombre: str, semilla: int) -> Agente:
        """Devuelve una instancia nueva del agente solicitado."""
        if nombre not in self._constructores:
            raise ErrorAgenteDesconocido(
                "Agente desconocido: '" + str(nombre) + "'. "
                "Agentes disponibles: " + ", ".join(self.nombres_disponibles())
            )

        constructor = self._constructores[nombre]
        return constructor(semilla)

    def nombres_disponibles(self) -> List[str]:
        """Devuelve la lista ordenada de nombres registrados."""
        return sorted(self._constructores.keys())

    # ------------------------------------------------------------------
    # Constructores concretos
    # ------------------------------------------------------------------

    def _construir_aleatorio(self, semilla: int) -> Agente:
        """Construye el agente de linea base aleatorio."""
        return AgenteAleatorio(semilla=semilla)