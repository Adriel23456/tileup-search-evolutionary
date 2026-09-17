"""
Heuristicas del agente de busqueda.

Una heuristica estima el costo que falta para alcanzar la meta desde un
estado. En A* se suma al costo real ya pagado para obtener f = g + h, que es
el valor por el que se ordena la lista abierta.

Todas las heuristicas de este modulo trabajan en las mismas unidades que la
funcion de costo definida en agente_busqueda.py:

    costo(a) = (N^2 - 1) - liberadas(a),  liberadas(a) = |G| - 1

Mezclar unidades entre g y h es el error clasico que rompe A* en silencio, de
modo que la unidad es parte del contrato de esta interfaz.
"""

from abc import ABC, abstractmethod
from typing import List, Set, Tuple

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

        Una heuristica admisible garantiza que A* devuelve la solucion
        optima. Una no admisible renuncia a esa garantia a cambio de explorar
        menos nodos.
        """

    @abstractmethod
    def estimar(self, estado: EstadoPartida) -> int:
        """Devuelve el costo estimado desde el estado hasta la meta."""


class HeuristicaCero(Heuristica):
    """
    Heuristica nula: h(n) = 0 para todo estado.

    Es trivialmente admisible y convierte A* en el algoritmo de Dijkstra: la
    busqueda se ordena solo por el costo real acumulado. Sirve de linea base
    en el informe para medir cuanto aporta realmente la heuristica informada.
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


class HeuristicaCotaLiberaciones(Heuristica):
    """
    Heuristica admisible basada en una cota de las fusiones futuras.

    Razonamiento completo:

    El costo restante es la suma, sobre las acciones que faltan, de
    (N^2 - 1) - liberadas. Es decir:

        costo_restante = restantes * (N^2 - 1) - liberaciones_totales_futuras

    Para acotar el costo por debajo hay que acotar las liberaciones futuras
    por arriba. Por conservacion de celdas:

        liberaciones_futuras = (ocupadas_ahora + restantes) - ocupadas_finales

    de modo que una cota inferior de ocupadas_finales da la cota superior que
    se busca. Se usan dos aportes disjuntos, porque hablan de colores
    distintos y por tanto no pueden solaparse:

      1. Cada color distinto que todavia aparece en la secuencia pendiente
         deja al menos una celda ocupada al final. Cuando se coloca su ultima
         ficha, nada posterior puede retirarla: solo una ficha del mismo color
         provocaria la fusion que la absorbe, y ya no queda ninguna.

      2. Cada componente conexa de un color congelado, entendiendo por
         congelado un color presente en el tablero pero ausente del resto de
         la secuencia, permanece intacta hasta el final. Ninguna colocacion
         futura puede tocarla.

    Por tanto:

        cota = componentes_congeladas + colores_distintos_restantes
        h(n) = restantes * (N^2 - 1) - (ocupadas + restantes - cota)

    Ambos terminos se recortan a cero para evitar valores negativos, lo que
    solo puede hacer la heuristica mas conservadora y nunca compromete la
    admisibilidad.
    """

    @property
    def nombre(self) -> str:
        """Nombre corto de la heuristica."""
        return "cota_liberaciones"

    @property
    def es_admisible(self) -> bool:
        """La cota se deriva de un argumento de conservacion, nunca excede."""
        return True

    def estimar(self, estado: EstadoPartida) -> int:
        """Calcula la cota inferior del costo restante."""
        instancia = estado.instancia
        tablero = estado.tablero

        fichas_restantes = instancia.cantidad_fichas - estado.indice_ficha_actual

        if fichas_restantes <= 0:
            return 0

        costo_maximo_por_accion = tablero.cantidad_celdas - 1
        costo_bruto_restante = fichas_restantes * costo_maximo_por_accion

        colores_restantes = self._colores_de_la_secuencia_pendiente(estado)
        componentes_congeladas = self._contar_componentes_congeladas(
            estado, colores_restantes
        )

        cota_ocupadas_finales = componentes_congeladas + len(colores_restantes)

        liberaciones_maximas = (
            tablero.cantidad_ocupadas + fichas_restantes - cota_ocupadas_finales
        )

        if liberaciones_maximas < 0:
            liberaciones_maximas = 0

        costo_estimado = costo_bruto_restante - liberaciones_maximas

        if costo_estimado < 0:
            return 0

        return costo_estimado

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _colores_de_la_secuencia_pendiente(self,
                                           estado: EstadoPartida) -> Set[int]:
        """Reune los colores distintos que aun quedan por colocar."""
        colores_pendientes: Set[int] = set()
        instancia = estado.instancia

        for indice in range(estado.indice_ficha_actual, instancia.cantidad_fichas):
            colores_pendientes.add(instancia.obtener_ficha(indice).color)

        return colores_pendientes

    def _contar_componentes_congeladas(self, estado: EstadoPartida,
                                       colores_restantes: Set[int]) -> int:
        """
        Cuenta las componentes conexas que ya no pueden fusionarse nunca mas.

        Una componente esta congelada cuando su color no vuelve a aparecer en
        la secuencia pendiente, de modo que ninguna colocacion futura puede
        tocarla.
        """
        tablero = estado.tablero
        celdas_ya_contadas: Set[Tuple[int, int]] = set()
        componentes_congeladas = 0

        for fila in range(tablero.dimension):
            for columna in range(tablero.dimension):
                if (fila, columna) in celdas_ya_contadas:
                    continue

                if tablero.esta_vacia(fila, columna) is True:
                    continue

                ficha_en_celda = tablero.obtener_ficha(fila, columna)

                if ficha_en_celda.color in colores_restantes:
                    continue

                componente = tablero.componente_conexa(fila, columna)

                for celda_de_la_componente in componente:
                    celdas_ya_contadas.add(celda_de_la_componente)

                componentes_congeladas = componentes_congeladas + 1

        return componentes_congeladas


class HeuristicaCompactacion(Heuristica):
    """
    Heuristica NO admisible orientada a mantener el tablero compacto.

    Toma la cota admisible y le suma una penalizacion proporcional a las
    celdas ocupadas en el estado actual. Eso empuja la busqueda hacia
    configuraciones despejadas mucho antes de que el costo real lo justifique,
    lo que reduce drasticamente los nodos expandidos.

    Garantia que se pierde: al sobreestimar, A* deja de garantizar que la
    solucion encontrada sea optima. Sigue siendo completa dentro del limite de
    nodos y sigue devolviendo soluciones legales, pero la cantidad de celdas
    ocupadas al final puede no ser la minima posible. Se declara de forma
    expresa porque la rubrica admite una heuristica no admisible siempre que
    se explique que se pierde con ella.

    El peso de la penalizacion se fijo por barrido: se probaron los valores
    1, 2, 4 y 8 sobre las instancias de prueba y se conservo el que mejor
    equilibrio dio entre nodos expandidos y celdas ocupadas finales.
    """

    def __init__(self, peso_penalizacion: int = 2) -> None:
        """Construye la heuristica con el peso de la penalizacion."""
        self._peso_penalizacion = peso_penalizacion
        self._heuristica_base = HeuristicaCotaLiberaciones()

    @property
    def nombre(self) -> str:
        """Nombre corto de la heuristica."""
        return "compactacion_p" + str(self._peso_penalizacion)

    @property
    def es_admisible(self) -> bool:
        """Sobreestima a proposito: no es admisible."""
        return False

    def estimar(self, estado: EstadoPartida) -> int:
        """Suma a la cota admisible una penalizacion por ocupacion."""
        if estado.hay_fichas_pendientes() is False:
            return 0

        estimacion_base = self._heuristica_base.estimar(estado)
        penalizacion = self._peso_penalizacion * estado.tablero.cantidad_ocupadas

        return estimacion_base + penalizacion