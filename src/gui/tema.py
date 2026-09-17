"""Paleta y constantes visuales de la ventana de juego."""

from typing import List


# Colores de fondo de la ventana y los paneles.
COLOR_FONDO_VENTANA = "#1e1e2e"
COLOR_TEXTO_PRIMARIO = "#f0f0f5"
COLOR_TEXTO_SECUNDARIO = "#a0a0b8"
COLOR_CELDA_VACIA = "#3a3a52"
COLOR_BORDE = "#50506e"
COLOR_ACENTO = "#7aa2f7"

# Paleta usada para pintar las fichas segun su color. El indice 0 nunca se usa
# porque el color 0 representa una celda vacia.
PALETA_COLORES_FICHA: List[str] = [
    COLOR_CELDA_VACIA,
    "#f7768e",
    "#9ece6a",
    "#7aa2f7",
    "#e0af68",
    "#bb9af7",
    "#7dcfff",
    "#ff9e64",
    "#73daca",
    "#c0caf5",
    "#f7c8e0",
]

# Tipografias reutilizadas por la ventana.
FUENTE_SUBTITULO = ("Segoe UI", 12)
FUENTE_BOTON = ("Segoe UI", 11, "bold")
FUENTE_CELDA = ("Consolas", 13, "bold")
FUENTE_ESTADO = ("Segoe UI", 10)


def color_de_ficha(color_ficha: int) -> str:
    """
    Devuelve el color hexadecimal asociado a un color de ficha.

    Si K supera el tamano de la paleta, esta se recorre de forma circular.
    """
    if color_ficha <= 0:
        return COLOR_CELDA_VACIA

    cantidad_colores_disponibles = len(PALETA_COLORES_FICHA) - 1
    indice = ((color_ficha - 1) % cantidad_colores_disponibles) + 1

    return PALETA_COLORES_FICHA[indice]