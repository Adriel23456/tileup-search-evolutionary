"""
Heuristicas del agente de busqueda.

Una heuristica h(n) estima el costo que falta para alcanzar la meta desde el
estado n. A* la suma al costo real ya pagado g(n) y ordena la lista abierta
por f(n) = g(n) + h(n).

Todas las heuristicas de este modulo trabajan en las mismas unidades que la
funcion de costo del agente:

    costo(a) = (N^2 - 1) - liberadas(a),  liberadas(a) = |G| - 1

Mezclar unidades entre g y h rompe A* en silencio, de modo que la unidad es
parte del contrato de esta interfaz.
"""

from abc import ABC, abstractmethod
from typing import Set

from src.dominio.estado_partida import EstadoPartida


class Heuristica(ABC):
    """Contrato comun de las heuristicas del agente de busqueda."""

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre corto de la heuristica, usado en el informe."""

    @property
    @abstractmethod
    def es_admisible(self) -> bool:
        """
        Indica si la heuristica nunca sobreestima el costo restante.

        Una heuristica admisible cumple h(n) <= h*(n) y garantiza que A*
        devuelve el camino optimo.
        """

    @abstractmethod
    def estimar(self, estado: EstadoPartida) -> int:
        """Devuelve el costo estimado desde el estado hasta la meta."""


class HeuristicaCero(Heuristica):
    """
    Heuristica nula: h(n) = 0 para todo estado.

    Es trivialmente admisible y convierte A* en el algoritmo de Dijkstra: la
    busqueda se ordena solo por el costo real acumulado, como se vio en clase.
    Sirve de linea base para medir cuanto trabajo ahorra la heuristica
    informada.
    """

    @property
    def nombre(self) -> str:
        """Nombre corto de la heuristica."""
        return "cero"

    @property
    def es_admisible(self) -> bool:
        """La heuristica nula nunca sobreestima."""
        return True

    def estimar(self, estado: EstadoPartida) -> int:
        """Devuelve siempre cero."""
        return 0


class HeuristicaColoresPendientes(Heuristica):
    """
    Heuristica admisible basada en los colores que faltan por colocar.

    Argumento completo, en tres pasos.

    Paso 1. El costo que falta es la suma, sobre las acciones restantes, de
    (N^2 - 1) - liberadas. Si quedan R fichas por colocar:

        costo_restante = R * (N^2 - 1) - liberaciones_futuras

    Paso 2. Por conservacion de celdas, cada ficha que se coloca ocupa una
    celda y cada fusion libera |G| - 1 celdas, de modo que:

        ocupadas_finales = ocupadas_ahora + R - liberaciones_futuras

    y por tanto:

        liberaciones_futuras = ocupadas_ahora + R - ocupadas_finales

    Acotar el costo por debajo equivale entonces a acotar ocupadas_finales
    por debajo.

    Paso 3. Cada color distinto que todavia aparece en la secuencia pendiente
    deja al menos una celda ocupada al terminar. Cuando se coloca la ultima
    ficha de ese color, nada posterior puede retirarla: solo una ficha del
    mismo color provocaria la fusion que la absorbe, y ya no queda ninguna.
    Por tanto:

        ocupadas_finales >= colores_distintos_pendientes

    Juntando los tres pasos:

        h(n) = R * (N^2 - 1) - (ocupadas + R - colores_distintos_pendientes)

    Los dos terminos se recortan a cero para que la estimacion nunca sea
    negativa. Recortar solo puede hacer la heuristica mas optimista, y una
    heuristica mas optimista sigue siendo admisible.

    La cota es exacta en los casos simples. En la instancia de ejemplo del
    enunciado (N=4, K=3, M=6, con los tres colores presentes en la secuencia)
    da ocupadas_finales >= 3, que es justo el optimo que alcanza el agente.

    Sobre la consistencia. La heuristica es admisible pero NO es consistente.
    Al colocar la ultima ficha de un color, el conjunto de colores pendientes
    se reduce y h cae mas de lo que cuesta esa accion, es decir

        h(n) - h(n') = costo(a) + (colores(n) - colores(n'))

    que excede costo(a) cuando un color desaparece de la secuencia pendiente.
    Por eso el agente reabre los nodos cerrados cuando descubre un camino mas
    barato hacia ellos; sin esa reapertura, A* con lista cerrada podria fijar
    un costo subotimo y no corregirlo.
    """

    @property
    def nombre(self) -> str:
        """Nombre corto de la heuristica."""
        return "colores_pendientes"

    @property
    def es_admisible(self) -> bool:
        """La cota sale de un invariante del juego, nunca sobreestima."""
        return True

    def estimar(self, estado: EstadoPartida) -> int:
        """Calcula la cota inferior del costo restante."""
        instancia = estado.instancia
        tablero = estado.tablero

        fichas_restantes = instancia.cantidad_fichas - estado.indice_ficha_actual

        if fichas_restantes <= 0:
            return 0

        costo_maximo_por_accion = tablero.cantidad_celdas - 1
        costo_bruto = fichas_restantes * costo_maximo_por_accion

        colores_pendientes = self._colores_pendientes(estado)
        cota_ocupadas_finales = len(colores_pendientes)

        liberaciones_maximas = (
            tablero.cantidad_ocupadas + fichas_restantes - cota_ocupadas_finales
        )

        if liberaciones_maximas < 0:
            liberaciones_maximas = 0

        costo_estimado = costo_bruto - liberaciones_maximas

        if costo_estimado < 0:
            return 0

        return costo_estimado

    def _colores_pendientes(self, estado: EstadoPartida) -> Set[int]:
        """Reune los colores distintos que aun quedan por colocar."""
        colores: Set[int] = set()
        instancia = estado.instancia

        for indice in range(estado.indice_ficha_actual, instancia.cantidad_fichas):
            colores.add(instancia.obtener_ficha(indice).color)

        return colores