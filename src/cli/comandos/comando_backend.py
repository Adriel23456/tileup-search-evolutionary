"""Subcomando que informa el backend de computo detectado."""

import argparse

from src.aceleracion.backend import DetectorBackend
from src.cli.codigos_salida import CODIGO_SALIDA_EXITO
from src.cli.comando import Comando


class ComandoBackend(Comando):
    """
    Muestra que capacidades de computo hay disponibles en la maquina.

    Es informativo: permite comprobar, antes de una tanda experimental, si la
    maquina ofrece un dispositivo CUDA utilizable o si el sistema correra
    integramente en CPU con NumPy.
    """

    def __init__(self) -> None:
        """Construye el comando con su detector de backend."""
        self._detector = DetectorBackend()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "backend"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Muestra el backend de computo detectado."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Este subcomando no recibe argumentos propios."""
        return None

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Detecta el backend e informa sus caracteristicas."""
        informacion = self._detector.detectar()

        print("backend=" + informacion.nombre)
        print("soporta_gpu=" + str(informacion.soporta_gpu))
        print("detalle=" + informacion.detalle)

        return CODIGO_SALIDA_EXITO