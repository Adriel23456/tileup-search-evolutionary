"""
Escritura del formato de instancia definido en el enunciado.

Formato:
  - Una linea con N y K separados por espacio.
  - Una linea con M.
  - M lineas con el color y el valor de cada ficha, en orden.

Es el espejo de LectorInstancia: juntos son los unicos modulos que conocen el
formato de entrada. Las lineas de comentario que encabezan el archivo son
opcionales segun el formato, y aqui se usan para dejar constancia de los
parametros con que se genero, de modo que cualquiera pueda reproducirlo.
"""

import os
from typing import List

from src.instancias.instancia import Instancia


class EscritorInstancia:
    """Convierte un objeto Instancia en un archivo de texto del formato oficial."""

    def escribir(self, ruta_archivo: str, instancia: Instancia,
                 semilla: int) -> None:
        """Escribe el archivo de instancia en la ruta indicada."""
        directorio = os.path.dirname(os.path.abspath(ruta_archivo))

        if os.path.isdir(directorio) is False:
            os.makedirs(directorio, exist_ok=True)

        contenido = self.generar_texto(instancia, semilla)

        # El salto de linea se fija a '\n' para que dos corridas con la misma
        # semilla produzcan el mismo archivo byte a byte en cualquier sistema.
        with open(ruta_archivo, "w", encoding="utf-8", newline="\n") as archivo:
            archivo.write(contenido)

    def generar_texto(self, instancia: Instancia, semilla: int) -> str:
        """Genera el contenido completo del archivo de instancia."""
        lineas: List[str] = []

        lineas.append("# TileUp -- instancia generada")
        lineas.append(
            "# generador: n=" + str(instancia.dimension)
            + " k=" + str(instancia.cantidad_colores)
            + " m=" + str(instancia.cantidad_fichas)
            + " semilla=" + str(semilla)
        )
        lineas.append(
            str(instancia.dimension) + " " + str(instancia.cantidad_colores)
        )
        lineas.append(str(instancia.cantidad_fichas))

        for indice_ficha in range(instancia.cantidad_fichas):
            ficha = instancia.obtener_ficha(indice_ficha)
            lineas.append(str(ficha.color) + " " + str(ficha.valor))

        return "\n".join(lineas) + "\n"
