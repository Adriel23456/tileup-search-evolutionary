"""
Convenciones de nombrado de los archivos generados por el sistema.

Este modulo no pertenece ni a la consola ni a la interfaz grafica: ambas lo
usan. Centralizar aqui los patrones evita que cada capa invente el suyo y
permite que el validador y la bateria experimental encuentren los archivos
sin ambiguedad.
"""

import os


# Extension de los archivos de solucion.
EXTENSION_SOLUCION = ".sol"

# Extension de los archivos de instancia.
EXTENSION_INSTANCIA = ".txt"

# Separador entre los campos del nombre de una solucion.
SEPARADOR_CAMPOS = "__"

# Raiz de los directorios de soluciones.
DIRECTORIO_RAIZ_SOLUCIONES = os.path.join("datos", "soluciones")

# Directorio donde viven los archivos de instancia.
DIRECTORIO_INSTANCIAS = os.path.join("datos", "instancias")

# Etiqueta con la que se nombran las instancias generadas si no se indica
# otra. La etiqueta distingue familias de instancias, como las de ejemplo
# ("ejemplo") o la no publicada ("ciega").
ETIQUETA_INSTANCIA_POR_DEFECTO = "gen"

# Nombre del agente que representa al jugador humano.
NOMBRE_AGENTE_HUMANO = "humano"


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
    return os.path.join(DIRECTORIO_RAIZ_SOLUCIONES, nombre_agente)


def ruta_solucion(nombre_instancia: str, nombre_agente: str,
                  semilla: int) -> str:
    """Construye la ruta completa del archivo de solucion."""
    directorio = directorio_soluciones_de(nombre_agente)
    nombre = nombre_archivo_solucion(nombre_instancia, nombre_agente, semilla)
    return os.path.join(directorio, nombre)


def ruta_solucion_humana(nombre_instancia: str, numero_partida: int) -> str:
    """
    Construye la ruta de la solucion de una partida humana.

    El numero de partida cumple el papel de la semilla, ya que una persona no
    juega a partir de un generador aleatorio.
    """
    return ruta_solucion(
        nombre_instancia=nombre_instancia,
        nombre_agente=NOMBRE_AGENTE_HUMANO,
        semilla=numero_partida,
    )


def nombre_archivo_instancia(etiqueta: str, semilla: int, dimension: int,
                             cantidad_colores: int,
                             cantidad_fichas: int) -> str:
    """
    Construye el nombre de un archivo de instancia generada.

    Patron: <etiqueta>_s<semilla>_n<N>_k<K>_m<M>.txt
    Ejemplo: gen_s1_n4_k3_m20.txt

    La semilla forma parte del nombre porque la bateria experimental corre
    varias semillas por configuracion: sin ella, la segunda semilla
    sobreescribiria el archivo de la primera.
    """
    return (
        etiqueta
        + "_s" + str(semilla)
        + "_n" + str(dimension)
        + "_k" + str(cantidad_colores)
        + "_m" + str(cantidad_fichas)
        + EXTENSION_INSTANCIA
    )


def ruta_instancia(etiqueta: str, semilla: int, dimension: int,
                   cantidad_colores: int, cantidad_fichas: int) -> str:
    """Construye la ruta completa del archivo de instancia generada."""
    nombre = nombre_archivo_instancia(
        etiqueta, semilla, dimension, cantidad_colores, cantidad_fichas
    )
    return os.path.join(DIRECTORIO_INSTANCIAS, nombre)


# Directorios donde se acumulan los resultados agregados.
DIRECTORIO_RESULTADOS = "resultados"


def ruta_bitacora_ejecuciones() -> str:
    """
    Devuelve la ruta del CSV que acumula las ejecuciones de agentes.

    Patron: resultados/experimentos/comparacion_agentes.csv
    """
    return os.path.join(
        DIRECTORIO_RESULTADOS, "experimentos", "comparacion_agentes.csv"
    )


def ruta_bitacora_humana() -> str:
    """
    Devuelve la ruta del CSV que acumula las partidas humanas.

    Patron: resultados/humano/partidas_humanas.csv
    """
    return os.path.join(DIRECTORIO_RESULTADOS, "humano", "partidas_humanas.csv")