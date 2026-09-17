"""
Coordinacion de las ejecuciones solicitadas desde la linea de comandos.

Este modulo no interpreta argumentos: eso corresponde a los subcomandos. Su
responsabilidad es cargar la instancia, construir el agente, correrlo y
reportar el resultado con un formato uniforme.

No importa Tkinter ni ningun componente grafico.
"""

import sys
from typing import List, Optional

from src.agentes.registro_agentes import (
    ErrorAgenteDesconocido,
    RegistroAgentes,
)
from src.cli.codigos_salida import (
    CODIGO_SALIDA_ERROR_AGENTE,
    CODIGO_SALIDA_ERROR_ENTRADA,
    CODIGO_SALIDA_EXITO,
)
from src.cli.observador_consola import ObservadorConsola
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.instancia import Instancia
from src.instancias.lector_instancia import LectorInstancia
from src.nombrado import nombres_archivos
from src.partidas.ejecutor_agente import EjecutorAgente


class EjecutorConsola:
    """Corre agentes y reporta sus resultados por salida estandar."""

    def __init__(self) -> None:
        """Construye la capa de consola con sus colaboradores."""
        self._lector_instancia = LectorInstancia()
        self._registro_agentes = RegistroAgentes()
        self._ejecutor_agente = EjecutorAgente()

    # ------------------------------------------------------------------
    # Ejecucion de un solo agente
    # ------------------------------------------------------------------

    def ejecutar_agente(self, ruta_instancia: str, nombre_agente: str,
                        semilla: int, limite_tiempo_segundos: float,
                        ruta_salida: Optional[str] = None,
                        silencioso: bool = False) -> int:
        """
        Corre un agente sobre una instancia y reporta el resultado.

        Devuelve el codigo de salida del proceso: cero si todo fue bien, un
        valor distinto de cero ante cualquier error controlado.
        """
        codigo_validacion = self._validar_limite_tiempo(limite_tiempo_segundos)

        if codigo_validacion != CODIGO_SALIDA_EXITO:
            return codigo_validacion

        instancia = self._cargar_instancia(ruta_instancia)

        if instancia is None:
            return CODIGO_SALIDA_ERROR_ENTRADA

        return self._correr_un_agente(
            instancia=instancia,
            nombre_agente=nombre_agente,
            semilla=semilla,
            limite_tiempo_segundos=limite_tiempo_segundos,
            ruta_salida=ruta_salida,
            silencioso=silencioso,
        )

    # ------------------------------------------------------------------
    # Ejecucion de varios agentes sobre la misma instancia
    # ------------------------------------------------------------------

    def ejecutar_comparacion(self, ruta_instancia: str,
                             nombres_agentes: List[str], semilla: int,
                             limite_tiempo_segundos: float,
                             silencioso: bool = False) -> int:
        """
        Corre varios agentes sobre la misma instancia y semilla.

        Sirve para la comparacion experimental del informe. Cada agente
        escribe su propia solucion en su propio directorio.
        """
        codigo_validacion = self._validar_limite_tiempo(limite_tiempo_segundos)

        if codigo_validacion != CODIGO_SALIDA_EXITO:
            return codigo_validacion

        instancia = self._cargar_instancia(ruta_instancia)

        if instancia is None:
            return CODIGO_SALIDA_ERROR_ENTRADA

        codigo_final = CODIGO_SALIDA_EXITO

        for nombre_agente in nombres_agentes:
            codigo_del_agente = self._correr_un_agente(
                instancia=instancia,
                nombre_agente=nombre_agente,
                semilla=semilla,
                limite_tiempo_segundos=limite_tiempo_segundos,
                ruta_salida=None,
                silencioso=silencioso,
            )

            if codigo_del_agente != CODIGO_SALIDA_EXITO:
                codigo_final = codigo_del_agente

        return codigo_final

    # ------------------------------------------------------------------
    # Utilidades de consulta
    # ------------------------------------------------------------------

    def listar_agentes(self) -> int:
        """Imprime los agentes disponibles para la linea de comandos."""
        for nombre in self._registro_agentes.nombres_disponibles():
            print(nombre)

        return CODIGO_SALIDA_EXITO

    def revisar_instancia(self, ruta_instancia: str) -> int:
        """Valida una instancia e informa el resultado por salida estandar."""
        instancia = self._cargar_instancia(ruta_instancia)

        if instancia is None:
            return CODIGO_SALIDA_ERROR_ENTRADA

        print("Instancia valida: " + instancia.resumen())
        return CODIGO_SALIDA_EXITO

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _correr_un_agente(self, instancia: Instancia, nombre_agente: str,
                          semilla: int, limite_tiempo_segundos: float,
                          ruta_salida: Optional[str], silencioso: bool) -> int:
        """Construye, ejecuta y reporta un agente sobre la instancia dada."""
        try:
            agente = self._registro_agentes.construir(nombre_agente, semilla)
        except ErrorAgenteDesconocido as error_de_agente:
            print(str(error_de_agente), file=sys.stderr)
            return CODIGO_SALIDA_ERROR_AGENTE

        ruta_final = self._resolver_ruta_salida(
            ruta_salida, instancia.nombre, agente.nombre, semilla
        )

        if silencioso is True:
            observador = None
        else:
            observador = ObservadorConsola(etiqueta=agente.nombre)
            self._anunciar_planificacion(
                nombre_agente, instancia, limite_tiempo_segundos
            )

        resultado = self._ejecutor_agente.ejecutar(
            agente=agente,
            instancia=instancia,
            semilla=semilla,
            limite_tiempo_segundos=limite_tiempo_segundos,
            ruta_solucion=ruta_final,
            observador=observador,
        )

        print(resultado.metricas.como_linea_estandar())
        print("solucion=" + resultado.ruta_solucion)

        if resultado.colocaciones_rechazadas > 0:
            print(
                "Advertencia: el agente propuso "
                + str(resultado.colocaciones_rechazadas)
                + " colocaciones ilegales que el motor rechazo",
                file=sys.stderr,
            )

        return CODIGO_SALIDA_EXITO

    def _anunciar_planificacion(self, nombre_agente: str,
                                instancia: Instancia,
                                limite_tiempo_segundos: float) -> None:
        """
        Avisa que la planificacion va a comenzar.

        La barra de progreso solo aparece durante la reproduccion, que ocurre
        despues de que el agente termino de decidir. Sin este aviso, la
        consola queda en blanco todo el tiempo de planificacion y da la
        impresion de que el programa se colgo.
        """
        print(
            "Planificando con '" + nombre_agente + "' sobre "
            + instancia.resumen() + ". Limite de tiempo: "
            + format(limite_tiempo_segundos, ".1f") + " s."
        )
        sys.stdout.flush()

    def _validar_limite_tiempo(self, limite_tiempo_segundos: float) -> int:
        """Verifica que el limite de tiempo sea utilizable."""
        if limite_tiempo_segundos <= 0:
            print(
                "El limite de tiempo debe ser mayor que cero",
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        return CODIGO_SALIDA_EXITO

    def _cargar_instancia(self, ruta_instancia: str) -> Optional[Instancia]:
        """Lee la instancia informando un error legible si el archivo falla."""
        try:
            return self._lector_instancia.leer_desde_archivo(ruta_instancia)
        except ErrorFormatoInstancia as error_de_formato:
            print(
                "Instancia invalida: " + str(error_de_formato),
                file=sys.stderr,
            )
            return None

    def _resolver_ruta_salida(self, ruta_salida: Optional[str],
                              nombre_instancia: str, nombre_agente: str,
                              semilla: int) -> str:
        """Determina donde escribir la solucion segun la convencion vigente."""
        if ruta_salida is not None:
            return ruta_salida

        return nombres_archivos.ruta_solucion(
            nombre_instancia=nombre_instancia,
            nombre_agente=nombre_agente,
            semilla=semilla,
        )