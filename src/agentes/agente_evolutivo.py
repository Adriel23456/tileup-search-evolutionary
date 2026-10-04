"""Agente evolutivo de estado estacionario para TileUp.

Cada individuo es una secuencia de M coordenadas. Una reparación virtual
permite contar conflictos posteriores sin modificar el cromosoma; únicamente
los individuos con cero reparaciones pueden entregarse como solución.

La evolución se detiene al agotar un presupuesto de evaluaciones que depende
solo del límite de tiempo y de M, no del reloj: así la misma entrada y la misma
semilla recorren siempre la misma trayectoria y entregan la misma solución. El
reloj se conserva únicamente como salvaguarda del límite obligatorio; si llega
a actuar antes que el presupuesto, el agente lo indica en corto_por_reloj.
"""

from dataclasses import dataclass
import math
import random
import time
from typing import List, Optional, Sequence, Tuple

from src.agentes.agente import Agente
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion, MotorTileUp
from src.dominio.tablero import DESPLAZAMIENTOS_ORTOGONALES


Coordenada = Tuple[int, int]

# Parámetros fijos de diseño para las baterías incluidas en esta entrega.
TAMANO_POBLACION_POR_DEFECTO = 20
TAMANO_TORNEO_POR_DEFECTO = 3
PROBABILIDAD_CRUCE_POR_DEFECTO = 0.70
PESO_FICHAS_COLOCADAS = 100
PESO_CELDAS_OCUPADAS = 10
PESO_REPARACIONES = 25
FRACCION_MARGEN_TIEMPO = 0.02

# Colocaciones simuladas por cada segundo del límite de tiempo. Fija el
# presupuesto determinista de evaluaciones: cada evaluación simula M
# colocaciones, así que el presupuesto es floor(COLOCACIONES * T / M). Se
# se fijó a partir de las corridas registradas; el límite se redondeó a 20000
# colocaciones por segundo de T. Ver README, sección del criterio de paro.
COLOCACIONES_POR_SEGUNDO_DE_LIMITE = 20000


def presupuesto_de_evaluaciones(limite_tiempo_segundos: float,
                                cantidad_fichas: int) -> int:
    """
    Presupuesto determinista de evaluaciones de aptitud.

    floor(COLOCACIONES_POR_SEGUNDO_DE_LIMITE * T / M), y al menos 1 para que el
    plan inicial siempre pueda evaluarse. Depende solo de las entradas.
    """
    if cantidad_fichas <= 0:
        return 1

    return max(1, int(math.floor(
        COLOCACIONES_POR_SEGUNDO_DE_LIMITE * limite_tiempo_segundos / cantidad_fichas
    )))


@dataclass(frozen=True)
class IndividuoEvaluado:
    """Cromosoma junto con el resultado de su última evaluación."""

    genes: Tuple[Coordenada, ...]
    fitness: int
    reparaciones_necesarias: int
    indices_reparacion: Tuple[int, ...]
    fichas_colocadas: int
    celdas_ocupadas: int
    cantidad_fusiones: int
    colocaciones_simuladas: Tuple[Coordenada, ...]


class AgenteEvolutivo(Agente):
    """Algoritmo genético de estado estacionario para TileUp."""

    def __init__(self, semilla: int,
                 tamano_poblacion: int = TAMANO_POBLACION_POR_DEFECTO,
                 tamano_torneo: int = TAMANO_TORNEO_POR_DEFECTO,
                 probabilidad_cruce: float = PROBABILIDAD_CRUCE_POR_DEFECTO) -> None:
        """Configura el agente y su fuente privada de aleatoriedad."""
        if tamano_poblacion < 1:
            raise ValueError("El tamaño de población debe ser positivo")
        if tamano_torneo < 1:
            raise ValueError("El tamaño de torneo debe ser positivo")

        if probabilidad_cruce < 0.0 or probabilidad_cruce > 1.0:
            raise ValueError("La probabilidad de cruce debe estar entre 0 y 1")

        self._semilla = semilla
        self._generador = random.Random(semilla)
        self._tamano_poblacion = tamano_poblacion
        self._tamano_torneo = tamano_torneo
        self._probabilidad_cruce = probabilidad_cruce
        self._motor = MotorTileUp()
        self._evaluaciones_aptitud = 0
        self._corto_por_reloj = False

    @property
    def nombre(self) -> str:
        return "evolutivo"

    @property
    def corto_por_reloj(self) -> bool:
        """Indica si el reloj de salvaguarda actuó antes que el presupuesto."""
        return self._corto_por_reloj

    @property
    def nombre_medida_esfuerzo(self) -> str:
        return "evaluaciones_aptitud"

    def esfuerzo_acumulado(self) -> int:
        return self._evaluaciones_aptitud

    def planificar(self, estado_inicial: EstadoPartida,
                   limite_tiempo_segundos: float) -> List[Coordenada]:
        """Evoluciona planes hasta agotar el presupuesto y devuelve el mejor plan legal."""
        self._evaluaciones_aptitud = 0
        self._corto_por_reloj = False
        self._generador = random.Random(self._semilla)

        presupuesto = presupuesto_de_evaluaciones(
            limite_tiempo_segundos, estado_inicial.instancia.cantidad_fichas
        )

        # El reloj ya no decide cuándo parar: es solo la salvaguarda del
        # límite obligatorio.
        instante_inicio = time.perf_counter()
        margen = limite_tiempo_segundos * FRACCION_MARGEN_TIEMPO
        instante_limite = instante_inicio + limite_tiempo_segundos - margen

        # Se guarda una partida legal antes de evolucionar, por si el tiempo se agota durante la inicialización.
        genes_base, colocaciones_base, construccion_completa = (
            self._construir_genes_legales(
                estado_inicial, usar_heuristica=True,
                instante_limite=instante_limite,
            )
        )

        if construccion_completa is False:
            self._corto_por_reloj = True
            return colocaciones_base

        individuo_base = self._evaluar(estado_inicial, genes_base, ())
        poblacion: List[IndividuoEvaluado] = [individuo_base]
        mejor_valido = individuo_base

        while (len(poblacion) < self._tamano_poblacion
               and self._evaluaciones_aptitud < presupuesto):
            if time.perf_counter() >= instante_limite:
                self._corto_por_reloj = True
                return list(mejor_valido.colocaciones_simuladas)

            genes, _, terminada = self._construir_genes_legales(
                estado_inicial, usar_heuristica=False,
                instante_limite=instante_limite,
            )

            if terminada is False:
                self._corto_por_reloj = True
                break

            individuo = self._evaluar(estado_inicial, genes, ())
            poblacion.append(individuo)
            mejor_valido = self._mejor_valido(mejor_valido, individuo)

        while (self._corto_por_reloj is False
               and self._evaluaciones_aptitud < presupuesto):
            if time.perf_counter() >= instante_limite:
                self._corto_por_reloj = True
                break

            padre_a = self._seleccionar_por_torneo(poblacion)
            padre_b = self._seleccionar_por_torneo(poblacion)

            hubo_cruce = (
                len(padre_a.genes) >= 2
                and self._generador.random() < self._probabilidad_cruce
            )

            if hubo_cruce:
                genes_hijo = self._cruzar(padre_a.genes, padre_b.genes)
                fuente_reparaciones = None
            else:
                genes_hijo = padre_a.genes
                fuente_reparaciones = padre_a

            cantidad = self._cantidad_de_mutaciones(len(genes_hijo))

            if cantidad == 0 and hubo_cruce is False:
                hijo = padre_a
            else:
                indices = self._elegir_indices_de_mutacion(
                    cantidad, len(genes_hijo), fuente_reparaciones
                )
                hijo = self._evaluar(estado_inicial, genes_hijo, indices)

            mejor_valido = self._mejor_valido(mejor_valido, hijo)
            self._reemplazar_si_mejora(poblacion, hijo)

        return list(mejor_valido.colocaciones_simuladas)

    def _construir_genes_legales(
            self, estado_inicial: EstadoPartida, usar_heuristica: bool,
            instante_limite: float) -> Tuple[Tuple[Coordenada, ...],
                                              List[Coordenada], bool]:
        """Construye un cromosoma cuyo prefijo ejecutado es siempre legal."""
        estado = estado_inicial.copiar()
        genes: List[Coordenada] = []
        colocaciones: List[Coordenada] = []
        cantidad_fichas = estado.instancia.cantidad_fichas

        while self._motor.evaluar_terminacion(estado) == EstadoTerminacion.EN_CURSO:
            if time.perf_counter() >= instante_limite:
                return (tuple(genes), colocaciones, False)

            celdas = self._motor.acciones_legales(estado)

            if usar_heuristica:
                celda = self._elegir_celda_guiada(
                    estado, referencia=None, exigir_cambio=False
                )
            else:
                celda = celdas[self._generador.randrange(len(celdas))]

            self._motor.colocar(estado, celda[0], celda[1])
            genes.append(celda)
            colocaciones.append(celda)

        # Los genes tras una derrota quedan latentes para que cruces o mutaciones los vuelvan alcanzables.
        dimension = estado.instancia.dimension
        while len(genes) < cantidad_fichas:
            genes.append((
                self._generador.randrange(dimension),
                self._generador.randrange(dimension),
            ))

        return (tuple(genes), colocaciones, True)

    def _evaluar(self, estado_inicial: EstadoPartida,
                 genes: Sequence[Coordenada],
                 indices_a_mutar: Sequence[int]) -> IndividuoEvaluado:
        """Simula una vez el cromosoma y cuenta reparaciones virtuales."""
        estado = estado_inicial.copiar()
        genes_resultantes = list(genes)
        indices_mutacion = set(indices_a_mutar)
        reparaciones = 0
        indices_reparacion: List[int] = []
        fusiones = 0
        colocaciones: List[Coordenada] = []

        for indice, gen_original in enumerate(genes_resultantes):
            if self._motor.evaluar_terminacion(estado) != EstadoTerminacion.EN_CURSO:
                break

            if indice in indices_mutacion:
                gen = self._elegir_celda_guiada(
                    estado, referencia=gen_original, exigir_cambio=True
                )
                genes_resultantes[indice] = gen
            else:
                gen = gen_original

            if not self._motor.es_colocacion_legal(estado, gen[0], gen[1]):
                reparaciones += 1
                indices_reparacion.append(indice)
                # Esta jugada virtual solo permite medir conflictos posteriores; el gen original no cambia.
                celda_aplicada = self._elegir_celda_guiada(
                    estado, referencia=gen, exigir_cambio=False
                )
            else:
                celda_aplicada = gen

            resultado = self._motor.colocar(
                estado, celda_aplicada[0], celda_aplicada[1]
            )
            colocaciones.append(celda_aplicada)

            if resultado.hubo_fusion:
                fusiones += 1

        fichas_colocadas = estado.cantidad_colocadas
        celdas_ocupadas = estado.tablero.cantidad_ocupadas
        # La aptitud premia progreso, espacio libre y, después, menos coordenadas conflictivas.
        fitness = (
            PESO_FICHAS_COLOCADAS * fichas_colocadas
            - PESO_CELDAS_OCUPADAS * celdas_ocupadas
            - PESO_REPARACIONES * reparaciones
        )
        self._evaluaciones_aptitud += 1

        return IndividuoEvaluado(
            genes=tuple(genes_resultantes),
            fitness=fitness,
            reparaciones_necesarias=reparaciones,
            indices_reparacion=tuple(indices_reparacion),
            fichas_colocadas=fichas_colocadas,
            celdas_ocupadas=celdas_ocupadas,
            cantidad_fusiones=fusiones,
            colocaciones_simuladas=tuple(colocaciones),
        )

    def _elegir_celda_guiada(self, estado: EstadoPartida,
                             referencia: Optional[Coordenada],
                             exigir_cambio: bool) -> Coordenada:
        """Prefiere la mayor fusión y desempata sin utilizar azar."""
        celdas = self._motor.acciones_legales(estado)

        if len(celdas) == 0:
            raise RuntimeError("No hay una celda legal para continuar la simulación")

        candidatas = celdas
        if exigir_cambio and referencia in celdas and len(celdas) > 1:
            candidatas = [celda for celda in celdas if celda != referencia]

        mejor = candidatas[0]
        mejor_clave = self._clave_heuristica(estado, mejor, referencia)

        for celda in candidatas[1:]:
            clave = self._clave_heuristica(estado, celda, referencia)
            if clave < mejor_clave:
                mejor = celda
                mejor_clave = clave

        return mejor

    def _clave_heuristica(self, estado: EstadoPartida, celda: Coordenada,
                          referencia: Optional[Coordenada]) -> tuple:
        """Ordena por mayor componente, cercanía y coordenada lexicográfica."""
        tamano = self._tamano_componente_potencial(estado, celda)
        distancia = 0 if referencia is None else (
            abs(celda[0] - referencia[0])
            + abs(celda[1] - referencia[1])
        )
        # El orden fijo resuelve empates y hace determinista la heurística.
        return (-tamano, distancia, celda[0], celda[1])

    def _tamano_componente_potencial(self, estado: EstadoPartida,
                                     celda: Coordenada) -> int:
        """Calcula cuántas fichas uniría la pendiente en una celda vacía."""
        ficha = estado.ficha_pendiente()
        if ficha is None:
            return 0

        fila, columna = celda
        componente = {celda}

        for delta_fila, delta_columna in DESPLAZAMIENTOS_ORTOGONALES:
            fila_vecina = fila + delta_fila
            columna_vecina = columna + delta_columna

            if not estado.tablero.coordenada_valida(fila_vecina, columna_vecina):
                continue

            ficha_vecina = estado.tablero.obtener_ficha(
                fila_vecina, columna_vecina
            )
            if ficha_vecina is None or ficha_vecina.color != ficha.color:
                continue

            componente.update(
                estado.tablero.componente_conexa(fila_vecina, columna_vecina)
            )

        return len(componente)

    def _seleccionar_por_torneo(
            self, poblacion: Sequence[IndividuoEvaluado]) -> IndividuoEvaluado:
        """Selecciona el mejor de varios aspirantes tomados con reemplazo."""
        aspirantes = [
            poblacion[self._generador.randrange(len(poblacion))]
            for _ in range(self._tamano_torneo)
        ]
        return max(aspirantes, key=self._clave_seleccion)

    def _cruzar(self, genes_a: Sequence[Coordenada],
                genes_b: Sequence[Coordenada]) -> Tuple[Coordenada, ...]:
        """Realiza un cruce de un punto conservando la longitud M."""
        punto = self._generador.randrange(1, len(genes_a))
        return tuple(genes_a[:punto]) + tuple(genes_b[punto:])

    def _cantidad_de_mutaciones(self, longitud: int) -> int:
        """Elige 0, 1, 2 o 3 con probabilidad uniforme y respeta M."""
        # Cero mutaciones deja actuar solo al cruce; se limita la cantidad si M es menor que tres.
        return min(self._generador.randrange(4), longitud)

    def _elegir_indices_de_mutacion(
            self, cantidad: int, longitud: int,
            fuente_reparaciones: Optional[IndividuoEvaluado]) -> Tuple[int, ...]:
        """Elige posiciones distintas, priorizando el primer conflicto."""
        if cantidad == 0:
            return ()

        elegidos: List[int] = []
        if fuente_reparaciones is not None:
            if len(fuente_reparaciones.indices_reparacion) > 0:
                # Mutar primero el conflicto más temprano conserva útiles las decisiones previas del plan.
                elegidos.append(fuente_reparaciones.indices_reparacion[0])

        disponibles = [i for i in range(longitud) if i not in elegidos]
        faltantes = cantidad - len(elegidos)
        if faltantes > 0:
            elegidos.extend(self._generador.sample(disponibles, faltantes))

        elegidos.sort()
        return tuple(elegidos)

    def _reemplazar_si_mejora(self, poblacion: List[IndividuoEvaluado],
                              hijo: IndividuoEvaluado) -> None:
        """Reemplaza al peor cuando el hijo tiene un mejor orden."""
        indice_peor = min(
            range(len(poblacion)),
            key=lambda indice: self._clave_seleccion(poblacion[indice]),
        )

        if self._clave_seleccion(hijo) > self._clave_seleccion(poblacion[indice_peor]):
            poblacion[indice_peor] = hijo

    def _clave_seleccion(self, individuo: IndividuoEvaluado) -> tuple:
        """Desempata de forma reproducible después del fitness ponderado."""
        return (
            individuo.fitness,
            -individuo.reparaciones_necesarias,
            individuo.fichas_colocadas,
            -individuo.celdas_ocupadas,
            individuo.genes,
        )

    def _mejor_valido(self, actual: IndividuoEvaluado,
                      candidato: IndividuoEvaluado) -> IndividuoEvaluado:
        """Conserva la mejor solución sin reparaciones según el concurso."""
        if candidato.reparaciones_necesarias != 0:
            return actual

        clave_actual = (actual.fichas_colocadas, -actual.celdas_ocupadas)
        clave_candidato = (
            candidato.fichas_colocadas,
            -candidato.celdas_ocupadas,
        )
        return candidato if clave_candidato > clave_actual else actual
