"""
Motor de reglas de TileUp.

Este modulo es la unica autoridad sobre las reglas del juego. Tanto el jugador
humano como los agentes automaticos pasan por aqui, y ninguno de ellos puede
alterar su comportamiento. Esto cumple el requisito del enunciado de que el
motor sea independiente de los agentes.
"""

from enum import Enum
from typing import List, Tuple

from src.dominio.estado_partida import EstadoPartida
from src.dominio.ficha import Ficha
from src.dominio.resultado_colocacion import ResultadoColocacion


class EstadoTerminacion(Enum):
    """Posibles condiciones de termino de una partida."""

    EN_CURSO = "en_curso"
    VICTORIA = "victoria"
    DERROTA = "derrota"


class ErrorColocacionIlegal(Exception):
    """Se lanza cuando se intenta una colocacion que las reglas no permiten."""


class MotorTileUp:
    """
    Aplica las reglas de TileUp sobre un estado de partida.

    El motor no guarda estado propio: recibe un EstadoPartida, lo modifica y
    devuelve el resultado. Asi la misma instancia del motor puede servir a
    muchas partidas en paralelo sin condiciones de carrera.
    """

    # ------------------------------------------------------------------
    # Consulta de acciones legales
    # ------------------------------------------------------------------

    def acciones_legales(self, estado: EstadoPartida) -> List[Tuple[int, int]]:
        """
        Devuelve todas las celdas donde la ficha pendiente puede colocarse.

        Como no hay gravedad ni restriccion de columna, cualquier celda vacia
        es una accion legal.
        """
        if estado.hay_fichas_pendientes() is False:
            return []

        return estado.tablero.celdas_vacias()

    def es_colocacion_legal(self, estado: EstadoPartida,
                            fila: int, columna: int) -> bool:
        """Indica si la colocacion propuesta respeta las reglas."""
        if estado.hay_fichas_pendientes() is False:
            return False

        if estado.tablero.coordenada_valida(fila, columna) is False:
            return False

        return estado.tablero.esta_vacia(fila, columna)

    # ------------------------------------------------------------------
    # Aplicacion de una colocacion
    # ------------------------------------------------------------------

    def colocar(self, estado: EstadoPartida,
                fila: int, columna: int) -> ResultadoColocacion:
        """
        Coloca la ficha pendiente en la celda indicada y aplica la fusion.

        Regla de fusion:
          1. Se escribe la ficha en la celda p.
          2. Se calcula G, la componente conexa maximal del mismo color que
             contiene a p, usando vecindad ortogonal.
          3. Si el tamano de G es mayor o igual a 2, se retiran todas las
             fichas de G y en p queda una unica ficha del mismo color cuyo
             valor es la suma de los valores de G.
          4. Si el tamano de G es 1, el tablero no cambia de otro modo.

        La fusion no encadena, porque G ya es la componente maximal: la ficha
        resultante no puede quedar adyacente a otra del mismo color.
        """
        if estado.hay_fichas_pendientes() is False:
            raise ErrorColocacionIlegal(
                "No quedan fichas pendientes por colocar"
            )

        if estado.tablero.coordenada_valida(fila, columna) is False:
            raise ErrorColocacionIlegal(
                "La coordenada (" + str(fila) + ", " + str(columna) + ") "
                "esta fuera del tablero"
            )

        if estado.tablero.esta_vacia(fila, columna) is False:
            raise ErrorColocacionIlegal(
                "La celda (" + str(fila) + ", " + str(columna) + ") "
                "ya esta ocupada"
            )

        indice_ficha = estado.indice_ficha_actual
        ficha_pendiente = estado.ficha_pendiente()

        # Paso 1: escribir la ficha en la celda elegida.
        estado.tablero.escribir_ficha(fila, columna, ficha_pendiente)

        # Paso 2: calcular la componente conexa maximal del mismo color.
        componente = estado.tablero.componente_conexa(fila, columna)
        tamano_componente = len(componente)

        # Paso 3: fusionar solo si la componente tiene dos o mas fichas.
        if tamano_componente >= 2:
            valor_acumulado = self._sumar_valores_de_la_componente(
                estado, componente
            )

            celdas_fusionadas = self._retirar_componente(estado, componente)

            ficha_resultante = Ficha(
                color=ficha_pendiente.color,
                valor=valor_acumulado,
            )
            estado.tablero.escribir_ficha(fila, columna, ficha_resultante)

            estado.avanzar_ficha()

            return ResultadoColocacion(
                indice_ficha=indice_ficha,
                fila=fila,
                columna=columna,
                color=ficha_pendiente.color,
                hubo_fusion=True,
                tamano_componente=tamano_componente,
                valor_resultante=valor_acumulado,
                celdas_fusionadas=tuple(celdas_fusionadas),
            )

        # Paso 4: componente de una sola ficha, no hay fusion.
        estado.avanzar_ficha()

        return ResultadoColocacion(
            indice_ficha=indice_ficha,
            fila=fila,
            columna=columna,
            color=ficha_pendiente.color,
            hubo_fusion=False,
            tamano_componente=1,
            valor_resultante=ficha_pendiente.valor,
            celdas_fusionadas=tuple(),
        )

    # ------------------------------------------------------------------
    # Condiciones de termino
    # ------------------------------------------------------------------

    def evaluar_terminacion(self, estado: EstadoPartida) -> EstadoTerminacion:
        """
        Determina si la partida termino y con que resultado.

        Victoria: se colocaron las M fichas de la secuencia.
        Derrota: queda al menos una ficha pendiente y el tablero esta lleno.
        """
        if estado.hay_fichas_pendientes() is False:
            return EstadoTerminacion.VICTORIA

        if estado.tablero.esta_lleno() is True:
            return EstadoTerminacion.DERROTA

        return EstadoTerminacion.EN_CURSO

    def es_meta(self, estado: EstadoPartida) -> bool:
        """
        Prueba de meta del problema de busqueda.

        Un estado es meta cuando toda la secuencia fue consumida.
        """
        return self.evaluar_terminacion(estado) == EstadoTerminacion.VICTORIA

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _sumar_valores_de_la_componente(self, estado: EstadoPartida,
                                        componente: List[Tuple[int, int]]) -> int:
        """Suma los valores de todas las fichas de la componente."""
        valor_acumulado = 0

        for fila_celda, columna_celda in componente:
            ficha_de_la_celda = estado.tablero.obtener_ficha(
                fila_celda, columna_celda
            )
            valor_acumulado = valor_acumulado + ficha_de_la_celda.valor

        return valor_acumulado

    def _retirar_componente(self, estado: EstadoPartida,
                            componente: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Vacia todas las celdas de la componente y devuelve sus coordenadas."""
        celdas_retiradas: List[Tuple[int, int]] = []

        for fila_celda, columna_celda in componente:
            estado.tablero.vaciar_celda(fila_celda, columna_celda)
            celdas_retiradas.append((fila_celda, columna_celda))

        return celdas_retiradas