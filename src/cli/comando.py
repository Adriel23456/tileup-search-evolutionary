"""
Contrato comun de los subcomandos de la linea de comandos.

Cada subcomando del programa es una clase que cumple esta interfaz. La
consecuencia practica es que agregar un subcomando nuevo no obliga a tocar
main.py ni ningun otro comando: basta escribir la clase e inscribirla en el
registro.

La interfaz se mantiene deliberadamente pequena, con tres miembros, siguiendo
el Principio de Segregacion de Interfaces.
"""

import argparse
from abc import ABC, abstractmethod


class Comando(ABC):
    """Interfaz que debe cumplir todo subcomando del programa."""

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando desde la consola."""

    @property
    @abstractmethod
    def ayuda(self) -> str:
        """Descripcion corta que aparece en la ayuda del programa."""

    @abstractmethod
    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """
        Declara los argumentos propios del subcomando.

        Recibe el analizador ya creado para este subcomando, de modo que cada
        comando define solo lo suyo y no conoce los argumentos de los demas.
        """

    @abstractmethod
    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Ejecuta el subcomando y devuelve el codigo de salida del proceso."""