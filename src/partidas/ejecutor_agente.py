"""
Ejecucion de un agente sobre una instancia.

El ejecutor separa dos fases de forma deliberada:

  1. Planificacion. El agente decide su secuencia completa de colocaciones,
     con un limite de tiempo. Aqui se mide el tiempo de computo.
  2. Reproduccion. La secuencia devuelta se aplica sobre una sesion limpia
     usando el motor. Si alguna colocacion resulta ilegal, se detiene ahi.

Esta separacion garantiza que el motor sea la unica autoridad sobre las
reglas: el agente propone, el motor dispone.
"""

import os
import time
from typing import List, Optional, Tuple

from src.agentes.agente import Agente
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import ErrorColocacionIlegal
from src.instancias.instancia import Instancia
from src.metricas.metricas_partida import MetricasPartida
from src.partidas.observador import ObservadorPartida
from src.partidas.sesion_partida import SesionPartida
from src.soluciones.escritor_solucion import EscritorSolucion


class ResultadoEjecucion:
    """Agrupa todo lo que produjo una ejecucion de un agente."""

    def __init__(self, metricas: MetricasPartida, ruta_solucion: str,
                 colocaciones_rechazadas: int) -> None:
        """Construye el resultado de la ejecucion."""
        self.metricas = metricas
        self.ruta_solucion = ruta_solucion
        self.colocaciones_rechazadas = colocaciones_rechazadas


class EjecutorAgente:
    """Corre un agente sobre una instancia y persiste su solucion."""

    def __init__(self, escritor: Optional[EscritorSolucion] = None) -> None:
        """Construye el ejecutor con su escritor de soluciones."""
        if escritor is None:
            self._escritor = EscritorSolucion()
        else:
            self._escritor = escritor

    def ejecutar(self, agente: Agente, instancia: Instancia, semilla: int,
                 limite_tiempo_segundos: float, ruta_solucion: str,
                 observador: Optional[ObservadorPartida] = None) -> ResultadoEjecucion:
        """Planifica, reproduce, escribe la solucion y devuelve las metricas."""
        colocaciones, tiempo_planificacion = self._planificar(
            agente, instancia, limite_tiempo_segundos
        )

        sesion = SesionPartida(
            instancia=instancia,
            nombre_agente=agente.nombre,
            semilla=semilla,
        )

        if observador is not None:
            sesion.agregar_observador(observador)

        colocaciones_rechazadas = self._reproducir(sesion, colocaciones)

        sesion.registrar_esfuerzo(
            cantidad=agente.esfuerzo_acumulado(),
            nombre=agente.nombre_medida_esfuerzo,
        )

        metricas_base = sesion.construir_metricas()
        metricas = self._reemplazar_tiempo(metricas_base, tiempo_planificacion)

        self._escritor.escribir(ruta_solucion, sesion.registro, metricas)

        return ResultadoEjecucion(
            metricas=metricas,
            ruta_solucion=os.path.abspath(ruta_solucion),
            colocaciones_rechazadas=colocaciones_rechazadas,
        )

    # ------------------------------------------------------------------
    # Fases
    # ------------------------------------------------------------------

    def _planificar(self, agente: Agente, instancia: Instancia,
                    limite_tiempo_segundos: float) -> Tuple[List[Tuple[int, int]], float]:
        """Ejecuta la planificacion del agente midiendo su tiempo real."""
        estado_inicial = EstadoPartida(instancia)

        instante_inicio = time.perf_counter()
        colocaciones = agente.planificar(estado_inicial, limite_tiempo_segundos)
        instante_fin = time.perf_counter()

        tiempo_planificacion = instante_fin - instante_inicio

        if colocaciones is None:
            return ([], tiempo_planificacion)

        return (colocaciones, tiempo_planificacion)

    def _reproducir(self, sesion: SesionPartida,
                    colocaciones: List[Tuple[int, int]]) -> int:
        """
        Aplica la secuencia propuesta sobre el motor.

        Devuelve cuantas colocaciones fueron rechazadas por ser ilegales. Un
        agente correcto nunca deberia producir ninguna.
        """
        sesion.iniciar()
        colocaciones_rechazadas = 0

        for fila, columna in colocaciones:
            if sesion.estado.hay_fichas_pendientes() is False:
                break

            try:
                sesion.aplicar_colocacion(fila, columna)
            except ErrorColocacionIlegal:
                colocaciones_rechazadas = colocaciones_rechazadas + 1
                break

        sesion.finalizar()
        return colocaciones_rechazadas


    def _reemplazar_tiempo(self, metricas: MetricasPartida,
                           tiempo_planificacion: float) -> MetricasPartida:
        """
        Sustituye el tiempo de la sesion por el tiempo real de planificacion.

        El tiempo que interesa reportar es el que el agente tardo en decidir,
        no el que tomo reproducir su secuencia sobre el motor.
        """
        return MetricasPartida(
            nombre_agente=metricas.nombre_agente,
            nombre_instancia=metricas.nombre_instancia,
            dimension=metricas.dimension,
            cantidad_colores=metricas.cantidad_colores,
            semilla=metricas.semilla,
            fichas_colocadas=metricas.fichas_colocadas,
            fichas_totales=metricas.fichas_totales,
            celdas_ocupadas=metricas.celdas_ocupadas,
            valor_ficha_mayor=metricas.valor_ficha_mayor,
            tiempo_segundos=tiempo_planificacion,
            esfuerzo_algoritmo=metricas.esfuerzo_algoritmo,
            nombre_esfuerzo=metricas.nombre_esfuerzo,
            resultado=metricas.resultado,
        )