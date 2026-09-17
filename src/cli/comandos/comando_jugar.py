"""Subcomando que abre la ventana de juego para una persona."""

import argparse
import sys

from src.cli.codigos_salida import (
    CODIGO_SALIDA_ERROR_ENTRADA,
    CODIGO_SALIDA_EXITO,
)
from src.cli.comando import Comando
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.lector_instancia import LectorInstancia


# Instancia que se carga cuando no se indica ninguna.
RUTA_INSTANCIA_POR_DEFECTO = "datos/instancias/ejemplo_n4_k3_m6.txt"

# Nombre del jugador cuando no se indica ninguno.
NOMBRE_JUGADOR_POR_DEFECTO = "humano"

# Numero de partida cuando no se indica ninguno.
NUMERO_PARTIDA_POR_DEFECTO = 0


class ComandoJugar(Comando):
    """
    Abre la interfaz grafica para que una persona juegue una partida.

    Es el unico comando del programa que toca la capa grafica, y la importa
    dentro de ejecutar, no en la cabecera del modulo. Gracias a esa
    importacion tardia, resolver una instancia o validar una solucion nunca
    carga Tkinter: la separacion entre jugar y ejecutar agentes se mantiene
    aunque ambos compartan punto de entrada.
    """

    def __init__(self) -> None:
        """Construye el comando con su lector de instancias."""
        self._lector_instancia = LectorInstancia()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "jugar"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Abre la ventana de juego para jugar una partida."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Declara los argumentos propios del juego humano."""
        analizador.add_argument(
            "--instancia",
            type=str,
            default=RUTA_INSTANCIA_POR_DEFECTO,
            help="Ruta del archivo de instancia que se va a jugar.",
        )

        analizador.add_argument(
            "--jugador",
            type=str,
            default=NOMBRE_JUGADOR_POR_DEFECTO,
            help="Nombre que se registra en la bitacora de partidas humanas.",
        )

        analizador.add_argument(
            "--partida",
            type=int,
            default=NUMERO_PARTIDA_POR_DEFECTO,
            help=(
                "Numero de partida. Distingue varios intentos de la misma "
                "persona sobre la misma instancia en el nombre del archivo."
            ),
        )

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Carga la instancia solicitada y abre la ventana de juego."""
        try:
            instancia = self._lector_instancia.leer_desde_archivo(
                argumentos.instancia
            )
        except ErrorFormatoInstancia as error_de_formato:
            print(
                "Instancia invalida: " + str(error_de_formato),
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        from src.gui.ventana_juego import VentanaJuego

        ventana = VentanaJuego(
            instancia=instancia,
            nombre_jugador=argumentos.jugador,
            numero_partida=argumentos.partida,
        )
        ventana.ejecutar()

        return CODIGO_SALIDA_EXITO