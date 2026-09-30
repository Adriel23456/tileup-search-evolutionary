"""
Resumen estadistico de una bateria a partir de su CSV crudo.

Lee exclusivamente resultados/experimentos/<experimento>/crudo.csv y escribe
resumen.csv en la misma carpeta: una fila por configuracion y agente, con la
dispersion entre semillas (media, desviacion estandar muestral, minimo y
maximo) de fichas colocadas, celdas ocupadas, tiempo y esfuerzo.

Reglas:
  - Las estadisticas se calculan solo sobre las corridas con status=ok. n_total
    y n_ok quedan siempre visibles, de modo que una corrida fallida nunca se
    promedia en silencio ni desaparece.
  - El esfuerzo de A* (nodos expandidos) y el del evolutivo (evaluaciones de
    aptitud) son unidades distintas. Cada fila corresponde a un solo agente y
    lleva su effort_type; nunca se agregan juntas.
  - prop_clock_safeguard es la proporcion de corridas en que el reloj de
    salvaguarda detuvo al agente antes de agotar su presupuesto determinista.
    Solo las corridas con clock_safeguard=False quedan determinadas por su
    entrada; en una bateria formal debe valer 0.

Uso, desde la raiz del repositorio:
    python -m experimentos.resumen comparacion
    python -m experimentos.resumen escalabilidad
"""

import argparse
import csv
import os
import statistics
import sys
from typing import Dict, List, Optional

from experimentos import corrida
from experimentos.registro import leer_crudo


DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos"
)

METRICAS = [
    ("tiles_placed", "tiles"),
    ("occupied_cells", "occupied"),
    ("elapsed_s", "elapsed_s"),
    ("effort", "effort"),
]

ESTADISTICOS = ["mean", "std", "min", "max"]

COLUMNAS_RESUMEN = (
    [
        "experiment", "config_id", "N", "K", "M", "rho", "agent", "effort_type",
        "n_total", "n_ok", "prop_validated", "prop_complete",
        "prop_search_cutoff", "prop_clock_safeguard",
    ]
    + [
        prefijo + "_" + estadistico
        for _, prefijo in METRICAS
        for estadistico in ESTADISTICOS
    ]
)


def resumir(filas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Agrupa por configuracion y agente, en el orden en que aparecen."""
    grupos: Dict[tuple, List[Dict[str, str]]] = {}

    for fila in filas:
        grupos.setdefault((fila["config_id"], fila["agent"]), []).append(fila)

    return [_resumir_grupo(grupo) for grupo in grupos.values()]


def _resumir_grupo(grupo: List[Dict[str, str]]) -> Dict[str, str]:
    """Una fila del resumen para una configuracion y un agente."""
    primera = grupo[0]
    ok = [fila for fila in grupo if fila["status"] == corrida.STATUS_OK]
    n_total = len(grupo)
    tipos = sorted({fila["effort_type"] for fila in ok if fila["effort_type"]})
    es_busqueda = tipos == [corrida.TIPO_ESFUERZO["nodos_expandidos"]]

    resultado = {
        "experiment": primera["experiment"],
        "config_id": primera["config_id"],
        "N": primera["N"],
        "K": primera["K"],
        "M": primera["M"],
        "rho": primera.get("rho", ""),
        "agent": primera["agent"],
        "effort_type": ";".join(tipos),
        "n_total": str(n_total),
        "n_ok": str(len(ok)),
        "prop_validated": _proporcion(grupo, "validated", n_total),
        "prop_complete": _proporcion(grupo, "complete", n_total),
        "prop_search_cutoff": "",
        "prop_clock_safeguard": _proporcion(grupo, "clock_safeguard", n_total),
    }

    if es_busqueda is True:
        resultado["prop_search_cutoff"] = _proporcion(grupo, "search_cutoff", n_total)

    for columna, prefijo in METRICAS:
        valores = [float(fila[columna]) for fila in ok if fila[columna] != ""]
        for estadistico, valor in _estadisticos(valores).items():
            resultado[prefijo + "_" + estadistico] = valor

    return resultado


def _estadisticos(valores: List[float]) -> Dict[str, str]:
    """Media, desviacion estandar muestral, minimo y maximo."""
    if len(valores) == 0:
        return {estadistico: "" for estadistico in ESTADISTICOS}

    desviacion = statistics.stdev(valores) if len(valores) >= 2 else None

    return {
        "mean": _numero(statistics.mean(valores)),
        "std": "" if desviacion is None else _numero(desviacion),
        "min": _numero(min(valores)),
        "max": _numero(max(valores)),
    }


def _proporcion(grupo: List[Dict[str, str]], columna: str, n_total: int) -> str:
    """Proporcion de corridas con la columna en True, sobre el total."""
    positivos = sum(1 for fila in grupo if fila[columna] == "True")
    return format(positivos / float(n_total), ".4f")


def _numero(valor: float) -> str:
    """Formato compacto: enteros sin decimales, reales con cuatro."""
    if float(valor).is_integer():
        return str(int(valor))

    return format(valor, ".4f")


def verificar_validacion(filas: List[Dict[str, str]]) -> Optional[str]:
    """
    Comprueba que todas las soluciones producidas fueron aceptadas.

    Devuelve None si todo esta en orden, o una descripcion del problema.
    """
    con_solucion = [fila for fila in filas if fila["solution_path"] != ""]
    aceptadas = [fila for fila in con_solucion if fila["validated"] == "True"]
    no_ok = [fila for fila in filas if fila["status"] != corrida.STATUS_OK]
    salvaguarda = [fila for fila in filas if fila["clock_safeguard"] == "True"]

    print(
        "soluciones aceptadas por el validador: "
        + str(len(aceptadas)) + "/" + str(len(con_solucion))
    )
    print("corridas ok: " + str(len(filas) - len(no_ok)) + "/" + str(len(filas)))
    print("corridas con clock_safeguard=True: " + str(len(salvaguarda)))

    problemas = [fila["run_id"] + "=" + fila["status"] for fila in no_ok]
    problemas += [fila["run_id"] + "=clock_safeguard" for fila in salvaguarda]

    if len(problemas) > 0:
        return ", ".join(problemas)

    return None


def main(argumentos: Optional[List[str]] = None) -> int:
    """Punto de entrada: resume la bateria indicada."""
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.resumen",
        description="Resume el CSV crudo de una bateria por configuracion y agente.",
    )
    analizador.add_argument("experimento", help="comparacion o escalabilidad")
    opciones = analizador.parse_args(argumentos)

    directorio = os.path.join(DIRECTORIO_RESULTADOS, opciones.experimento)
    filas = leer_crudo(os.path.join(directorio, "crudo.csv"))
    resumen = resumir(filas)

    ruta_resumen = os.path.join(directorio, "resumen.csv")
    with open(ruta_resumen, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_RESUMEN)
        escritor.writeheader()
        escritor.writerows(resumen)

    print("resumen=" + corrida.ruta_para_registro(ruta_resumen))
    problema = verificar_validacion(filas)

    if problema is not None:
        print("Corridas que no quedaron ok: " + problema, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
