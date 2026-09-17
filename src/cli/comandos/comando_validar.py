"""Subcomando que arbitra una solucion contra su instancia."""

import argparse
import sys

from src.cli.codigos_salida import (
    CODIGO_SALIDA_ERROR_ENTRADA,
    CODIGO_SALIDA_EXITO,
    CODIGO_SALIDA_VEREDICTO_NEGATIVO,
)
from src.cli.comando import Comando
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.lector_instancia import LectorInstancia
from src.validacion.errores import ErrorFormatoSolucion
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


class ComandoValidar(Comando):
    """
    Reproduce una partida guardada y dictamina si es legal.

    Es la herramienta con la que se arbitra el concurso. El comando es una
    capa delgada: la verificacion real ocurre en el paquete de validacion, que
    reimplementa las reglas por su cuenta y no comparte codigo de decision con
    ningun agente.
    """

    def __init__(self) -> None:
        """Construye el comando con sus lectores y el validador."""
        self._lector_instancia = LectorInstancia()
        self._lector_solucion = LectorSolucion()
        self._validador = Validador()

    @property
    def nombre(self) -> str:
        """Nombre con el que se invoca el subcomando."""
        return "validar"

    @property
    def ayuda(self) -> str:
        """Descripcion corta del subcomando."""
        return "Valida un archivo de solucion contra su instancia."

    def configurar_argumentos(self, analizador: argparse.ArgumentParser) -> None:
        """Declara los argumentos propios de la validacion."""
        analizador.add_argument(
            "--instancia",
            type=str,
            required=True,
            help="Ruta del archivo de instancia.",
        )

        analizador.add_argument(
            "--solucion",
            type=str,
            required=True,
            help="Ruta del archivo de solucion que se va a validar.",
        )

        analizador.add_argument(
            "--exigir-completa",
            action="store_true",
            dest="exigir_completa",
            help=(
                "Rechaza la solucion si no consume la secuencia entera. Sin "
                "esta opcion, una solucion incompleta pero legal se acepta."
            ),
        )

    def ejecutar(self, argumentos: argparse.Namespace) -> int:
        """Lee ambos archivos, valida e informa el dictamen."""
        try:
            instancia = self._lector_instancia.leer_desde_archivo(
                argumentos.instancia
            )
        except ErrorFormatoInstancia as error_de_instancia:
            print(
                "Instancia invalida: " + str(error_de_instancia),
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        try:
            solucion = self._lector_solucion.leer_desde_archivo(
                argumentos.solucion
            )
        except ErrorFormatoSolucion as error_de_solucion:
            print(
                "Solucion invalida: " + str(error_de_solucion),
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        dictamen = self._validador.validar(instancia, solucion)

        print("instancia=" + instancia.resumen())
        print("solucion=" + solucion.nombre)
        print(dictamen.como_texto())

        if dictamen.es_legal is False:
            return CODIGO_SALIDA_VEREDICTO_NEGATIVO

        if argumentos.exigir_completa is True:
            if dictamen.esta_completa is False:
                return CODIGO_SALIDA_VEREDICTO_NEGATIVO

        return CODIGO_SALIDA_EXITO