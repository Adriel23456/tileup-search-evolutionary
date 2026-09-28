"""
Punto de entrada unico del sistema TileUp.

El programa se organiza en subcomandos. Cada uno resuelve una tarea y declara
sus propios argumentos:

    resolver     Resuelve una instancia con uno o varios agentes.
    validar      Valida un archivo de solucion contra su instancia.
    jugar        Abre la ventana de juego para jugar una partida.
    instancia    Revisa el formato de un archivo de instancia.
    generar      Genera un archivo de instancia resoluble.
    agentes      Lista los agentes disponibles.
    backend      Muestra el backend de computo detectado.

Ejemplos:
    python main.py resolver --instancia datos\\instancias\\ejemplo_n4_k3_m6.txt ^
                            --agente busqueda --semilla 42 --limite-tiempo 5

    python main.py validar --instancia datos\\instancias\\ejemplo_n4_k3_m6.txt ^
                           --solucion datos\\soluciones\\busqueda\\ejemplo_n4_k3_m6__busqueda__s42.sol

    python main.py jugar --instancia datos\\instancias\\pequena_n5_k3_m12.txt
    python main.py generar --n 4 --k 3 --m 20 --semilla 1
    python main.py agentes
    python main.py --ayuda-completa

Este archivo no contiene logica del juego, de los algoritmos ni de la interfaz
grafica. Su unica responsabilidad es armar el analizador de argumentos a
partir del registro de subcomandos y despachar hacia el que corresponda.
"""

import argparse
import sys

from src.cli.codigos_salida import CODIGO_SALIDA_ERROR_ENTRADA
from src.cli.registro_comandos import RegistroComandos


# Nombre del programa, tal como aparece en los mensajes de ayuda.
NOMBRE_PROGRAMA = "tileup"

# Descripcion general que encabeza la ayuda.
DESCRIPCION_PROGRAMA = (
    "Sistema TileUp: motor del juego, agentes automaticos, validador de "
    "soluciones e interfaz de juego humano."
)


def construir_analizador_argumentos(registro: RegistroComandos) -> argparse.ArgumentParser:
    """
    Arma el analizador principal con un subanalizador por subcomando.

    Cada subcomando declara sus propios argumentos, de modo que esta funcion
    no conoce ninguno de ellos y no cambia cuando se agrega uno nuevo.
    """
    analizador = argparse.ArgumentParser(
        prog=NOMBRE_PROGRAMA,
        description=DESCRIPCION_PROGRAMA,
    )

    analizador.add_argument(
        "--ayuda-completa",
        action="store_true",
        dest="ayuda_completa",
        help="Muestra la ayuda de todos los subcomandos y termina.",
    )

    subanalizadores = analizador.add_subparsers(
        dest="comando",
        metavar="subcomando",
        help="Tarea que se desea ejecutar.",
    )

    for comando in registro.todos():
        subanalizador = subanalizadores.add_parser(
            comando.nombre,
            help=comando.ayuda,
            description=comando.ayuda,
        )
        comando.configurar_argumentos(subanalizador)

    return analizador


def mostrar_ayuda_completa(registro: RegistroComandos,
                           analizador: argparse.ArgumentParser) -> int:
    """Imprime la ayuda general seguida de la de cada subcomando."""
    analizador.print_help()

    for comando in registro.todos():
        print("")
        print("=" * 70)
        print("Subcomando: " + comando.nombre)
        print("=" * 70)

        subanalizador = argparse.ArgumentParser(
            prog=NOMBRE_PROGRAMA + " " + comando.nombre,
            description=comando.ayuda,
        )
        comando.configurar_argumentos(subanalizador)
        subanalizador.print_help()

    return CODIGO_SALIDA_ERROR_ENTRADA


def main() -> int:
    """Interpreta los argumentos y despacha hacia el subcomando indicado."""
    registro = RegistroComandos()
    analizador = construir_analizador_argumentos(registro)
    argumentos = analizador.parse_args()

    if argumentos.ayuda_completa is True:
        return mostrar_ayuda_completa(registro, analizador)

    if argumentos.comando is None:
        analizador.print_help()
        return CODIGO_SALIDA_ERROR_ENTRADA

    comando = registro.obtener(argumentos.comando)
    return comando.ejecutar(argumentos)


if __name__ == "__main__":
    sys.exit(main())