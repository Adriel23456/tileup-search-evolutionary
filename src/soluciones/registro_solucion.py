"""Acumulador de las colocaciones realizadas durante una partida."""

from typing import List, Tuple

from src.dominio.resultado_colocacion import ResultadoColocacion


class RegistroSolucion:
    """
    Guarda la secuencia de colocaciones de una partida.

    Se llena incrementalmente durante el juego y luego se entrega al escritor
    de soluciones. Separar el acumulado de la escritura permite reutilizar el
    mismo registro para la ventana de juego, la bitacora y el archivo de
    solucion.
    """

    def __init__(self) -> None:
        """Crea un registro vacio."""
        self._colocaciones: List[Tuple[int, int, int]] = []

    def agregar(self, resultado: ResultadoColocacion) -> None:
        """Agrega una colocacion al registro."""
        self._colocaciones.append(
            (resultado.indice_ficha, resultado.fila, resultado.columna)
        )

    def colocaciones(self) -> List[Tuple[int, int, int]]:
        """Devuelve una copia de la lista de colocaciones registradas."""
        return list(self._colocaciones)