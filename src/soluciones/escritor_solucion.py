"""
Escritura del formato de solucion definido en el enunciado.

Formato:
  - Una linea por colocacion con tres enteros: indice de ficha, fila, columna.
  - Ultima linea con el resumen, comenzando con '#'.
"""

import os
from typing import List

from src.metricas.metricas_partida import MetricasPartida
from src.soluciones.registro_solucion import RegistroSolucion


class EscritorSolucion:
    """
    Convierte un RegistroSolucion en un archivo de solucion.

    Al igual que el lector de instancias, es la unica clase que conoce el
    formato de salida.
    """

    def escribir(self, ruta_archivo: str, registro: RegistroSolucion,
                 metricas: MetricasPartida) -> None:
        """Escribe el archivo de solucion en la ruta indicada."""
        directorio = os.path.dirname(os.path.abspath(ruta_archivo))

        if os.path.isdir(directorio) is False:
            os.makedirs(directorio, exist_ok=True)

        contenido = self.generar_texto(registro, metricas)

        with open(ruta_archivo, "w", encoding="utf-8", newline="\n") as archivo:
            archivo.write(contenido)

    def generar_texto(self, registro: RegistroSolucion,
                      metricas: MetricasPartida) -> str:
        """Genera el contenido completo del archivo de solucion."""
        lineas: List[str] = []

        for indice_ficha, fila, columna in registro.colocaciones():
            lineas.append(
                str(indice_ficha) + " " + str(fila) + " " + str(columna)
            )

        linea_resumen = (
            "# colocadas=" + str(metricas.fichas_colocadas)
            + " ocupadas=" + str(metricas.celdas_ocupadas)
            + " mayor=" + str(metricas.valor_ficha_mayor)
        )
        lineas.append(linea_resumen)

        return "\n".join(lineas) + "\n"