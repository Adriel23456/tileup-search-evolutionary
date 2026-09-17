"""
Contrato comun de los agentes automaticos.

Todavia no hay implementaciones concretas: en esta etapa solo se define la
abstraccion para que el agente de busqueda y el evolutivo se conecten despues
sin tocar el motor, la sesion ni la GUI.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

from src.dominio.estado_partida import EstadoPartida


class Agente(ABC):
    """
    Interfaz minima que debe cumplir todo agente automatico.

    Se mantiene deliberadamente pequena, siguiendo el Principio de Segregacion
    de Interfaces: un agente solo necesita saber planificar y reportar su
    esfuerzo, nada mas.
    """

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre corto del agente, usado en metricas y rutas de salida."""

    @property
    @abstractmethod
    def nombre_medida_esfuerzo(self) -> str:
        """
        Nombre de la medida de esfuerzo del algoritmo.

        Por ejemplo 'nodos_expandidos' o 'evaluaciones_aptitud'.
        """

    @abstractmethod
    def planificar(self, estado_inicial: EstadoPartida,
                   limite_tiempo_segundos: float) -> List[Tuple[int, int]]:
        """
        Devuelve la secuencia de colocaciones que el agente decidio.

        Cada elemento es una tupla (fila, columna) y corresponde, en orden, a
        las fichas de la secuencia. Si el limite de tiempo se agota, el agente
        devuelve la mejor secuencia parcial encontrada hasta ese momento.
        """

    @abstractmethod
    def esfuerzo_acumulado(self) -> int:
        """Devuelve el esfuerzo consumido en la ultima planificacion."""