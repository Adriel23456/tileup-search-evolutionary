"""Estado completo de una partida de TileUp en un instante dado."""

from typing import Optional

from src.dominio.ficha import Ficha
from src.dominio.tablero import Tablero
from src.instancias.instancia import Instancia


class EstadoPartida:
    """
    Agrupa el tablero y el avance sobre la secuencia de fichas.

    Esta clase es un contenedor de datos con consultas derivadas. No aplica
    reglas: el motor es quien las aplica sobre un estado.
    """

    def __init__(self, instancia: Instancia, tablero: Optional[Tablero] = None,
                 indice_ficha_actual: int = 0) -> None:
        """Construye un estado, por defecto el estado inicial de la instancia."""
        self._instancia = instancia

        if tablero is None:
            self._tablero = Tablero(instancia.dimension)
        else:
            self._tablero = tablero

        self._indice_ficha_actual = indice_ficha_actual

    # ------------------------------------------------------------------
    # Accesores
    # ------------------------------------------------------------------

    @property
    def instancia(self) -> Instancia:
        """Devuelve la instancia que define esta partida."""
        return self._instancia

    @property
    def tablero(self) -> Tablero:
        """Devuelve el tablero actual."""
        return self._tablero

    @property
    def indice_ficha_actual(self) -> int:
        """Devuelve el indice de la proxima ficha por colocar."""
        return self._indice_ficha_actual

    @property
    def cantidad_colocadas(self) -> int:
        """
        Devuelve cuantas fichas se han colocado.

        Coincide con el indice de la ficha actual porque las fichas se
        consumen estrictamente en orden.
        """
        return self._indice_ficha_actual

    # ------------------------------------------------------------------
    # Consultas derivadas
    # ------------------------------------------------------------------

    def hay_fichas_pendientes(self) -> bool:
        """Indica si aun queda al menos una ficha por colocar."""
        return self._indice_ficha_actual < self._instancia.cantidad_fichas

    def ficha_pendiente(self) -> Optional[Ficha]:
        """Devuelve la proxima ficha por colocar, o None si ya no quedan."""
        if self.hay_fichas_pendientes() is False:
            return None

        return self._instancia.obtener_ficha(self._indice_ficha_actual)

    def ficha_siguiente_a_la_pendiente(self) -> Optional[Ficha]:
        """
        Devuelve la ficha posterior a la pendiente, o None si no existe.

        Es informacion legitima: el problema es completamente observable y el
        agente conoce toda la secuencia desde el inicio.
        """
        indice_siguiente = self._indice_ficha_actual + 1

        if indice_siguiente >= self._instancia.cantidad_fichas:
            return None

        return self._instancia.obtener_ficha(indice_siguiente)

    def avanzar_ficha(self) -> None:
        """Consume la ficha pendiente actual, avanzando el indice."""
        self._indice_ficha_actual = self._indice_ficha_actual + 1

    # ------------------------------------------------------------------
    # Copia
    # ------------------------------------------------------------------

    def copiar(self) -> "EstadoPartida":
        """Devuelve una copia independiente del estado."""
        return EstadoPartida(
            instancia=self._instancia,
            tablero=self._tablero.copiar(),
            indice_ficha_actual=self._indice_ficha_actual,
        )