"""Representacion en memoria de una instancia de TileUp."""

from typing import Sequence

from src.dominio.ficha import Ficha


class Instancia:
    """
    Agrupa los parametros fijos de una partida.

    Contiene N (dimension del tablero), K (cantidad de colores) y la secuencia
    fija de M fichas. Todos permanecen constantes durante la partida.
    """

    def __init__(self, dimension: int, cantidad_colores: int,
                 fichas: Sequence[Ficha], nombre: str = "sin_nombre") -> None:
        """Construye la instancia validando sus invariantes."""
        if dimension < 1:
            raise ValueError(
                "N debe ser mayor o igual a 1, se recibio: " + str(dimension)
            )

        if cantidad_colores < 1:
            raise ValueError(
                "K debe ser mayor o igual a 1, se recibio: "
                + str(cantidad_colores)
            )

        for posicion in range(len(fichas)):
            ficha_actual = fichas[posicion]

            if ficha_actual.color > cantidad_colores:
                raise ValueError(
                    "La ficha en la posicion " + str(posicion)
                    + " tiene color " + str(ficha_actual.color)
                    + " pero K vale " + str(cantidad_colores)
                )

        self._dimension = dimension
        self._cantidad_colores = cantidad_colores
        self._fichas = tuple(fichas)
        self._nombre = nombre

    @property
    def dimension(self) -> int:
        """Devuelve N."""
        return self._dimension

    @property
    def cantidad_colores(self) -> int:
        """Devuelve K."""
        return self._cantidad_colores

    @property
    def cantidad_fichas(self) -> int:
        """Devuelve M."""
        return len(self._fichas)

    @property
    def nombre(self) -> str:
        """Devuelve el nombre de la instancia, util para nombrar soluciones."""
        return self._nombre

    def obtener_ficha(self, indice: int) -> Ficha:
        """Devuelve la ficha en la posicion indicada de la secuencia."""
        if indice < 0:
            raise IndexError("El indice de ficha no puede ser negativo")

        if indice >= len(self._fichas):
            raise IndexError(
                "Indice de ficha fuera de rango: " + str(indice)
            )

        return self._fichas[indice]

    def resumen(self) -> str:
        """Genera una linea de resumen para la consola y la ventana de juego."""
        return (
            self._nombre
            + "  (N=" + str(self._dimension)
            + ", K=" + str(self._cantidad_colores)
            + ", M=" + str(self.cantidad_fichas) + ")"
        )