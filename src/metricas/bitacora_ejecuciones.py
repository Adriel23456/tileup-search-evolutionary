"""
Bitacora acumulada de las ejecuciones de agentes.

Cada vez que un agente resuelve una instancia por linea de comandos se agrega
una fila a un CSV. Esa acumulacion es la materia prima de la comparacion
experimental del informe, que el enunciado exige presentar por agente y por
instancia, con dispersion entre semillas.

Escribir la fila en el momento de la ejecucion, y no al final en un guion
aparte, garantiza que lo reportado sea exactamente lo que el programa
informo por salida estandar.
"""

import csv
import datetime
import os
from typing import List

from src.metricas.metricas_partida import MetricasPartida


# Encabezado del CSV de comparacion. Su orden debe coincidir con el de
# MetricasPartida.como_fila_csv.
ENCABEZADO_COMPARACION = [
    "agente",
    "instancia",
    "n",
    "k",
    "m",
    "semilla",
    "resultado",
    "colocadas",
    "ocupadas",
    "mayor",
    "tiempo_s",
    "esfuerzo",
    "nombre_esfuerzo",
]

# Columnas que la bitacora agrega por su cuenta, al final de cada fila.
COLUMNAS_ADICIONALES = [
    "marca_de_tiempo",
    "archivo_solucion",
]


class BitacoraEjecuciones:
    """Acumula una fila de CSV por cada ejecucion de un agente."""

    def __init__(self, ruta_bitacora: str) -> None:
        """Construye la bitacora asegurando que el archivo exista."""
        self._ruta_bitacora = ruta_bitacora
        self._asegurar_archivo()

    def registrar(self, metricas: MetricasPartida,
                  archivo_solucion: str) -> None:
        """Agrega una fila con el resultado de una ejecucion."""
        marca_de_tiempo = datetime.datetime.now().isoformat(timespec="seconds")

        fila: List[str] = metricas.como_fila_csv()
        fila.append(marca_de_tiempo)
        fila.append(archivo_solucion)

        with open(self._ruta_bitacora, "a", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo, lineterminator="\n")
            escritor.writerow(fila)

    def _asegurar_archivo(self) -> None:
        """Crea el archivo y su encabezado si todavia no existen."""
        directorio = os.path.dirname(os.path.abspath(self._ruta_bitacora))

        if os.path.isdir(directorio) is False:
            os.makedirs(directorio, exist_ok=True)

        if os.path.isfile(self._ruta_bitacora) is True:
            return

        encabezado = list(ENCABEZADO_COMPARACION) + list(COLUMNAS_ADICIONALES)

        with open(self._ruta_bitacora, "w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo, lineterminator="\n")
            escritor.writerow(encabezado)