"""
Registro de los subcomandos disponibles.

Cumple para los comandos el mismo papel que RegistroAgentes cumple para los
agentes: centraliza la construccion para que agregar un subcomando nuevo no
obligue a modificar el punto de entrada. Eso es el Principio Abierto/Cerrado
aplicado a la capa de consola.
"""

from typing import Dict, List

from src.cli.comando import Comando
from src.cli.comandos.comando_agentes import ComandoAgentes
from src.cli.comandos.comando_instancia import ComandoInstancia
from src.cli.comandos.comando_jugar import ComandoJugar
from src.cli.comandos.comando_resolver import ComandoResolver
from src.cli.comandos.comando_validar import ComandoValidar


class ErrorComandoDesconocido(Exception):
    """Se lanza cuando se solicita un subcomando que no esta registrado."""


class RegistroComandos:
    """Tabla de subcomandos disponibles, indexada por su nombre en consola."""

    def __init__(self) -> None:
        """Crea el registro con todos los subcomandos del programa."""
        self._comandos: Dict[str, Comando] = {}
        self._registrar_comandos_disponibles()

    def _registrar_comandos_disponibles(self) -> None:
        """
        Inscribe cada subcomando implementado.

        El orden de inscripcion es el orden en que aparecen en la ayuda, asi
        que se listan de mayor a menor frecuencia de uso.
        """
        self.registrar(ComandoResolver())
        self.registrar(ComandoValidar())
        self.registrar(ComandoJugar())
        self.registrar(ComandoInstancia())
        self.registrar(ComandoAgentes())

    def registrar(self, comando: Comando) -> None:
        """Inscribe un subcomando bajo su propio nombre."""
        self._comandos[comando.nombre] = comando

    def obtener(self, nombre: str) -> Comando:
        """Devuelve el subcomando solicitado."""
        if nombre not in self._comandos:
            raise ErrorComandoDesconocido(
                "Subcomando desconocido: '" + str(nombre) + "'. "
                "Subcomandos disponibles: "
                + ", ".join(self.nombres_disponibles())
            )

        return self._comandos[nombre]

    def nombres_disponibles(self) -> List[str]:
        """Devuelve los nombres registrados, en orden de inscripcion."""
        return list(self._comandos.keys())

    def todos(self) -> List[Comando]:
        """Devuelve todos los subcomandos, en orden de inscripcion."""
        return list(self._comandos.values())