"""Resultado inmutable de aplicar una colocacion sobre el tablero."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoColocacion:
    """
    Describe lo que ocurrio al colocar una ficha.

    Se devuelve al llamador en lugar de que este tenga que volver a
    inspeccionar el tablero. Asi el motor sigue siendo la unica fuente de
    verdad de las reglas.
    """

    indice_ficha: int
    fila: int
    columna: int
    hubo_fusion: bool
    tamano_componente: int
    valor_resultante: int