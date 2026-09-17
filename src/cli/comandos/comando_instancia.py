"""Subcomando que revisa el formato de un archivo de instancia."""

import argparse

from src.cli.comando import Comando
from src.cli.ejecutor_consola import EjecutorConsola


class ComandoInstancia(Comando):
    """
    Valida el formato de una instancia sin resolver nada.

    Sirve para comprobar que un archivo escrito a mano o producido por el
    generador cumple la especificacion antes de gastar tiempo de computo en
    el.
    """

    def __init__(self) -> None:
        """Construye el comando con su ejecutor de consola."""
        self._ejecutor = EjecutorConsola()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "instancia"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Revisa el formato de un archivo de instancia."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Declara los argumentos propios de la revision."""
        analizador.add_argument(
            "--instancia",
            type=str,
            required=True,
            help="Ruta del archivo de instancia que se va a revisar.",
        )

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Delega la revision en el ejecutor de consola."""
        return self._ejecutor.revisar_instancia(argumentos.instancia)