"""
Registro de agentes disponibles para la linea de comandos.

Centraliza la construccion de agentes para que agregar uno nuevo no obligue a
modificar la capa de consola. Esto cumple el Principio Abierto/Cerrado: el
sistema se extiende registrando, no editando.

Convencion de nombrado de los agentes. Todos los agentes de busqueda son el
mismo algoritmo A*; lo unico que cambia entre ellos es la heuristica. Por eso
el nombre se forma como busqueda_<heuristica>, de modo que el nombre del
agente, el nombre del directorio de soluciones y el nombre de la heuristica
digan siempre lo mismo.
"""

from typing import Callable, Dict, List

from src.agentes.agente import Agente
from src.agentes.agente_aleatorio import AgenteAleatorio
from src.agentes.agente_busqueda import AgenteBusquedaAEstrella
from src.agentes.agente_evolutivo import AgenteEvolutivo
from src.agentes.heuristicas import HeuristicaCero, HeuristicaColoresPendientes


# Firma que debe cumplir todo constructor registrado.
ConstructorAgente = Callable[[int], Agente]

# Nombre del agente de busqueda que el enunciado exige y que compite.
NOMBRE_AGENTE_BUSQUEDA = "busqueda_astar"

# Nombre del agente de busqueda que sirve de linea base en el informe.
NOMBRE_AGENTE_DIJKSTRA = "busqueda_dijkstra"

# Nombre del agente evolutivo exigido por el enunciado.
NOMBRE_AGENTE_EVOLUTIVO = "evolutivo"

# Nombre del agente de linea base que coloca al azar.
NOMBRE_AGENTE_ALEATORIO = "aleatorio"


class ErrorAgenteDesconocido(Exception):
    """Se lanza cuando se solicita un agente que no esta registrado."""


class RegistroAgentes:
    """Tabla de agentes disponibles, indexada por su nombre en consola."""

    def __init__(self) -> None:
        """Crea el registro con los agentes implementados."""
        self._constructores: Dict[str, ConstructorAgente] = {}
        self._registrar_agentes_disponibles()

    def _registrar_agentes_disponibles(self) -> None:
        """Inscribe cada agente bajo su nombre de consola."""
        self.registrar(NOMBRE_AGENTE_ALEATORIO, self._construir_aleatorio)
        self.registrar(NOMBRE_AGENTE_BUSQUEDA, self._construir_busqueda_astar)
        self.registrar(NOMBRE_AGENTE_DIJKSTRA, self._construir_busqueda_dijkstra)
        self.registrar(NOMBRE_AGENTE_EVOLUTIVO, self._construir_evolutivo)

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
        """
        Construye el agente de linea base que coloca al azar.

        No es el agente que exige el enunciado. Sirve de piso de comparacion
        en el informe: la busqueda informada debe superarlo siempre.
        """
        return AgenteAleatorio(semilla=semilla)

    def _construir_busqueda_astar(self, semilla: int) -> Agente:
        """
        Construye el agente de busqueda del enunciado.

        Es A* con la heuristica admisible de colores pendientes, y es el
        agente que compite.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            nombre=NOMBRE_AGENTE_BUSQUEDA,
            heuristica=HeuristicaColoresPendientes(),
        )

    def _construir_busqueda_dijkstra(self, semilla: int) -> Agente:
        """
        Construye A* con heuristica nula, que es el algoritmo de Dijkstra.

        Existe solo como linea base del informe, para medir con numeros
        propios cuantos nodos ahorra la heuristica informada.
        """
        return AgenteBusquedaAEstrella(
            semilla=semilla,
            nombre=NOMBRE_AGENTE_DIJKSTRA,
            heuristica=HeuristicaCero(),
        )

    def _construir_evolutivo(self, semilla: int) -> Agente:
        """Construye el algoritmo genetico de estado estacionario."""
        return AgenteEvolutivo(semilla=semilla)
