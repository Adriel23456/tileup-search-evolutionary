"""
Capa de consola del sistema.

Implementa el requisito de ejecucion por linea de comandos: un unico punto de
entrada que recibe la ruta de la instancia, el agente, la semilla y el limite
de tiempo, sin pasos interactivos ni edicion de archivos.
"""

import os
import sys
from typing import Optional

from src.agentes.registro_agentes import (
    ErrorAgenteDesconocido,
    RegistroAgentes,
)
from src.cli import nombres_archivos
from src.cli.observador_consola import ObservadorConsola
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente


# Codigos de salida del programa.
CODIGO_SALIDA_EXITO = 0
CODIGO_SALIDA_ERROR_ENTRADA = 2
CODIGO_SALIDA_ERROR_AGENTE = 3


class EjecutorConsola:
    """Coordina una ejecucion completa solicitada desde la linea de comandos."""

    def __init__(self) -> None:
        """Construye la capa de consola con sus colaboradores."""
        self._lector_instancia = LectorInstancia()
        self._registro_agentes = RegistroAgentes()
        self._ejecutor_agente = EjecutorAgente()

    def ejecutar(self, ruta_instancia: str, nombre_agente: str, semilla: int,
                 limite_tiempo_segundos: float,
                 ruta_salida: Optional[str] = None,
                 silencioso: bool = False) -> int:
        """
        Corre un agente sobre una instancia y reporta el resultado.

        Devuelve el codigo de salida del proceso: cero si todo fue bien, un
        valor distinto de cero ante cualquier error controlado.
        """
        if limite_tiempo_segundos <= 0:
            print(
                "El limite de tiempo debe ser mayor que cero",
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        instancia = self._cargar_instancia(ruta_instancia)

        if instancia is None:
            return CODIGO_SALIDA_ERROR_ENTRADA

        try:
            agente = self._registro_agentes.construir(nombre_agente, semilla)
        except ErrorAgenteDesconocido as error_de_agente:
            print(str(error_de_agente), file=sys.stderr)
            return CODIGO_SALIDA_ERROR_AGENTE

        ruta_final = self._resolver_ruta_salida(
            ruta_salida, instancia.nombre, agente.nombre, semilla
        )

        if silencioso is True:
            observador = None
        else:
            observador = ObservadorConsola(mostrar_detalle=False)

        resultado = self._ejecutor_agente.ejecutar(
            agente=agente,
            instancia=instancia,
            semilla=semilla,
            limite_tiempo_segundos=limite_tiempo_segundos,
            ruta_solucion=ruta_final,
            observador=observador,
        )

        print(resultado.metricas.como_linea_estandar())
        print("solucion=" + resultado.ruta_solucion)

        if resultado.colocaciones_rechazadas > 0:
            print(
                "Advertencia: el agente propuso "
                + str(resultado.colocaciones_rechazadas)
                + " colocaciones ilegales que el motor rechazo",
                file=sys.stderr,
            )

        return CODIGO_SALIDA_EXITO

    def listar_agentes(self) -> int:
        """Imprime los agentes disponibles para la linea de comandos."""
        for nombre in self._registro_agentes.nombres_disponibles():
            print(nombre)

        return CODIGO_SALIDA_EXITO

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _cargar_instancia(self, ruta_instancia: str):
        """Lee la instancia informando un error legible si el archivo falla."""
        try:
            return self._lector_instancia.leer_desde_archivo(ruta_instancia)
        except ErrorFormatoInstancia as error_de_formato:
            print(
                "Instancia invalida: " + str(error_de_formato),
                file=sys.stderr,
            )
            return None

    def _resolver_ruta_salida(self, ruta_salida: Optional[str],
                              nombre_instancia: str, nombre_agente: str,
                              semilla: int) -> str:
        """Determina donde escribir la solucion segun la convencion vigente."""
        if ruta_salida is not None:
            return ruta_salida

        return nombres_archivos.ruta_solucion(
            nombre_instancia=nombre_instancia,
            nombre_agente=nombre_agente,
            semilla=semilla,
        )