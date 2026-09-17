"""Subcomando que resuelve una instancia con uno o varios agentes."""

import argparse
import sys

from src.cli.codigos_salida import CODIGO_SALIDA_ERROR_ENTRADA
from src.cli.comando import Comando
from src.cli.ejecutor_consola import EjecutorConsola


# Limite de tiempo por defecto en segundos cuando no se indica otro.
LIMITE_TIEMPO_POR_DEFECTO = 10.0

# Semilla por defecto cuando no se indica otra.
SEMILLA_POR_DEFECTO = 0


class ComandoResolver(Comando):
    """
    Ejecuta agentes sobre una instancia.

    Este subcomando implementa el contrato de ejecucion exigido por el
    enunciado: recibe la ruta de la instancia, el agente que debe usarse, la
    semilla y el limite de tiempo en segundos, sin pasos interactivos ni
    edicion de archivos.
    """

    def __init__(self) -> None:
        """Construye el comando con su ejecutor de consola."""
        self._ejecutor = EjecutorConsola()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "resolver"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Resuelve una instancia con uno o varios agentes."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Declara los argumentos propios de la resolucion."""
        analizador.add_argument(
            "--instancia",
            type=str,
            required=True,
            help="Ruta del archivo de instancia.",
        )

        analizador.add_argument(
            "--agente",
            type=str,
            default=None,
            help="Nombre del agente que debe resolver la instancia.",
        )

        analizador.add_argument(
            "--agentes",
            type=str,
            nargs="+",
            default=None,
            help=(
                "Lista de agentes que resuelven la misma instancia, uno tras "
                "otro, para la comparacion experimental."
            ),
        )

        analizador.add_argument(
            "--semilla",
            type=int,
            default=SEMILLA_POR_DEFECTO,
            help="Semilla que fija toda fuente de azar del agente.",
        )

        analizador.add_argument(
            "--limite-tiempo",
            type=float,
            default=LIMITE_TIEMPO_POR_DEFECTO,
            dest="limite_tiempo",
            help="Limite de tiempo de planificacion, en segundos.",
        )

        analizador.add_argument(
            "--salida",
            type=str,
            default=None,
            help=(
                "Ruta del archivo de solucion. Solo aplica con --agente. Si "
                "se omite, se usa la convencion de nombrado del repositorio."
            ),
        )

        analizador.add_argument(
            "--silencioso",
            action="store_true",
            help="Omite la barra de progreso y deja solo las metricas.",
        )

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Despacha hacia la ejecucion de uno o de varios agentes."""
        if argumentos.agente is not None and argumentos.agentes is not None:
            print(
                "Use --agente o --agentes, pero no ambos a la vez",
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        if argumentos.agente is None and argumentos.agentes is None:
            print(
                "Debe indicar un agente con --agente o varios con --agentes",
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        if argumentos.agente is not None:
            return self._ejecutor.ejecutar_agente(
                ruta_instancia=argumentos.instancia,
                nombre_agente=argumentos.agente,
                semilla=argumentos.semilla,
                limite_tiempo_segundos=argumentos.limite_tiempo,
                ruta_salida=argumentos.salida,
                silencioso=argumentos.silencioso,
            )

        return self._ejecutor.ejecutar_comparacion(
            ruta_instancia=argumentos.instancia,
            nombres_agentes=argumentos.agentes,
            semilla=argumentos.semilla,
            limite_tiempo_segundos=argumentos.limite_tiempo,
            silencioso=argumentos.silencioso,
        )