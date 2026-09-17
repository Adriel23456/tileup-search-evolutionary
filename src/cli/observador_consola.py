"""Observador que reporta el avance de una partida por salida estandar."""

import sys

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion
from src.dominio.resultado_colocacion import ResultadoColocacion
from src.partidas.observador import ObservadorPartida


# Ancho en caracteres de la barra de progreso textual.
ANCHO_BARRA_PROGRESO = 30


class ObservadorConsola(ObservadorPartida):
    """
    Dibuja una barra de progreso textual mientras avanza la partida.

    Es una implementacion mas de ObservadorPartida, exactamente igual a la
    vista grafica desde el punto de vista de la sesion. Esto demuestra que la
    logica del juego no depende de ninguna capa de presentacion.
    """

    def __init__(self, mostrar_detalle: bool = False) -> None:
        """Construye el observador, opcionalmente con detalle por jugada."""
        self._mostrar_detalle = mostrar_detalle
        self._fichas_totales = 0

    def al_iniciar(self, estado: EstadoPartida) -> None:
        """Guarda el total de fichas y dibuja la barra vacia."""
        self._fichas_totales = estado.instancia.cantidad_fichas
        self._dibujar_barra(0)

    def al_colocar(self, estado: EstadoPartida,
                   resultado: ResultadoColocacion) -> None:
        """Actualiza la barra tras cada colocacion."""
        if self._mostrar_detalle is True:
            print(resultado.descripcion())
            return

        self._dibujar_barra(estado.cantidad_colocadas)

    def al_terminar(self, estado: EstadoPartida,
                    terminacion: EstadoTerminacion) -> None:
        """Cierra la linea de la barra al terminar la partida."""
        if self._mostrar_detalle is False:
            self._dibujar_barra(estado.cantidad_colocadas)

        sys.stdout.write("\n")
        sys.stdout.flush()

    def _dibujar_barra(self, cantidad_colocadas: int) -> None:
        """Redibuja la barra de progreso en la misma linea de la consola."""
        if self._fichas_totales <= 0:
            return

        proporcion = cantidad_colocadas / self._fichas_totales
        segmentos_llenos = int(proporcion * ANCHO_BARRA_PROGRESO)
        segmentos_vacios = ANCHO_BARRA_PROGRESO - segmentos_llenos

        barra = "[" + ("#" * segmentos_llenos) + ("-" * segmentos_vacios) + "]"
        texto_progreso = (
            barra + " " + str(cantidad_colocadas)
            + "/" + str(self._fichas_totales)
        )

        sys.stdout.write("\r" + texto_progreso)
        sys.stdout.flush()