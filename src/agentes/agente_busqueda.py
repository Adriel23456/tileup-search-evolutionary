"""
Agente de busqueda informada A* para TileUp.

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
    celdas vacias.

Costo de accion
    Sea liberadas(a) = |G| - 1, el numero de celdas que la fusion libero
    (cero cuando no hubo fusion). Se define:

        costo(a) = (N^2 - 1) - liberadas(a)

    Esta eleccion cumple dos condiciones necesarias a la vez:

      - Es no negativa, porque |G| <= N^2. La alternativa obvia, el cambio en
        celdas ocupadas, vale 2 - |G| y es negativa en cuanto hay fusion; A*
        pierde sus garantias con costos negativos.

      - Es exacta respecto al objetivo. Todo camino meta tiene exactamente M
        acciones y suma(liberadas) = M - ocupadas_finales, de modo que

            g_total = M * (N^2 - 2) + ocupadas_finales

        El termino constante es identico para todos los caminos meta, asi que
        minimizar g equivale exactamente a minimizar las celdas ocupadas al
        terminar, que es el segundo criterio de desempate del concurso.

Prueba de meta
    i == M, es decir, la secuencia completa fue consumida.

Heuristica
    Ver el modulo heuristicas.py. La opcion por defecto es admisible y se
    justifica alli con el argumento de conservacion completo.

Comportamiento anytime
----------------------

El espacio de estados es enorme: para N = 6 y M = 24 el arbol tiene del orden
de 36^24 nodos. A* exacto solo termina en instancias diminutas, de modo que el
agente incorpora tres mecanismos que el enunciado exige o permite:

  1. Limite de tiempo. Se comprueba en cada expansion.
  2. Limite de nodos expandidos, para acotar tambien la memoria.
  3. Completado avido. Si la busqueda se detiene sin alcanzar la meta, se toma
     el mejor nodo visto y se termina la partida con una politica avida
     determinista. Asi el agente siempre entrega una solucion, como pide el
     enunciado.

Ademas se puede limitar la cantidad de sucesores que se generan por nodo. Con
ese limite activo el algoritmo deja de ser A* puro y se convierte en una
busqueda en haz ordenada por f: gana tratabilidad y pierde completitud y
optimalidad. Se declara de forma expresa y se desactiva pasando cero.
"""

import heapq
import itertools
import time
from typing import List, Optional, Tuple

from src.agentes.agente import Agente
from src.agentes.heuristicas import Heuristica, HeuristicaCotaLiberaciones
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import MotorTileUp


# Cantidad de nodos expandidos por defecto antes de detener la busqueda.
LIMITE_NODOS_POR_DEFECTO = 200000

# Cantidad de sucesores conservados por nodo. Cero significa todos, es decir
# A* exacto sin poda.
MAXIMO_SUCESORES_POR_DEFECTO = 6


class NodoBusqueda:
    """
    Nodo del arbol de busqueda.

    Guarda el estado, el costo real acumulado, el valor heuristico y un
    puntero al padre. El puntero al padre es lo que permite reconstruir el
    camino cuando se alcanza la meta, igual que en el A* clasico sobre grafos.
    """

    __slots__ = (
        "estado",
        "costo_acumulado",
        "valor_heuristico",
        "padre",
        "accion",
        "profundidad",
    )

    def __init__(self, estado: EstadoPartida, costo_acumulado: int,
                 valor_heuristico: int, padre: Optional["NodoBusqueda"],
                 accion: Optional[Tuple[int, int]], profundidad: int) -> None:
        """Construye el nodo con todos sus campos."""
        self.estado = estado
        self.costo_acumulado = costo_acumulado
        self.valor_heuristico = valor_heuristico
        self.padre = padre
        self.accion = accion
        self.profundidad = profundidad

    @property
    def valor_f(self) -> int:
        """Devuelve f(n) = g(n) + h(n), el valor por el que se ordena."""
        return self.costo_acumulado + self.valor_heuristico


class AgenteBusquedaAEstrella(Agente):
    """Resuelve una instancia de TileUp con busqueda informada A*."""

    def __init__(self, semilla: int,
                 heuristica: Optional[Heuristica] = None,
                 limite_nodos: int = LIMITE_NODOS_POR_DEFECTO,
                 maximo_sucesores: int = MAXIMO_SUCESORES_POR_DEFECTO) -> None:
        """
        Construye el agente con su heuristica y sus limites de recursos.

        La semilla se conserva por contrato del enunciado, aunque este agente
        es determinista por construccion: todos los desempates se resuelven
        por reglas fijas y no por azar, de modo que dos ejecuciones con la
        misma instancia producen siempre la misma solucion.
        """
        self._semilla = semilla

        if heuristica is None:
            self._heuristica = HeuristicaCotaLiberaciones()
        else:
            self._heuristica = heuristica

        self._limite_nodos = limite_nodos
        self._maximo_sucesores = maximo_sucesores

        self._motor = MotorTileUp()
        self._nodos_expandidos = 0
        self._contador_de_insercion = itertools.count()

    # ------------------------------------------------------------------
    # Identificacion
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        """Nombre corto del agente."""
        return "busqueda"

    @property
    def nombre_medida_esfuerzo(self) -> str:
        """Medida de esfuerzo propia de un algoritmo de busqueda."""
        return "nodos_expandidos"

    @property
    def heuristica(self) -> Heuristica:
        """Devuelve la heuristica configurada, para informarla en el reporte."""
        return self._heuristica

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

        Si la busqueda alcanza la meta, devuelve el camino optimo respecto a
        la heuristica usada. Si se agota el tiempo o el limite de nodos,
        devuelve el mejor camino parcial encontrado, completado con la
        politica avida.
        """
        self._nodos_expandidos = 0
        self._contador_de_insercion = itertools.count()

        instante_limite = time.perf_counter() + limite_tiempo_segundos

        nodo_raiz = NodoBusqueda(
            estado=estado_inicial.copiar(),
            costo_acumulado=0,
            valor_heuristico=self._heuristica.estimar(estado_inicial),
            padre=None,
            accion=None,
            profundidad=0,
        )

        if self._motor.es_meta(nodo_raiz.estado) is True:
            return []

        lista_abierta: List[Tuple[int, int, int, NodoBusqueda]] = []
        self._insertar_en_abierta(lista_abierta, nodo_raiz)

        lista_cerrada = set()
        mejor_nodo = nodo_raiz

        while len(lista_abierta) > 0:
            if time.perf_counter() >= instante_limite:
                break

            if self._nodos_expandidos >= self._limite_nodos:
                break

            nodo_actual = heapq.heappop(lista_abierta)[3]
            clave_actual = self._construir_clave(nodo_actual)

            if clave_actual in lista_cerrada:
                continue

            lista_cerrada.add(clave_actual)
            self._nodos_expandidos = self._nodos_expandidos + 1

            if self._motor.es_meta(nodo_actual.estado) is True:
                return self._reconstruir_camino(nodo_actual)

            sucesores = self._generar_sucesores(nodo_actual)

            for nodo_sucesor in sucesores:
                clave_sucesor = self._construir_clave(nodo_sucesor)

                if clave_sucesor in lista_cerrada:
                    continue

                if self._es_mejor_que(nodo_sucesor, mejor_nodo) is True:
                    mejor_nodo = nodo_sucesor

                self._insertar_en_abierta(lista_abierta, nodo_sucesor)

        return self._completar_con_avidez(mejor_nodo)

    # ------------------------------------------------------------------
    # Lista abierta y cerrada
    # ------------------------------------------------------------------

    def _insertar_en_abierta(self, lista_abierta: list,
                             nodo: NodoBusqueda) -> None:
        """
        Inserta un nodo en la cola de prioridad ordenada por f.

        El desempate es de tres niveles y es lo que hace la busqueda
        deterministica:
          1. Menor f gana.
          2. A igual f, menor h gana, lo que prefiere los nodos mas cercanos
             a la meta y acelera el descenso.
          3. A igual f y h, gana el insertado primero, gracias a un contador
             monotono que ademas evita que la cola tenga que comparar nodos
             entre si.
        """
        orden_de_insercion = next(self._contador_de_insercion)

        entrada = (
            nodo.valor_f,
            nodo.valor_heuristico,
            orden_de_insercion,
            nodo,
        )

        heapq.heappush(lista_abierta, entrada)

    def _construir_clave(self, nodo: NodoBusqueda) -> tuple:
        """
        Construye la clave de la lista cerrada.

        Dos nodos representan el mismo estado cuando coinciden el contenido
        del tablero y el indice de la ficha pendiente. El indice es
        imprescindible: el mismo tablero con distinta ficha pendiente son
        situaciones completamente distintas.
        """
        return (
            nodo.estado.tablero.clave_hash(),
            nodo.estado.indice_ficha_actual,
        )

    # ------------------------------------------------------------------
    # Generacion de sucesores
    # ------------------------------------------------------------------

    def _generar_sucesores(self, nodo: NodoBusqueda) -> List[NodoBusqueda]:
        """
        Genera los nodos hijos del nodo indicado.

        La generacion ocurre en dos fases separadas a proposito:

          1. Se aplica cada colocacion legal y se calcula su costo, que es una
             operacion barata: una resta sobre el tamano de la componente que
             el motor ya devolvio.
          2. Solo sobre los sucesores que sobreviven a la poda se evalua la
             heuristica, que es la operacion cara porque recorre el tablero
             entero contando componentes congeladas.

        Evaluar la heuristica antes de podar significaba pagarla tambien por
        los sucesores descartados. Con N = 6 eso son 36 evaluaciones por nodo
        en lugar de 6, seis veces mas trabajo para el mismo resultado.

        Cuando maximo_sucesores es cero no hay poda y ambas fases recorren el
        mismo conjunto, de modo que A* exacto no cambia su comportamiento.
        """
        celdas_disponibles = self._motor.acciones_legales(nodo.estado)
        candidatos: List[tuple] = []
        tableros_ya_generados = set()

        for fila, columna in celdas_disponibles:
            estado_sucesor = nodo.estado.copiar()
            resultado = self._motor.colocar(estado_sucesor, fila, columna)

            clave_del_tablero = estado_sucesor.tablero.clave_hash()

            if clave_del_tablero in tableros_ya_generados:
                continue

            tableros_ya_generados.add(clave_del_tablero)

            costo_de_la_accion = self._calcular_costo(
                estado_sucesor, resultado.tamano_componente
            )

            clave_de_orden = (
                costo_de_la_accion,
                estado_sucesor.tablero.cantidad_ocupadas,
                fila,
                columna,
            )

            candidatos.append(
                (clave_de_orden, costo_de_la_accion, estado_sucesor, fila, columna)
            )

        candidatos_conservados = self._podar_candidatos(candidatos)

        return self._construir_nodos(nodo, candidatos_conservados)

    def _podar_candidatos(self, candidatos: List[tuple]) -> List[tuple]:
        """
        Conserva solo los mejores candidatos segun su costo inmediato.

        Con maximo_sucesores en cero se devuelven todos, lo que mantiene A*
        exacto. Con un valor positivo la busqueda se convierte en un haz
        ordenado por f, lo que se declara en la documentacion del agente.
        """
        if self._maximo_sucesores <= 0:
            return candidatos

        if len(candidatos) <= self._maximo_sucesores:
            return candidatos

        candidatos.sort(key=self._extraer_clave_de_orden)
        return candidatos[:self._maximo_sucesores]

    def _extraer_clave_de_orden(self, candidato: tuple) -> tuple:
        """Devuelve la clave de ordenamiento de un candidato."""
        return candidato[0]

    def _construir_nodos(self, nodo_padre: NodoBusqueda,
                         candidatos: List[tuple]) -> List[NodoBusqueda]:
        """Evalua la heuristica y arma el nodo definitivo de cada candidato."""
        sucesores: List[NodoBusqueda] = []

        for candidato in candidatos:
            clave_de_orden, costo_de_la_accion, estado_sucesor, fila, columna = candidato

            nodo_sucesor = NodoBusqueda(
                estado=estado_sucesor,
                costo_acumulado=nodo_padre.costo_acumulado + costo_de_la_accion,
                valor_heuristico=self._heuristica.estimar(estado_sucesor),
                padre=nodo_padre,
                accion=(fila, columna),
                profundidad=nodo_padre.profundidad + 1,
            )

            sucesores.append(nodo_sucesor)

        return sucesores

    def _calcular_costo(self, estado: EstadoPartida,
                        tamano_componente: int) -> int:
        """
        Calcula el costo de la accion que produjo este estado.

        costo = (N^2 - 1) - liberadas, con liberadas = |G| - 1.
        """
        celdas_liberadas = tamano_componente - 1
        costo_maximo_por_accion = estado.tablero.cantidad_celdas - 1

        return costo_maximo_por_accion - celdas_liberadas

    # ------------------------------------------------------------------
    # Comportamiento anytime
    # ------------------------------------------------------------------

    def _es_mejor_que(self, candidato: NodoBusqueda,
                      referencia: NodoBusqueda) -> bool:
        """
        Compara dos nodos con el mismo criterio que arbitra el concurso.

        Primero manda la profundidad, es decir la cantidad de fichas
        colocadas. Ante igualdad, manda dejar menos celdas ocupadas. Ante
        igualdad en ambas, manda el menor costo acumulado.
        """
        if candidato.profundidad != referencia.profundidad:
            return candidato.profundidad > referencia.profundidad

        ocupadas_candidato = candidato.estado.tablero.cantidad_ocupadas
        ocupadas_referencia = referencia.estado.tablero.cantidad_ocupadas

        if ocupadas_candidato != ocupadas_referencia:
            return ocupadas_candidato < ocupadas_referencia

        return candidato.costo_acumulado < referencia.costo_acumulado

    def _completar_con_avidez(self, nodo: NodoBusqueda) -> List[Tuple[int, int]]:
        """
        Termina la partida desde el nodo indicado con una politica avida.

        Se invoca cuando la busqueda se detuvo sin alcanzar la meta. En cada
        paso se elige la celda que minimiza el costo de la accion, con los
        mismos desempates que ordenan los sucesores, de modo que el resultado
        es reproducible.
        """
        colocaciones = self._reconstruir_camino(nodo)
        estado_simulado = nodo.estado.copiar()

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
        mejor_clave = None

        for fila, columna in celdas_disponibles:
            estado_tentativo = estado.copiar()
            resultado = self._motor.colocar(estado_tentativo, fila, columna)

            costo_de_la_accion = self._calcular_costo(
                estado_tentativo, resultado.tamano_componente
            )

            clave_tentativa = (
                costo_de_la_accion,
                estado_tentativo.tablero.cantidad_ocupadas,
                fila,
                columna,
            )

            if mejor_clave is None:
                mejor_clave = clave_tentativa
                mejor_celda = (fila, columna)
                continue

            if clave_tentativa < mejor_clave:
                mejor_clave = clave_tentativa
                mejor_celda = (fila, columna)

        return mejor_celda

    def _reconstruir_camino(self, nodo: NodoBusqueda) -> List[Tuple[int, int]]:
        """
        Recorre los punteros al padre para reconstruir la secuencia de acciones.

        Sin estos punteros la busqueda conoceria el costo del camino pero no el
        camino en si.
        """
        acciones_invertidas: List[Tuple[int, int]] = []
        nodo_actual = nodo

        while nodo_actual is not None:
            if nodo_actual.accion is not None:
                acciones_invertidas.append(nodo_actual.accion)

            nodo_actual = nodo_actual.padre

        acciones_invertidas.reverse()
        return acciones_invertidas