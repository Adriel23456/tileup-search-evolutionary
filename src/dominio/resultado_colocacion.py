"""Resultado inmutable de aplicar una colocacion sobre el tablero."""

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ResultadoColocacion:
    """
    Describe todo lo que ocurrio al colocar una ficha.

    Se devuelve al llamador en lugar de que este tenga que volver a
    inspeccionar el tablero. Esto mantiene el motor como unica fuente
    de verdad de las reglas.
    """

    indice_ficha: int
    fila: int
    columna: int
    color: int
    hubo_fusion: bool
    tamano_componente: int
    valor_resultante: int
    celdas_fusionadas: Tuple[Tuple[int, int], ...] = field(default_factory=tuple)

    def descripcion(self) -> str:
        """Genera un texto corto para bitacoras y para la GUI."""
        if self.hubo_fusion is True:
            return (
                "Ficha " + str(self.indice_ficha)
                + " colocada en (" + str(self.fila) + ", " + str(self.columna) + ")"
                + " y fusiono " + str(self.tamano_componente) + " fichas"
                + " en un valor de " + str(self.valor_resultante)
            )

        return (
            "Ficha " + str(self.indice_ficha)
            + " colocada en (" + str(self.fila) + ", " + str(self.columna) + ")"
            + " sin fusion"
        )