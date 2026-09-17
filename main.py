"""
Punto de entrada unico del sistema TileUp.

Modo consola (sin interfaz grafica, sin pasos interactivos):
    python main.py --instancia datos\\instancias\\ejemplo_n4_k3_m6.txt ^
                   --agente aleatorio --semilla 42 --limite-tiempo 5

Modo grafico:
    python main.py --gui

Utilidades:
    python main.py --listar-agentes
    python main.py --revisar-instancia datos\\instancias\\ejemplo_n4_k3_m6.txt
    python main.py --backend
"""

import argparse
import sys

from src.aceleracion.backend import DetectorBackend
from src.cli.ejecutor_consola import (
    CODIGO_SALIDA_ERROR_ENTRADA,
    CODIGO_SALIDA_EXITO,
    EjecutorConsola,
)
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.lector_instancia import LectorInstancia


# Limite de tiempo por defecto en segundos cuando no se indica otro.
LIMITE_TIEMPO_POR_DEFECTO = 10.0

# Semilla por defecto cuando no se indica otra.
SEMILLA_POR_DEFECTO = 0


def construir_analizador_argumentos() -> argparse.ArgumentParser:
    """Define los argumentos que acepta la linea de comandos."""
    analizador = argparse.ArgumentParser(
        prog="tileup",
        description=(
            "Sistema TileUp: motor del juego, ejecucion por linea de comandos "
            "e interfaz grafica opcional."
        ),
    )

    analizador.add_argument(
        "--instancia",
        type=str,
        default=None,
        help="Ruta del archivo de instancia.",
    )

    analizador.add_argument(
        "--agente",
        type=str,
        default=None,
        help="Nombre del agente que debe resolver la instancia.",
    )

    analizador.add_argument(
        "--semilla",
        type=int,
        default=SEMILLA_POR_DEFECTO,
        help="Semilla que fija toda fuente de azar del agente.",
    )

    analizador.add_argument(
        "--limite-tiempo",
        type=float,
        default=LIMITE_TIEMPO_POR_DEFECTO,
        dest="limite_tiempo",
        help="Limite de tiempo de planificacion, en segundos.",
    )

    analizador.add_argument(
        "--salida",
        type=str,
        default=None,
        help=(
            "Ruta del archivo de solucion. Si se omite, se usa la convencion "
            "datos/soluciones/<agente>/<instancia>__<agente>__s<semilla>.sol"
        ),
    )

    analizador.add_argument(
        "--silencioso",
        action="store_true",
        help="Omite la barra de progreso y deja solo la linea de metricas.",
    )

    analizador.add_argument(
        "--gui",
        action="store_true",
        help="Abre la interfaz grafica en lugar de ejecutar por consola.",
    )

    analizador.add_argument(
        "--listar-agentes",
        action="store_true",
        dest="listar_agentes",
        help="Imprime los agentes disponibles y termina.",
    )

    analizador.add_argument(
        "--revisar-instancia",
        type=str,
        default=None,
        dest="revisar_instancia",
        help="Valida el formato de una instancia y termina.",
    )

    analizador.add_argument(
        "--backend",
        action="store_true",
        help="Muestra el backend de computo detectado y termina.",
    )

    return analizador


def revisar_instancia(ruta_instancia: str) -> int:
    """Valida una instancia e informa el resultado por salida estandar."""
    lector = LectorInstancia()

    try:
        instancia = lector.leer_desde_archivo(ruta_instancia)
    except ErrorFormatoInstancia as error_de_formato:
        print("Instancia invalida: " + str(error_de_formato), file=sys.stderr)
        return CODIGO_SALIDA_ERROR_ENTRADA

    print("Instancia valida: " + instancia.resumen())
    return CODIGO_SALIDA_EXITO


def mostrar_backend() -> int:
    """Imprime el backend de computo disponible."""
    informacion = DetectorBackend().detectar()

    print("backend=" + informacion.nombre)
    print("soporta_gpu=" + str(informacion.soporta_gpu))
    print("detalle=" + informacion.detalle)

    return CODIGO_SALIDA_EXITO


def abrir_interfaz(ruta_instancia: str) -> int:
    """Abre la interfaz grafica del sistema."""
    from src.gui.aplicacion import AplicacionTileUp

    aplicacion = AplicacionTileUp(ruta_instancia_inicial=ruta_instancia)
    aplicacion.ejecutar()

    return CODIGO_SALIDA_EXITO


def main() -> int:
    """Interpreta los argumentos y ejecuta la accion correspondiente."""
    analizador = construir_analizador_argumentos()
    argumentos = analizador.parse_args()

    if argumentos.backend is True:
        return mostrar_backend()

    if argumentos.listar_agentes is True:
        return EjecutorConsola().listar_agentes()

    if argumentos.revisar_instancia is not None:
        return revisar_instancia(argumentos.revisar_instancia)

    if argumentos.gui is True:
        return abrir_interfaz(argumentos.instancia)

    if argumentos.agente is not None:
        if argumentos.instancia is None:
            print(
                "Se indico un agente pero falta --instancia",
                file=sys.stderr,
            )
            return CODIGO_SALIDA_ERROR_ENTRADA

        return EjecutorConsola().ejecutar(
            ruta_instancia=argumentos.instancia,
            nombre_agente=argumentos.agente,
            semilla=argumentos.semilla,
            limite_tiempo_segundos=argumentos.limite_tiempo,
            ruta_salida=argumentos.salida,
            silencioso=argumentos.silencioso,
        )

    return abrir_interfaz(argumentos.instancia)


if __name__ == "__main__":
    sys.exit(main())