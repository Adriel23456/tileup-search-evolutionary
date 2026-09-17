"""Metricas reportables de una partida terminada."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricasPartida:
    """
    Agrupa las metricas que el enunciado exige reportar por salida estandar.

    El campo esfuerzo_algoritmo es generico a proposito: el agente de busqueda
    reportara nodos expandidos y el evolutivo evaluaciones de aptitud, sin que
    esta clase tenga que cambiar.
    """

    nombre_agente: str
    nombre_instancia: str
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

    def como_diccionario(self) -> dict:
        """Devuelve las metricas como diccionario para escribirlas en CSV."""
        return {
            "agente": self.nombre_agente,
            "instancia": self.nombre_instancia,
            "semilla": self.semilla,
            "resultado": self.resultado,
            "colocadas": self.fichas_colocadas,
            "totales": self.fichas_totales,
            "ocupadas": self.celdas_ocupadas,
            "mayor": self.valor_ficha_mayor,
            "tiempo_s": format(self.tiempo_segundos, ".6f"),
            "esfuerzo": self.esfuerzo_algoritmo,
            "nombre_esfuerzo": self.nombre_esfuerzo,
        }