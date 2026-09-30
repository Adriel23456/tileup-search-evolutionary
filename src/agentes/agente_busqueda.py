"""
Agente de busqueda informada A* para TileUp.

La implementacion sigue el pseudocodigo visto en clase: una lista abierta que
es una cola de prioridad ordenada por f = g + h, una lista cerrada que evita
reprocesar estados, un diccionario g con el costo real de llegar a cada
estado y un diccionario de punteros al padre que permite reconstruir el
camino cuando se alcanza la meta.

Formulacion del problema
------------------------

Estado
    Par <tablero, i>, donde el tablero es la configuracion de N x N celdas e i
    es el indice de la proxima ficha por colocar. Estado inicial: tablero
    vacio, i = 0. La secuencia de fichas no forma parte del estado porque es
    fija y comun a todos los nodos.

Operador de sucesion
    Colocar la ficha i en cualquier celda vacia, aplicando la fusion segun las
    reglas del motor. El factor de ramificacion es exactamente la cantidad de
    celdas vacias, tal como dice el enunciado.

Costo de accion
    Sea liberadas(a) = |G| - 1, las celdas que la fusion libero (cero cuando
    no hubo fusion). Se define:

        costo(a) = (N^2 - 1) - liberadas(a)

    Dos razones para esta forma:

      a) Es no negativa, porque |G| <= N^2. El costo "natural" seria el cambio
         en celdas ocupadas, que vale 1 - |G| y es negativo en cuanto hay
         fusion; con costos negativos A* pierde sus garantias.

      b) Minimiza exactamente lo que interesa. Todo camino meta tiene M
         acciones y suma(liberadas) = M - ocupadas_finales, de modo que

             g_total = M * (N^2 - 2) + ocupadas_finales

         El primer termino es identico para todos los caminos meta, asi que
         minimizar g equivale a minimizar las celdas ocupadas al terminar,
         que es el segundo criterio del concurso.

Prueba de meta
    i == M, es decir, la secuencia completa fue consumida.

Heuristica
    Ver heuristicas.py. La de por defecto es admisible y alli se justifica.

Limite de tiempo
----------------

El espacio de estados es enorme: para N = 6 y M = 24 el arbol tiene del orden
de 36^24 nodos, de modo que A* solo termina en instancias pequenas. El
enunciado exige que, alcanzado el limite, el agente entregue la mejor
solucion encontrada hasta ese momento. Por eso el agente recuerda el mejor
estado visto y, si la busqueda se corta, completa la partida colocando cada
ficha restante en la celda de menor costo inmediato.

La busqueda se corta por un presupuesto de nodos que depende solo del limite
de tiempo recibido, no por el reloj. Asi la misma entrada expande siempre los
mismos nodos y entrega la misma solucion, como exige el enunciado. El reloj se
conserva unicamente como salvaguarda del limite obligatorio: si llegara a
actuar antes que el presupuesto, el agente lo indica en corto_por_reloj.
"""

import heapq
import math
import time
from typing import Dict, List, Optional, Tuple

from src.agentes.agente import Agente
from src.agentes.heuristicas import Heuristica, HeuristicaColoresPendientes
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import MotorTileUp


# Tope de nodos expandidos. Existe solo para acotar la memoria: cada estado
# visitado se conserva para poder reconstruir el camino.
LIMITE_NODOS_POR_DEFECTO = 120000

# Fraccion del limite de tiempo que se reserva para completar la partida de
# forma avida cuando la busqueda no alcanzo la meta.
FRACCION_MARGEN_COMPLETADO = 0.15

# Nodos expandibles por cada segundo del limite de tiempo. Fija el presupuesto
# determinista de la busqueda. Se calibro con las corridas registradas: debe
# ser al menos 1991 para no cortar ninguna meta observada con T = 10 s (la mas
# costosa necesito 19912 nodos) y a lo sumo 2369 para agotarse antes que el
# reloj con margen 1.5 en el caso mas lento observado (4181 nodos/s durante el
# 85 % de T). Ver README, seccion del criterio de paro.
NODOS_POR_SEGUNDO_DE_LIMITE = 2200


def presupuesto_de_nodos(limite_tiempo_segundos: float,
                         limite_nodos: int = LIMITE_NODOS_POR_DEFECTO) -> int:
    """
    Presupuesto determinista de nodos para un limite de tiempo dado.

    min(limite_nodos, floor(NODOS_POR_SEGUNDO_DE_LIMITE * T)). Depende solo de
    las entradas, de modo que dos ejecuciones iguales expanden lo mismo.
    """
    return min(
        limite_nodos,
        int(math.floor(NODOS_POR_SEGUNDO_DE_LIMITE * limite_tiempo_segundos)),
    )


class AgenteBusquedaAEstrella(Agente):
    """Resuelve una instancia de TileUp con busqueda informada A*."""

    def __init__(self, semilla: int, nombre: str,
                 heuristica: Optional[Heuristica] = None,
                 limite_nodos: int = LIMITE_NODOS_POR_DEFECTO) -> None:
        """
        Construye el agente con su nombre, su heuristica y su tope de nodos.

        El nombre se recibe desde el registro porque identifica la variante:
        todas son A* y solo difieren en la heuristica, de modo que el nombre
        sigue el patron busqueda_<heuristica>. Ese nombre decide tambien el
        directorio donde se escribe la solucion.

        La semilla se recibe por contrato del enunciado, pero este agente es
        determinista por construccion: no usa ninguna fuente de azar y todos
        los desempates se resuelven por reglas fijas.
        """
        self._semilla = semilla
        self._nombre = nombre

        if heuristica is None:
            self._heuristica = HeuristicaColoresPendientes()
        else:
            self._heuristica = heuristica

        self._limite_nodos = limite_nodos
        self._motor = MotorTileUp()
        self._nodos_expandidos = 0

        # Indica si la ultima planificacion alcanzo la meta por busqueda o si
        # se corto antes de la meta y termino con la politica avida. Es
        # el dato que permite reportar en el informe en que punto A* deja de
        # resolver dentro del limite.
        self._alcanzo_la_meta = False

        # Indica si la ultima planificacion la detuvo el reloj de salvaguarda
        # antes de agotar el presupuesto. Solo mientras sea False la solucion
        # queda determinada por la entrada.
        self._corto_por_reloj = False

    # ------------------------------------------------------------------
    # Identificacion
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        """Nombre corto del agente."""
        return self._nombre

    @property
    def nombre_medida_esfuerzo(self) -> str:
        """Medida de esfuerzo propia de un algoritmo de busqueda."""
        return "nodos_expandidos"

    @property
    def heuristica(self) -> Heuristica:
        """Devuelve la heuristica configurada, para informarla en el reporte."""
        return self._heuristica


    @property
    def alcanzo_la_meta(self) -> bool:
        """Indica si la ultima planificacion termino por busqueda completa."""
        return self._alcanzo_la_meta

    @property
    def corto_por_reloj(self) -> bool:
        """Indica si el reloj de salvaguarda actuo antes que el presupuesto."""
        return self._corto_por_reloj

    def esfuerzo_acumulado(self) -> int:
        """Devuelve cuantos nodos se expandieron en la ultima planificacion."""
        return self._nodos_expandidos

    # ------------------------------------------------------------------
    # Planificacion
    # ------------------------------------------------------------------

    def planificar(self, estado_inicial: EstadoPartida,
                   limite_tiempo_segundos: float) -> List[Tuple[int, int]]:
        """
        Ejecuta A* y devuelve la secuencia de colocaciones decidida.

        Estructuras, con los nombres del pseudocodigo de clase:
          lista_abierta  cola de prioridad con (f, h, orden, clave)
          lista_cerrada  claves ya expandidas
          g              costo real de llegar a cada clave
          padre          clave del hijo -> (clave del padre, accion)
          estados        clave -> el EstadoPartida correspondiente
        """
        self._nodos_expandidos = 0
        self._alcanzo_la_meta = False
        self._corto_por_reloj = False

        presupuesto = presupuesto_de_nodos(limite_tiempo_segundos, self._limite_nodos)

        # El reloj ya no decide cuando parar: es solo la salvaguarda del limite
        # obligatorio. El completado avido ocurre despues de que la busqueda se
        # detiene y tambien consume tiempo, asi que la salvaguarda le reserva
        # una fraccion del limite para que el total nunca lo exceda: un agente
        # que se pasa del limite queda fuera del concurso.
        margen_para_completar = limite_tiempo_segundos * FRACCION_MARGEN_COMPLETADO
        instante_limite = (
            time.perf_counter() + limite_tiempo_segundos - margen_para_completar
        )

        estado_raiz = estado_inicial.copiar()
        clave_raiz = self._clave_del_estado(estado_raiz)

        lista_abierta: List[Tuple[int, int, int, bytes]] = []
        lista_cerrada = set()

        g: Dict[bytes, int] = {clave_raiz: 0}
        padre: Dict[bytes, Tuple[bytes, Tuple[int, int]]] = {}
        estados: Dict[bytes, EstadoPartida] = {clave_raiz: estado_raiz}

        orden_de_insercion = 0
        heuristica_raiz = self._heuristica.estimar(estado_raiz)
        heapq.heappush(
            lista_abierta,
            (heuristica_raiz, heuristica_raiz, orden_de_insercion, clave_raiz),
        )

        clave_mejor = clave_raiz

        while len(lista_abierta) > 0:
            if self._nodos_expandidos >= presupuesto:
                break

            if time.perf_counter() >= instante_limite:
                self._corto_por_reloj = True
                break

            valor_f, valor_h, orden, clave_actual = heapq.heappop(lista_abierta)

            if clave_actual in lista_cerrada:
                continue

            estado_actual = estados[clave_actual]

            if self._motor.es_meta(estado_actual) is True:
                self._alcanzo_la_meta = True
                return self._reconstruir_camino(padre, clave_actual)

            lista_cerrada.add(clave_actual)
            self._nodos_expandidos = self._nodos_expandidos + 1

            celdas_disponibles = self._motor.acciones_legales(estado_actual)

            for fila, columna in celdas_disponibles:
                estado_sucesor = estado_actual.copiar()
                resultado = self._motor.colocar(estado_sucesor, fila, columna)

                clave_sucesor = self._clave_del_estado(estado_sucesor)

                costo_de_la_accion = self._costo_de_la_accion(
                    estado_sucesor, resultado.tamano_componente
                )
                g_tentativo = g[clave_actual] + costo_de_la_accion

                if clave_sucesor in g and g_tentativo >= g[clave_sucesor]:
                    continue

                # La heuristica es admisible pero no consistente: al consumir
                # la ultima ficha de un color, h cae mas de lo que cuesta la
                # accion. Con una heuristica inconsistente, un nodo ya cerrado
                # puede alcanzarse despues por un camino mas barato, de modo
                # que hay que reabrirlo para no perder el optimo.
                if clave_sucesor in lista_cerrada:
                    lista_cerrada.remove(clave_sucesor)

                g[clave_sucesor] = g_tentativo
                padre[clave_sucesor] = (clave_actual, (fila, columna))
                estados[clave_sucesor] = estado_sucesor

                heuristica_sucesor = self._heuristica.estimar(estado_sucesor)
                orden_de_insercion = orden_de_insercion + 1

                heapq.heappush(
                    lista_abierta,
                    (
                        g_tentativo + heuristica_sucesor,
                        heuristica_sucesor,
                        orden_de_insercion,
                        clave_sucesor,
                    ),
                )

                if self._es_mejor(estado_sucesor, estados[clave_mejor]) is True:
                    clave_mejor = clave_sucesor

        return self._completar_desde_el_mejor(padre, estados, clave_mejor)

    # ------------------------------------------------------------------
    # Costo, clave y reconstruccion
    # ------------------------------------------------------------------

    def _clave_del_estado(self, estado: EstadoPartida) -> bytes:
        """
        Construye la clave con la que se identifica un estado.

        Dos estados son el mismo cuando coinciden el contenido del tablero y
        el indice de la ficha pendiente. El indice es imprescindible: el mismo
        tablero con distinta ficha pendiente son situaciones distintas.
        """
        return (
            estado.tablero.clave_hash()
            + estado.indice_ficha_actual.to_bytes(4, "big")
        )

    def _costo_de_la_accion(self, estado: EstadoPartida,
                            tamano_componente: int) -> int:
        """Calcula costo = (N^2 - 1) - liberadas, con liberadas = |G| - 1."""
        celdas_liberadas = tamano_componente - 1
        costo_maximo_por_accion = estado.tablero.cantidad_celdas - 1

        return costo_maximo_por_accion - celdas_liberadas

    def _reconstruir_camino(self, padre: dict,
                            clave: bytes) -> List[Tuple[int, int]]:
        """
        Recorre los punteros al padre hacia atras para rearmar el camino.

        Sin estos punteros la busqueda conoceria el costo del camino pero no
        el camino en si, tal como se advirtio en clase.
        """
        acciones: List[Tuple[int, int]] = []
        clave_actual = clave

        while clave_actual in padre:
            clave_padre, accion = padre[clave_actual]
            acciones.append(accion)
            clave_actual = clave_padre

        acciones.reverse()
        return acciones

    # ------------------------------------------------------------------
    # Entrega de la mejor solucion cuando se agota el tiempo
    # ------------------------------------------------------------------

    def _es_mejor(self, candidato: EstadoPartida,
                  referencia: EstadoPartida) -> bool:
        """
        Compara dos estados con el mismo orden que arbitra el concurso.

        Primero mandan las fichas colocadas. Ante igualdad, manda dejar menos
        celdas ocupadas.
        """
        if candidato.cantidad_colocadas != referencia.cantidad_colocadas:
            return candidato.cantidad_colocadas > referencia.cantidad_colocadas

        ocupadas_candidato = candidato.tablero.cantidad_ocupadas
        ocupadas_referencia = referencia.tablero.cantidad_ocupadas

        return ocupadas_candidato < ocupadas_referencia

    def _completar_desde_el_mejor(self, padre: dict, estados: dict,
                                  clave_mejor: bytes) -> List[Tuple[int, int]]:
        """
        Termina la partida desde el mejor estado visto, de forma avida.

        Se invoca cuando la busqueda se detuvo sin alcanzar la meta. En cada
        paso se elige la celda de menor costo inmediato, con el mismo criterio
        de desempate que usa el resto del agente, de modo que el resultado es
        reproducible.
        """
        colocaciones = self._reconstruir_camino(padre, clave_mejor)
        estado_simulado = estados[clave_mejor].copiar()

        while estado_simulado.hay_fichas_pendientes() is True:
            celdas_disponibles = self._motor.acciones_legales(estado_simulado)

            if len(celdas_disponibles) == 0:
                break

            mejor_celda = self._elegir_celda_avida(
                estado_simulado, celdas_disponibles
            )

            fila_elegida, columna_elegida = mejor_celda
            self._motor.colocar(estado_simulado, fila_elegida, columna_elegida)
            colocaciones.append(mejor_celda)

        return colocaciones

    def _elegir_celda_avida(self, estado: EstadoPartida,
                            celdas_disponibles: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Elige la celda que produce el menor costo inmediato."""
        mejor_celda = celdas_disponibles[0]
        mejor_clave_de_orden = None

        for fila, columna in celdas_disponibles:
            estado_tentativo = estado.copiar()
            resultado = self._motor.colocar(estado_tentativo, fila, columna)

            costo_de_la_accion = self._costo_de_la_accion(
                estado_tentativo, resultado.tamano_componente
            )

            clave_de_orden = (costo_de_la_accion, fila, columna)

            if mejor_clave_de_orden is None:
                mejor_clave_de_orden = clave_de_orden
                mejor_celda = (fila, columna)
                continue

            if clave_de_orden < mejor_clave_de_orden:
                mejor_clave_de_orden = clave_de_orden
                mejor_celda = (fila, columna)

        return mejor_celda