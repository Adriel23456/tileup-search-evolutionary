"""
Convenciones de nombrado de archivos generados por el sistema.

Centralizar el nombrado en un solo modulo evita que cada parte del sistema
invente su propio patron y permite que el validador y los guiones de la
bateria experimental encuentren los archivos sin ambiguedad.
"""

import os


# Extension de los archivos de solucion.
EXTENSION_SOLUCION = ".sol"

# Separador entre los campos del nombre de una solucion.
SEPARADOR_CAMPOS = "__"


def nombre_archivo_solucion(nombre_instancia: str, nombre_agente: str,
                            semilla: int) -> str:
    """
    Construye el nombre de un archivo de solucion.

    Patron: <instancia>__<agente>__s<semilla>.sol
    Ejemplo: ejemplo_n4_k3_m6__busqueda__s42.sol
    """
    return (
        nombre_instancia
        + SEPARADOR_CAMPOS + nombre_agente
        + SEPARADOR_CAMPOS + "s" + str(semilla)
        + EXTENSION_SOLUCION
    )


def directorio_soluciones_de(nombre_agente: str) -> str:
    """
    Devuelve el directorio de soluciones que corresponde a un agente.

    Patron: datos/soluciones/<agente>
    """
    return os.path.join("datos", "soluciones", nombre_agente)


def ruta_solucion(nombre_instancia: str, nombre_agente: str,
                  semilla: int) -> str:
    """Construye la ruta completa del archivo de solucion."""
    directorio = directorio_soluciones_de(nombre_agente)
    nombre = nombre_archivo_solucion(nombre_instancia, nombre_agente, semilla)
    return os.path.join(directorio, nombre)