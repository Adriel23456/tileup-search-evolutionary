"""
Registro de agentes disponibles para la linea de comandos.

Centraliza la construccion de agentes para que agregar uno nuevo no obligue a
modificar la capa de consola. Esto cumple el Principio Abierto/Cerrado: el
sistema se extiende registrando, no editando.
"""

from typing import Callable, Dict, List

from src.agentes.agente import Agente
from src.agentes.agente_aleatorio import AgenteAleatorio
from src.agentes.agente_busqueda import AgenteBusquedaAEstrella
from src.agentes.heuristicas import (
    HeuristicaCero,
    HeuristicaCompactacion,
    HeuristicaCotaLiberaciones,
)


# Firma que debe cumplir todo constructor registrado: recibe la semilla y
# devuelve una instancia lista para planificar.
ConstructorAgente = Callable[[int], Agente]


class ErrorAgenteDesconocido(Exception):
    """Se lanza cuando se solicita un agente que no esta registrado."""


class RegistroAgentes:
    """Tabla de agentes disponibles, indexada por su nombre en consola."""

    def __init__(self) -> None:
        """Crea el registro con los agentes disponibles en esta etapa."""
        self._constructores: Dict[str, ConstructorAgente] = {}
        self._registrar_agentes_disponibles()

    def _registrar_agentes_disponibles(self) -> None:
        """Inscribe cada agente implementado bajo su nombre de consola."""
        self.registrar("aleatorio", self._construir_aleatorio)
        self.registrar("busqueda", self._construir_busqueda)
        self.registrar("busqueda_exacta", self._construir_busqueda_exacta)
        self.registrar("busqueda_dijkstra", self._construir_busqueda_dijkstra)
        self.registrar("busqueda_agresiva", self._construir_busqueda_agresiva)

    def registrar(self, nombre: str, constructor: ConstructorAgente) -> None:
        """Inscribe un constructor bajo el nombre indicado."""
        self._constructores[nombre] = constructor

    def construir(self, nombre: str, semilla: int) -> Agente:
        """Devuelve una instancia nueva del agente solicitado."""
        if nombre not in self._constructores:
            raise ErrorAgenteDesconocido(
                "Agente desconocido: '" + str(nombre) + "'. "
                "Agentes disponibles: " + ", ".join(self.nombres_disponibles())
            )

        constructor = self._constructores[nombre]
        return constructor(semilla)

    def nombres_disponibles(self) -> List[str]:
        """Devuelve la lista ordenada de nombres registrados."""
        return sorted(self._constructores.keys())

    # ------------------------------------------------------------------
    # Constructores concretos
    # ------------------------------------------------------------------

    def _construir_aleatorio(self, semilla: int) -> Agente:
        """Construye el agente de linea base aleatorio."""
        return AgenteAleatorio(semilla=semilla)

    def _construir_busqueda(self, semilla: int) -> Agente:
        """
        Construye la configuracion de competencia del agente de busqueda.

        Heuristica admisible con poda de sucesores. Es la variante pensada
        para el concurso: no garantiza optimalidad, pero termina dentro del
        limite de tiempo en instancias de tamano realista.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            heuristica=HeuristicaCotaLiberaciones(),
            maximo_sucesores=6,
        )

    def _construir_busqueda_exacta(self, semilla: int) -> Agente:
        """
        Construye A* puro: heuristica admisible y sin poda de sucesores.

        Garantiza la solucion optima, pero solo termina en instancias
        pequenas. Es la referencia contra la cual se mide cuanto pierde la
        variante de competencia.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            heuristica=HeuristicaCotaLiberaciones(),
            maximo_sucesores=0,
        )

    def _construir_busqueda_dijkstra(self, semilla: int) -> Agente:
        """
        Construye A* con heuristica nula, es decir, Dijkstra.

        Sirve de linea base para medir cuanto trabajo ahorra la heuristica
        informada en el informe.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            heuristica=HeuristicaCero(),
            maximo_sucesores=0,
        )

    def _construir_busqueda_agresiva(self, semilla: int) -> Agente:
        """
        Construye A* con la heuristica NO admisible de compactacion.

        Expande muchos menos nodos a cambio de renunciar a la garantia de
        optimalidad.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            heuristica=HeuristicaCompactacion(peso_penalizacion=2),
            maximo_sucesores=6,
        )