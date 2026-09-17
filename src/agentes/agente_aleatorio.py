"""
Agente de linea base que coloca fichas al azar.

No es ninguno de los dos agentes exigidos por el enunciado. Existe para que la
ejecucion por linea de comandos sea verificable desde esta etapa y para servir
como punto de comparacion inferior en el informe final: todo agente informado
debe superarlo de forma consistente.

Es completamente determinista respecto a la semilla recibida, tal como exige
el requisito de determinismo del enunciado.
"""

import random
import time
from typing import List, Optional, Tuple

from src.agentes.agente import Agente
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion, MotorTileUp


class AgenteAleatorio(Agente):
    """Coloca cada ficha en una celda vacia elegida uniformemente al azar."""

    def __init__(self, semilla: int) -> None:
        """Construye el agente con su propio generador de numeros aleatorios."""
        self._semilla = semilla
        self._generador = random.Random(semilla)
        self._motor = MotorTileUp()
        self._esfuerzo = 0

    # ------------------------------------------------------------------
    # Identificacion
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        """Nombre corto del agente."""
        return "aleatorio"

    @property
    def nombre_medida_esfuerzo(self) -> str:
        """Medida de esfuerzo propia de este agente."""
        return "colocaciones_evaluadas"

    # ------------------------------------------------------------------
    # Planificacion
    # ------------------------------------------------------------------

    def planificar(self, estado_inicial: EstadoPartida,
                   limite_tiempo_segundos: float) -> List[Tuple[int, int]]:
        """
        Recorre la secuencia colocando cada ficha en una celda vacia al azar.

        Si el limite de tiempo se agota, devuelve la secuencia parcial que
        alcanzo a construir, como exige el enunciado.
        """
        self._esfuerzo = 0
        instante_inicio = time.perf_counter()

        estado_simulado = estado_inicial.copiar()
        colocaciones: List[Tuple[int, int]] = []

        while True:
            terminacion = self._motor.evaluar_terminacion(estado_simulado)

            if terminacion != EstadoTerminacion.EN_CURSO:
                break

            tiempo_transcurrido = time.perf_counter() - instante_inicio

            if tiempo_transcurrido >= limite_tiempo_segundos:
                break

            celda_elegida = self._elegir_celda(estado_simulado)

            if celda_elegida is None:
                break

            fila_elegida, columna_elegida = celda_elegida
            self._motor.colocar(estado_simulado, fila_elegida, columna_elegida)
            colocaciones.append((fila_elegida, columna_elegida))

        return colocaciones

    def esfuerzo_acumulado(self) -> int:
        """Devuelve cuantas celdas candidatas se evaluaron en total."""
        return self._esfuerzo

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _elegir_celda(self, estado: EstadoPartida) -> Optional[Tuple[int, int]]:
        """Elige al azar una de las celdas vacias disponibles."""
        celdas_disponibles = self._motor.acciones_legales(estado)

        if len(celdas_disponibles) == 0:
            return None

        self._esfuerzo = self._esfuerzo + len(celdas_disponibles)

        indice_elegido = self._generador.randrange(len(celdas_disponibles))
        return celdas_disponibles[indice_elegido]