"""Definicion de la ficha, la unidad minima del juego TileUp."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Ficha:
    """
    Representa una ficha del juego.

    Una ficha es un par <color, valor>:
      - color: entero en el rango 1..K que identifica el grupo de fusion.
      - valor: entero positivo que se suma al fusionar.

    La clase es inmutable (frozen) para que ningun agente pueda
    modificar la secuencia de la instancia por accidente.
    """

    color: int
    valor: int

    def __post_init__(self) -> None:
        """Valida los invariantes de la ficha al construirla."""
        if self.color < 1:
            raise ValueError(
                "El color de una ficha debe ser un entero mayor o igual a 1, "
                "se recibio: " + str(self.color)
            )

        if self.valor < 1:
            raise ValueError(
                "El valor de una ficha debe ser un entero positivo, "
                "se recibio: " + str(self.valor)
            )

    def __str__(self) -> str:
        """Representacion legible para mensajes de consola y GUI."""
        return "Ficha(color=" + str(self.color) + ", valor=" + str(self.valor) + ")"