"""
Una corrida experimental: resolver, validar y clasificar.

Este es el unico modulo de experimentos/ que conoce los formatos que imprime la
linea de comandos. No reimplementa nada del juego ni de los agentes: invoca
main.py como lo haria una persona, lee lo que imprime y arma una fila del CSV
crudo con esa informacion y con el dictamen del validador independiente.

Una corrida solo cuenta como valida (status=ok) si el validador acepta la
solucion y, ademas, las metricas que informo el agente coinciden con las que el
validador reproduce por su cuenta. Que el programa termine no basta.
"""

import datetime
import hashlib
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


RAIZ_REPOSITORIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_MAIN = os.path.join(RAIZ_REPOSITORIO, "main.py")

# El agente se limita a si mismo con el limite de tiempo que recibe. El runner
# impone ademas un tope externo, holgado, solo para no quedar colgado si un
# proceso no termina: 1.5 veces el limite mas 30 s de arranque. Arrancar
# Python con NumPy toma del orden de 0.3 s, asi que el margen sobra.
FACTOR_TIMEOUT_EXTERNO = 1.5
MARGEN_TIMEOUT_EXTERNO_S = 30.0

# El validador no tiene limite propio; reproduce una partida, lo que es rapido.
TIMEOUT_VALIDADOR_S = 120.0

# Columnas del CSV crudo, una fila por corrida. Las primeras dieciocho son las
# obligatorias acordadas; el resto es evidencia para rastrear cada resultado.
COLUMNAS_CRUDO = [
    "experiment",
    "config_id",
    "instance",
    "N",
    "K",
    "M",
    "instance_seed",
    "agent",
    "agent_seed",
    "timeout_s",
    "status",
    "validated",
    "tiles_placed",
    "occupied_cells",
    "largest_tile",
    "elapsed_s",
    "effort",
    "effort_type",
    "result",
    "complete",
    "search_cutoff",
    "clock_safeguard",
    "time_fraction",
    "exceeded_limit",
    "wall_s",
    "return_code",
    "validator_return_code",
    "validator_verdict",
    "validator_tiles",
    "validator_occupied",
    "validator_largest",
    "solution_path",
    "solution_sha256",
    "run_id",
    "timestamp",
]

# Nombre con que el programa imprime cada medida de esfuerzo, y nombre con que
# se registra en el CSV. Son unidades distintas y nunca se suman ni se comparan
# como si fueran la misma magnitud.
TIPO_ESFUERZO = {
    "nodos_expandidos": "expanded_nodes",
    "evaluaciones_aptitud": "fitness_evaluations",
}

# Valores posibles de la columna status.
STATUS_OK = "ok"
STATUS_RECHAZADA = "rejected"
STATUS_DISCREPANCIA = "mismatch"
STATUS_ERROR_AGENTE = "agent_error"
STATUS_ABORTADA = "killed"
STATUS_ERROR_VALIDADOR = "validator_error"


# ----------------------------------------------------------------------
# Formatos de la linea de comandos
# ----------------------------------------------------------------------

PATRON_METRICAS = re.compile(
    r"^agente=(?P<agente>\S+) instancia=(?P<instancia>\S+)"
    r" semilla=(?P<semilla>-?\d+) resultado=(?P<resultado>\S+)"
    r" colocadas=(?P<colocadas>\d+)/(?P<total>\d+)"
    r" ocupadas=(?P<ocupadas>\d+) mayor=(?P<mayor>\d+)"
    r" tiempo_s=(?P<tiempo>[0-9.]+)"
    r" (?P<nombre_esfuerzo>[a-z_]+)=(?P<esfuerzo>\d+)$"
)

# Aviso que imprime el agente de busqueda cuando se detiene sin llegar a la
# meta y completa la partida de forma avida.
PREFIJO_NOTA_CORTE = "Nota: la busqueda se corto"

# Aviso que imprime cualquier agente cuando el reloj de salvaguarda lo detuvo
# antes de agotar su presupuesto determinista. Sin este aviso, la corrida quedo
# determinada por su entrada.
PREFIJO_SALVAGUARDA = "Advertencia: el reloj de salvaguarda"

PREFIJO_SOLUCION = "solucion="

PATRON_VEREDICTO = re.compile(r"^veredicto=(?P<veredicto>ACEPTADA|RECHAZADA)$")

PATRON_METRICAS_VALIDADOR = re.compile(
    r"^colocadas=(?P<colocadas>\d+)/(?P<total>\d+)"
    r" ocupadas=(?P<ocupadas>\d+) mayor=(?P<mayor>\d+) suma=(?P<suma>\d+)$"
)

PATRON_COMPLETITUD = re.compile(r"^completitud=(?P<completitud>\S+)$")

PATRON_DESCRIPCION_INSTANCIA = re.compile(
    r"^Instancia valida: (?P<nombre>\S+)\s+"
    r"\(N=(?P<n>\d+), K=(?P<k>\d+), M=(?P<m>\d+)\)$"
)


@dataclass(frozen=True)
class SalidaProceso:
    """Lo que dejo una invocacion de main.py."""

    argumentos: List[str]
    codigo: Optional[int]
    stdout: str
    stderr: str
    segundos_reloj: float
    abortado: bool


@dataclass(frozen=True)
class MetricasAgente:
    """Metricas que el agente informo por salida estandar."""

    resultado: str
    colocadas: int
    total: int
    ocupadas: int
    mayor: int
    tiempo_s: float
    esfuerzo: int
    nombre_esfuerzo: str
    corte_busqueda: bool
    corte_por_reloj: bool
    ruta_solucion: Optional[str]


@dataclass(frozen=True)
class DictamenValidador:
    """Lo que el validador independiente dictamino sobre una solucion."""

    veredicto: str
    colocadas: int
    total: int
    ocupadas: int
    mayor: int
    suma: int
    completa: bool


def ejecutar_main(argumentos: List[str], timeout_s: float) -> SalidaProceso:
    """
    Invoca main.py con los argumentos dados y captura todo lo que produce.

    Se ejecuta desde la raiz del repositorio y con la salida en UTF-8, para que
    el resultado no dependa de donde se lance el guion ni de la consola.
    """
    comando = [sys.executable, RUTA_MAIN] + list(argumentos)
    entorno = dict(os.environ)
    entorno["PYTHONIOENCODING"] = "utf-8"

    instante_inicio = time.perf_counter()

    try:
        proceso = subprocess.run(
            comando,
            cwd=RAIZ_REPOSITORIO,
            capture_output=True,
            timeout=timeout_s,
            env=entorno,
        )
    except subprocess.TimeoutExpired as agotado:
        return SalidaProceso(
            argumentos=list(argumentos),
            codigo=None,
            stdout=_como_texto(agotado.stdout),
            stderr=_como_texto(agotado.stderr),
            segundos_reloj=time.perf_counter() - instante_inicio,
            abortado=True,
        )

    return SalidaProceso(
        argumentos=list(argumentos),
        codigo=proceso.returncode,
        stdout=_como_texto(proceso.stdout),
        stderr=_como_texto(proceso.stderr),
        segundos_reloj=time.perf_counter() - instante_inicio,
        abortado=False,
    )


def interpretar_resolver(stdout: str) -> Optional[MetricasAgente]:
    """Extrae las metricas de la salida de resolver, o None si no aparecen."""
    coincidencia = None
    corte_busqueda = False
    corte_por_reloj = False
    ruta_solucion = None

    for linea in stdout.splitlines():
        linea = linea.strip()

        if linea.startswith(PREFIJO_NOTA_CORTE):
            corte_busqueda = True
        elif linea.startswith(PREFIJO_SALVAGUARDA):
            corte_por_reloj = True
        elif linea.startswith(PREFIJO_SOLUCION):
            ruta_solucion = linea[len(PREFIJO_SOLUCION):]
        elif PATRON_METRICAS.match(linea):
            coincidencia = PATRON_METRICAS.match(linea)

    if coincidencia is None:
        return None

    return MetricasAgente(
        resultado=coincidencia.group("resultado"),
        colocadas=int(coincidencia.group("colocadas")),
        total=int(coincidencia.group("total")),
        ocupadas=int(coincidencia.group("ocupadas")),
        mayor=int(coincidencia.group("mayor")),
        tiempo_s=float(coincidencia.group("tiempo")),
        esfuerzo=int(coincidencia.group("esfuerzo")),
        nombre_esfuerzo=coincidencia.group("nombre_esfuerzo"),
        corte_busqueda=corte_busqueda,
        corte_por_reloj=corte_por_reloj,
        ruta_solucion=ruta_solucion,
    )


def interpretar_validar(stdout: str) -> Optional[DictamenValidador]:
    """Extrae el dictamen de la salida de validar, o None si esta incompleto."""
    veredicto = None
    metricas = None
    completitud = None

    for linea in stdout.splitlines():
        linea = linea.strip()

        if PATRON_VEREDICTO.match(linea):
            veredicto = PATRON_VEREDICTO.match(linea).group("veredicto")
        elif PATRON_METRICAS_VALIDADOR.match(linea):
            metricas = PATRON_METRICAS_VALIDADOR.match(linea)
        elif PATRON_COMPLETITUD.match(linea):
            completitud = PATRON_COMPLETITUD.match(linea).group("completitud")

    if veredicto is None or metricas is None or completitud is None:
        return None

    return DictamenValidador(
        veredicto=veredicto,
        colocadas=int(metricas.group("colocadas")),
        total=int(metricas.group("total")),
        ocupadas=int(metricas.group("ocupadas")),
        mayor=int(metricas.group("mayor")),
        suma=int(metricas.group("suma")),
        completa=completitud == "secuencia_consumida",
    )


def describir_instancia(ruta_instancia: str) -> Tuple[str, int, int, int]:
    """
    Devuelve el nombre, N, K y M de una instancia, preguntandoselo a la CLI.

    Lanza ValueError si el programa no la acepta como instancia valida.
    """
    salida = ejecutar_main(["instancia", "--instancia", ruta_instancia], 60.0)

    for linea in salida.stdout.splitlines():
        coincidencia = PATRON_DESCRIPCION_INSTANCIA.match(linea.strip())

        if coincidencia is not None:
            return (
                coincidencia.group("nombre"),
                int(coincidencia.group("n")),
                int(coincidencia.group("k")),
                int(coincidencia.group("m")),
            )

    raise ValueError(
        "La CLI no acepto la instancia " + ruta_instancia + ": "
        + salida.stderr.strip()
    )


# ----------------------------------------------------------------------
# Clasificacion
# ----------------------------------------------------------------------

def metricas_coinciden(metricas: MetricasAgente,
                       dictamen: DictamenValidador) -> bool:
    """Indica si lo que informo el agente es lo que el validador reproduce."""
    return (
        metricas.colocadas == dictamen.colocadas
        and metricas.total == dictamen.total
        and metricas.ocupadas == dictamen.ocupadas
        and metricas.mayor == dictamen.mayor
    )


def clasificar(salida_resolver: SalidaProceso,
               metricas: Optional[MetricasAgente],
               salida_validar: Optional[SalidaProceso],
               dictamen: Optional[DictamenValidador]) -> str:
    """
    Asigna una unica etiqueta de estado a la corrida.

    Llegar al limite de tiempo no es un error: el agente debe entregar la mejor
    solucion encontrada, y eso se registra aparte como observacion.
    """
    if salida_resolver.abortado is True:
        return STATUS_ABORTADA

    if salida_resolver.codigo != 0 or metricas is None:
        return STATUS_ERROR_AGENTE

    if salida_validar is None or salida_validar.abortado is True:
        return STATUS_ERROR_VALIDADOR

    if dictamen is None:
        return STATUS_ERROR_VALIDADOR

    # El codigo de salida del validador y su veredicto deben contar la misma
    # historia: 0 con ACEPTADA, 1 con RECHAZADA. Cualquier otra combinacion es
    # un fallo del propio validador, no de la solucion.
    if dictamen.veredicto == "ACEPTADA" and salida_validar.codigo != 0:
        return STATUS_ERROR_VALIDADOR

    if dictamen.veredicto == "RECHAZADA" and salida_validar.codigo != 1:
        return STATUS_ERROR_VALIDADOR

    if dictamen.veredicto == "RECHAZADA":
        return STATUS_RECHAZADA

    if metricas_coinciden(metricas, dictamen) is False:
        return STATUS_DISCREPANCIA

    return STATUS_OK


# ----------------------------------------------------------------------
# Corrida completa
# ----------------------------------------------------------------------

def ejecutar_corrida(experimento: str, config_id: str, ruta_instancia: str,
                     nombre_instancia: str, n: int, k: int, m: int,
                     instance_seed: Optional[int], agente: str,
                     agent_seed: int, timeout_s: float, ruta_solucion: str,
                     run_id: str) -> Tuple[Dict[str, str], Dict]:
    """
    Resuelve, valida y clasifica una corrida.

    Devuelve la fila del CSV crudo y el detalle completo (comandos, stdout y
    stderr) para el registro de evidencia. Nunca lanza por un fallo de la
    corrida: el fallo queda registrado en la fila.
    """
    marca_de_tiempo = datetime.datetime.now().isoformat(timespec="seconds")

    # Una solucion que quedara de una corrida anterior en la misma ruta se
    # validaria como si fuera de esta. Se retira antes de empezar.
    directorio_solucion = os.path.dirname(os.path.abspath(ruta_solucion))
    os.makedirs(directorio_solucion, exist_ok=True)

    if os.path.isfile(ruta_solucion) is True:
        os.remove(ruta_solucion)

    salida_resolver = ejecutar_main(
        [
            "resolver",
            "--instancia", ruta_instancia,
            "--agente", agente,
            "--semilla", str(agent_seed),
            "--limite-tiempo", repr(float(timeout_s)),
            "--salida", ruta_solucion,
            "--silencioso",
        ],
        timeout_s * FACTOR_TIMEOUT_EXTERNO + MARGEN_TIMEOUT_EXTERNO_S,
    )
    metricas = interpretar_resolver(salida_resolver.stdout)

    salida_validar = None
    dictamen = None
    hay_solucion = os.path.isfile(ruta_solucion)

    if salida_resolver.abortado is False and hay_solucion is True:
        salida_validar = ejecutar_main(
            ["validar", "--instancia", ruta_instancia, "--solucion", ruta_solucion],
            TIMEOUT_VALIDADOR_S,
        )
        dictamen = interpretar_validar(salida_validar.stdout)

    status = clasificar(salida_resolver, metricas, salida_validar, dictamen)

    fila = {
        "experiment": experimento,
        "config_id": config_id,
        "instance": nombre_instancia,
        "N": str(n),
        "K": str(k),
        "M": str(m),
        "instance_seed": _texto_opcional(instance_seed),
        "agent": agente,
        "agent_seed": str(agent_seed),
        "timeout_s": _decimal(timeout_s),
        "status": status,
        "validated": "",
        "tiles_placed": "",
        "occupied_cells": "",
        "largest_tile": "",
        "elapsed_s": "",
        "effort": "",
        "effort_type": "",
        "result": "",
        "complete": "",
        "search_cutoff": "",
        "clock_safeguard": "",
        "time_fraction": "",
        "exceeded_limit": "",
        "wall_s": _decimal(salida_resolver.segundos_reloj),
        "return_code": _texto_opcional(salida_resolver.codigo),
        "validator_return_code": "",
        "validator_verdict": "",
        "validator_tiles": "",
        "validator_occupied": "",
        "validator_largest": "",
        "solution_path": "",
        "solution_sha256": "",
        "run_id": run_id,
        "timestamp": marca_de_tiempo,
    }

    if metricas is not None:
        tipo_esfuerzo = TIPO_ESFUERZO.get(
            metricas.nombre_esfuerzo, metricas.nombre_esfuerzo
        )

        fila["tiles_placed"] = str(metricas.colocadas)
        fila["occupied_cells"] = str(metricas.ocupadas)
        fila["largest_tile"] = str(metricas.mayor)
        fila["elapsed_s"] = _decimal(metricas.tiempo_s)
        fila["effort"] = str(metricas.esfuerzo)
        fila["effort_type"] = tipo_esfuerzo
        fila["result"] = metricas.resultado
        fila["complete"] = str(metricas.colocadas == m)
        fila["clock_safeguard"] = str(metricas.corte_por_reloj)
        fila["time_fraction"] = _decimal(metricas.tiempo_s / timeout_s)
        fila["exceeded_limit"] = str(metricas.tiempo_s > timeout_s)

        # Solo el agente de busqueda avisa cuando se detiene sin llegar a la
        # meta. Para otros agentes la ausencia del aviso no significa nada, asi
        # que la columna queda vacia en lugar de afirmar un False.
        if tipo_esfuerzo == TIPO_ESFUERZO["nodos_expandidos"]:
            fila["search_cutoff"] = str(metricas.corte_busqueda)

    if salida_validar is not None:
        fila["validator_return_code"] = _texto_opcional(salida_validar.codigo)

    if dictamen is not None:
        fila["validated"] = str(dictamen.veredicto == "ACEPTADA")
        fila["validator_verdict"] = dictamen.veredicto
        fila["validator_tiles"] = str(dictamen.colocadas)
        fila["validator_occupied"] = str(dictamen.ocupadas)
        fila["validator_largest"] = str(dictamen.mayor)

    if hay_solucion is True:
        fila["solution_path"] = ruta_para_registro(ruta_solucion)
        fila["solution_sha256"] = huella_archivo(ruta_solucion)

    detalle = {
        "run_id": run_id,
        "resolver": asdict(salida_resolver),
        "validar": None if salida_validar is None else asdict(salida_validar),
    }

    return (fila, detalle)


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def huella_archivo(ruta: str) -> str:
    """Devuelve el SHA-256 del contenido del archivo."""
    with open(ruta, "rb") as archivo:
        return hashlib.sha256(archivo.read()).hexdigest()


def ruta_para_registro(ruta: str) -> str:
    """
    Expresa una ruta de forma portable para el CSV.

    Dentro del repositorio se guarda relativa a la raiz y con '/', de modo que
    el CSV sirva igual en Windows, Linux o macOS.
    """
    absoluta = os.path.abspath(ruta)

    try:
        relativa = os.path.relpath(absoluta, RAIZ_REPOSITORIO)
    except ValueError:
        return absoluta.replace(os.sep, "/")

    if relativa.startswith(".."):
        return absoluta.replace(os.sep, "/")

    return relativa.replace(os.sep, "/")


def _como_texto(contenido) -> str:
    """Convierte la salida capturada de un proceso en texto."""
    if contenido is None:
        return ""

    if isinstance(contenido, str):
        return contenido

    return contenido.decode("utf-8", errors="replace")


def _texto_opcional(valor) -> str:
    """Convierte un valor en texto, o en vacio si no existe."""
    if valor is None:
        return ""

    return str(valor)


def _decimal(valor: float) -> str:
    """Formato fijo para los numeros reales del CSV."""
    return format(valor, ".6f")
