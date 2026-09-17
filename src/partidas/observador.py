"""Contrato de observacion del avance de una partida."""

from abc import ABC, abstractmethod

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion
from src.dominio.resultado_colocacion import ResultadoColocacion


class ObservadorPartida(ABC):
    """
    Interfaz que permite observar una partida sin acoplarla a la GUI.

    Cumple el Principio de Inversion de Dependencias: la sesion de partida
    depende de esta abstraccion, no de Tkinter. Mas adelante la barra de
    progreso de los agentes sera simplemente otra implementacion de esta
    misma interfaz.
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


class ObservadorSilencioso(ObservadorPartida):
    """
    Implementacion vacia de ObservadorPartida.

    Sirve como objeto nulo cuando no interesa observar nada, por ejemplo en
    las pruebas automatizadas.
    """

    def al_iniciar(self, estado: EstadoPartida) -> None:
        """No hace nada."""
        return None

    def al_colocar(self, estado: EstadoPartida,
                   resultado: ResultadoColocacion) -> None:
        """No hace nada."""
        return None

    def al_terminar(self, estado: EstadoPartida,
                    terminacion: EstadoTerminacion) -> None:
        """No hace nada."""
        return None