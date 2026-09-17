"""Subcomando que lista los agentes registrados."""

import argparse

from src.cli.comando import Comando
from src.cli.ejecutor_consola import EjecutorConsola


class ComandoAgentes(Comando):
    """Imprime los nombres de agente aceptados por el subcomando resolver."""

    def __init__(self) -> None:
        """Construye el comando con su ejecutor de consola."""
        self._ejecutor = EjecutorConsola()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "agentes"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Lista los agentes disponibles."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Este subcomando no recibe argumentos propios."""
        return None

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Delega el listado en el ejecutor de consola."""
        return self._ejecutor.listar_agentes()