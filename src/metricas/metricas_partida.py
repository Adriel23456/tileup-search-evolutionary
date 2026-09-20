"""Metricas reportables de una partida terminada."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricasPartida:
    """
    Agrupa las metricas que el enunciado exige reportar por salida estandar:
    fichas colocadas, celdas ocupadas, valor de la ficha mayor, tiempo
    transcurrido y la medida de esfuerzo del algoritmo.

    El campo esfuerzo_algoritmo es generico a proposito: el agente de busqueda
    reporta nodos expandidos y el evolutivo reportara evaluaciones de aptitud,
    sin que esta clase tenga que cambiar.
    """

    nombre_agente: str
    nombre_instancia: str
    dimension: int
    cantidad_colores: int
    semilla: int
    fichas_colocadas: int
    fichas_totales: int
    celdas_ocupadas: int
    valor_ficha_mayor: int
    tiempo_segundos: float
    esfuerzo_algoritmo: int
    nombre_esfuerzo: str
    resultado: str

    def como_linea_estandar(self) -> str:
        """Genera la linea de metricas para la salida estandar."""
        return (
            "agente=" + self.nombre_agente
            + " instancia=" + self.nombre_instancia
            + " semilla=" + str(self.semilla)
            + " resultado=" + self.resultado
            + " colocadas=" + str(self.fichas_colocadas)
            + "/" + str(self.fichas_totales)
            + " ocupadas=" + str(self.celdas_ocupadas)
            + " mayor=" + str(self.valor_ficha_mayor)
            + " tiempo_s=" + format(self.tiempo_segundos, ".4f")
            + " " + self.nombre_esfuerzo + "=" + str(self.esfuerzo_algoritmo)
        )

    def como_fila_csv(self) -> list:
        """
        Devuelve las metricas como una fila de CSV.

        El orden coincide con ENCABEZADO_COMPARACION de la bitacora de
        ejecuciones. Cambiar uno obliga a cambiar el otro.
        """
        return [
            self.nombre_agente,
            self.nombre_instancia,
            str(self.dimension),
            str(self.cantidad_colores),
            str(self.fichas_totales),
            str(self.semilla),
            self.resultado,
            str(self.fichas_colocadas),
            str(self.celdas_ocupadas),
            str(self.valor_ficha_mayor),
            format(self.tiempo_segundos, ".6f"),
            str(self.esfuerzo_algoritmo),
            self.nombre_esfuerzo,
        ]