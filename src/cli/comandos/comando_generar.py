"""Subcomando que genera una instancia resoluble a partir de N, K, M y semilla."""

import argparse
import os
import sys

from src.cli.codigos_salida import (
    CODIGO_SALIDA_ERROR_ENTRADA,
    CODIGO_SALIDA_EXITO,
)
from src.cli.comando import Comando
from src.instancias.errores import ErrorParametrosGenerador
from src.instancias.escritor_instancia import EscritorInstancia
from src.instancias.generador_instancia import GeneradorInstancias
from src.nombrado import nombres_archivos


class ComandoGenerar(Comando):
    """
    Escribe un archivo de instancia nuevo en el formato del enunciado.

    El comando es una capa delgada: decide la ruta de salida e informa el
    resultado. La construccion de la instancia ocurre en GeneradorInstancias, y
    el formato del archivo lo conoce EscritorInstancia.
    """

    def __init__(self) -> None:
        """Construye el comando con el generador y el escritor."""
        self._generador = GeneradorInstancias()
        self._escritor = EscritorInstancia()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "generar"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Genera un archivo de instancia resoluble a partir de N, K, M y semilla."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Declara los argumentos propios de la generacion."""
        analizador.add_argument(
            "--n",
            type=int,
            required=True,
            help="Lado del tablero. Debe ser mayor o igual a 1.",
        )

        analizador.add_argument(
            "--k",
            type=int,
            required=True,
            help="Cantidad de colores. Debe ser mayor o igual a 1.",
        )

        analizador.add_argument(
            "--m",
            type=int,
            required=True,
            help="Cantidad de fichas de la secuencia. No puede ser negativa.",
        )

        analizador.add_argument(
            "--semilla",
            type=int,
            default=0,
            help=(
                "Fija toda fuente de azar del generador. Los mismos N, K, M y "
                "semilla producen siempre el mismo archivo."
            ),
        )

        analizador.add_argument(
            "--etiqueta",
            type=str,
            default=nombres_archivos.ETIQUETA_INSTANCIA_POR_DEFECTO,
            help=(
                "Familia a la que pertenece la instancia. Es el prefijo del "
                "patron <etiqueta>_s<semilla>_n<N>_k<K>_m<M>.txt."
            ),
        )

        analizador.add_argument(
            "--salida",
            type=str,
            default=None,
            help=(
                "Ruta del archivo que se va a escribir. Si se omite, se usa la "
                "convencion de nombrado dentro de datos/instancias."
            ),
        )

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Genera la instancia, la escribe e informa por salida estandar."""
        ruta_salida = self._resolver_ruta_salida(argumentos)

        # El nombre de la instancia es el del archivo sin extension, la misma
        # regla que aplica LectorInstancia al leerla, de modo que coincide con
        # el que despues aparece en las soluciones y en las bitacoras.
        nombre_instancia = os.path.splitext(os.path.basename(ruta_salida))[0]

        try:
            generada = self._generador.generar(
                dimension=argumentos.n,
                cantidad_colores=argumentos.k,
                cantidad_fichas=argumentos.m,
                semilla=argumentos.semilla,
                nombre=nombre_instancia,
            )
        except ErrorParametrosGenerador as error_de_parametros:
            print(
                "Parametros invalidos: " + str(error_de_parametros),
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        try:
            self._escritor.escribir(
                ruta_archivo=ruta_salida,
                instancia=generada.instancia,
                semilla=argumentos.semilla,
            )
        except OSError as error_de_escritura:
            print(
                "No se pudo escribir el archivo de instancia: "
                + str(error_de_escritura),
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        print("instancia=" + generada.instancia.resumen())
        print("semilla=" + str(argumentos.semilla))
        print("archivo=" + ruta_salida)
        print(
            "colocaciones_testigo=" + str(len(generada.colocaciones))
            + " (la instancia se construyo jugando una partida legal completa)"
        )

        return CODIGO_SALIDA_EXITO

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _resolver_ruta_salida(self, argumentos: argparse.Namespace) -> str:
        """Determina donde escribir la instancia segun la convencion vigente."""
        if argumentos.salida is not None:
            return argumentos.salida

        return nombres_archivos.ruta_instancia(
            etiqueta=argumentos.etiqueta,
            semilla=argumentos.semilla,
            dimension=argumentos.n,
            cantidad_colores=argumentos.k,
            cantidad_fichas=argumentos.m,
        )
