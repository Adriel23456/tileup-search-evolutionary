"""Bitacora de partidas jugadas por una persona."""

import csv
import datetime
import os
from typing import List

from src.metricas.metricas_partida import MetricasPartida


# Encabezado del archivo CSV de la bitacora humana.
ENCABEZADO_BITACORA = [
    "marca_de_tiempo",
    "jugador",
    "instancia",
    "resultado",
    "colocadas",
    "totales",
    "ocupadas",
    "mayor",
    "tiempo_s",
    "archivo_solucion",
]


class RegistroHumano:
    """
    Escribe una fila por cada partida humana terminada.

    El objetivo es tener una linea base humana con la cual comparar el
    desempeno de los dos agentes en el informe final.
    """

    def __init__(self, ruta_bitacora: str) -> None:
        """Construye la bitacora asegurando que el archivo exista."""
        self._ruta_bitacora = ruta_bitacora
        self._asegurar_archivo()

    def registrar(self, metricas: MetricasPartida, jugador: str,
                  archivo_solucion: str) -> None:
        """Agrega una fila a la bitacora con el resultado de la partida."""
        marca_de_tiempo = datetime.datetime.now().isoformat(timespec="seconds")

        fila: List[str] = [
            marca_de_tiempo,
            jugador,
            metricas.nombre_instancia,
            metricas.resultado,
            str(metricas.fichas_colocadas),
            str(metricas.fichas_totales),
            str(metricas.celdas_ocupadas),
            str(metricas.valor_ficha_mayor),
            format(metricas.tiempo_segundos, ".3f"),
            archivo_solucion,
        ]

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

        with open(self._ruta_bitacora, "w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo, lineterminator="\n")
            escritor.writerow(ENCABEZADO_BITACORA)