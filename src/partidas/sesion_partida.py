"""
Orquestacion de una partida de TileUp.

La sesion conoce el motor, el estado, el registro de solucion y los
observadores, pero no conoce las reglas ni la interfaz grafica. Es el punto
unico por donde pasan todas las colocaciones, sin importar si vienen de una
persona o de un agente.
"""

import time
from typing import List, Optional

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion, MotorTileUp
from src.dominio.resultado_colocacion import ResultadoColocacion
from src.instancias.instancia import Instancia
from src.metricas.metricas_partida import MetricasPartida
from src.partidas.observador import ObservadorPartida
from src.soluciones.registro_solucion import RegistroSolucion


class SesionPartida:
    """Ciclo de vida completo de una partida."""

    def __init__(self, instancia: Instancia, motor: Optional[MotorTileUp] = None,
                 nombre_agente: str = "humano", semilla: int = 0) -> None:
        """Prepara una partida nueva sobre la instancia indicada."""
        self._instancia = instancia

        if motor is None:
            self._motor = MotorTileUp()
        else:
            self._motor = motor

        self._estado = EstadoPartida(instancia)
        self._registro = RegistroSolucion()
        self._observadores: List[ObservadorPartida] = []
        self._nombre_agente = nombre_agente
        self._semilla = semilla

        self._instante_inicio: Optional[float] = None
        self._instante_fin: Optional[float] = None
        self._esfuerzo_algoritmo = 0
        self._nombre_esfuerzo = "acciones"

        # Marcas de una sola ejecucion. Garantizan que los observadores reciban
        # exactamente una notificacion de inicio y una de fin, sin importar
        # cuantas veces se llame a iniciar o a finalizar desde afuera.
        self._inicio_notificado = False
        self._fin_notificado = False

    # ------------------------------------------------------------------
    # Accesores
    # ------------------------------------------------------------------

    @property
    def estado(self) -> EstadoPartida:
        """Devuelve el estado actual de la partida."""
        return self._estado

    @property
    def motor(self) -> MotorTileUp:
        """Devuelve el motor de reglas asociado a la sesion."""
        return self._motor

    @property
    def registro(self) -> RegistroSolucion:
        """Devuelve el registro de colocaciones acumuladas."""
        return self._registro

    # ------------------------------------------------------------------
    # Observadores
    # ------------------------------------------------------------------

    def agregar_observador(self, observador: ObservadorPartida) -> None:
        """Suscribe un observador a los eventos de la partida."""
        self._observadores.append(observador)

    def _notificar_inicio(self) -> None:
        """Avisa a todos los observadores que la partida comenzo."""
        for observador in self._observadores:
            observador.al_iniciar(self._estado)

    def _notificar_colocacion(self, resultado: ResultadoColocacion) -> None:
        """Avisa a todos los observadores de una colocacion aplicada."""
        for observador in self._observadores:
            observador.al_colocar(self._estado, resultado)

    def _notificar_fin(self, terminacion: EstadoTerminacion) -> None:
        """Avisa a todos los observadores que la partida termino."""
        for observador in self._observadores:
            observador.al_terminar(self._estado, terminacion)

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """
        Arranca el cronometro y notifica el inicio de la partida.

        Llamarla mas de una vez no tiene efecto: la notificacion de inicio se
        entrega una sola vez a cada observador.
        """
        if self._inicio_notificado is True:
            return

        self._instante_inicio = time.perf_counter()
        self._instante_fin = None
        self._inicio_notificado = True

        self._notificar_inicio()

    def aplicar_colocacion(self, fila: int, columna: int) -> ResultadoColocacion:
        """
        Aplica una colocacion decidida desde afuera.

        Este es el metodo que usa la ventana de juego cuando la persona hace
        clic en una celda, y tambien el que usa el ejecutor de agentes al
        reproducir la secuencia planificada.
        """
        if self._inicio_notificado is False:
            self.iniciar()

        resultado = self._motor.colocar(self._estado, fila, columna)

        self._registro.agregar(resultado)
        self._esfuerzo_algoritmo = self._esfuerzo_algoritmo + 1

        self._notificar_colocacion(resultado)

        terminacion = self._motor.evaluar_terminacion(self._estado)

        if terminacion != EstadoTerminacion.EN_CURSO:
            self.finalizar(terminacion)

        return resultado

    def finalizar(self, terminacion: Optional[EstadoTerminacion] = None) -> EstadoTerminacion:
        """
        Detiene el cronometro y notifica el fin de la partida.

        Es idempotente: si la partida ya habia terminado, devuelve la misma
        condicion de termino sin volver a notificar a los observadores. Esto
        permite que tanto la colocacion final como el ejecutor llamen a este
        metodo sin que la barra de progreso se dibuje dos veces.
        """
        if terminacion is None:
            terminacion_final = self._motor.evaluar_terminacion(self._estado)
        else:
            terminacion_final = terminacion

        if self._fin_notificado is True:
            return terminacion_final

        if self._instante_fin is None:
            self._instante_fin = time.perf_counter()

        self._fin_notificado = True
        self._notificar_fin(terminacion_final)

        return terminacion_final

    # ------------------------------------------------------------------
    # Metricas
    # ------------------------------------------------------------------

    def registrar_esfuerzo(self, cantidad: int, nombre: str) -> None:
        """
        Fija la medida de esfuerzo propia del algoritmo.

        El agente de busqueda llama a este metodo con nodos expandidos y el
        evolutivo lo hara con evaluaciones de aptitud.
        """
        self._esfuerzo_algoritmo = cantidad
        self._nombre_esfuerzo = nombre

    def tiempo_transcurrido(self) -> float:
        """Devuelve el tiempo de la partida en segundos."""
        if self._instante_inicio is None:
            return 0.0

        if self._instante_fin is None:
            return time.perf_counter() - self._instante_inicio

        return self._instante_fin - self._instante_inicio

    def construir_metricas(self) -> MetricasPartida:
        """Reune todas las metricas reportables de la partida."""
        terminacion = self._motor.evaluar_terminacion(self._estado)

        return MetricasPartida(
            nombre_agente=self._nombre_agente,
            nombre_instancia=self._instancia.nombre,
            dimension=self._instancia.dimension,
            cantidad_colores=self._instancia.cantidad_colores,
            semilla=self._semilla,
            fichas_colocadas=self._estado.cantidad_colocadas,
            fichas_totales=self._instancia.cantidad_fichas,
            celdas_ocupadas=self._estado.tablero.cantidad_ocupadas,
            valor_ficha_mayor=self._estado.tablero.valor_ficha_mayor(),
            tiempo_segundos=self.tiempo_transcurrido(),
            esfuerzo_algoritmo=self._esfuerzo_algoritmo,
            nombre_esfuerzo=self._nombre_esfuerzo,
            resultado=terminacion.value,
        )