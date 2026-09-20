"""Contrato de observacion del avance de una partida."""

from abc import ABC, abstractmethod

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion
from src.dominio.resultado_colocacion import ResultadoColocacion


class ObservadorPartida(ABC):
    """
    Interfaz que permite observar una partida sin acoplarla a la interfaz
    grafica.

    Cumple el Principio de Inversion de Dependencias: la sesion de partida
    depende de esta abstraccion, no de Tkinter. La barra de progreso de la
    consola y la ventana de juego son dos implementaciones de esta misma
    interfaz, y la sesion no distingue cual la esta observando.
    """

    @abstractmethod
    def al_iniciar(self, estado: EstadoPartida) -> None:
        """Se invoca una vez antes de la primera colocacion."""

    @abstractmethod
    def al_colocar(self, estado: EstadoPartida,
                   resultado: ResultadoColocacion) -> None:
        """Se invoca despues de cada colocacion aplicada con exito."""

    @abstractmethod
    def al_terminar(self, estado: EstadoPartida,
                    terminacion: EstadoTerminacion) -> None:
        """Se invoca una vez cuando la partida llega a su condicion de termino."""