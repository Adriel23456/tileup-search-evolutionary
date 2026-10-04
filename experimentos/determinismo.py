"""
Verificacion empirica del requisito de determinismo.

El enunciado exige: dos ejecuciones con la misma instancia, el mismo agente y
la misma semilla producen la misma solucion. Ambos agentes se detienen por
reloj (A* ademas por meta o por nodos), asi que conviene comprobarlo con datos
antes de construir la bateria.

Prueba oficial, la unica que decide: R repeticiones con entradas identicas,
es decir misma instancia, mismo agente, misma semilla y mismo limite de tiempo.
Las soluciones se comparan por su SHA-256.

Diagnostico opcional (--diagnostico): la misma instancia, agente y semilla con
varios limites de tiempo. Como el limite cambia, no son entradas identicas y el
resultado no prueba ni refuta el determinismo; solo muestra si la solucion
depende del computo disponible.

Uso, desde la raiz del repositorio:
    python -m experimentos.determinismo
    python -m experimentos.determinismo --diagnostico
"""

import argparse
import csv
import datetime
import json
import os
import sys
from typing import Dict, List, Optional

from experimentos import corrida
from experimentos.registro import (
    ErrorExperimentoExistente,
    RegistroExperimento,
    huella_de_configuracion,
    metadatos_del_entorno,
)


RUTA_CONFIGURACION = os.path.join(
    "experimentos", "configuracion", "determinismo.json"
)

DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos"
)

COLUMNAS = corrida.COLUMNAS_CRUDO + ["repeat"]

COLUMNAS_INFORME = [
    "instance",
    "agent",
    "agent_seed",
    "timeout_s",
    "runs",
    "n_ok",
    "distinct_solutions",
    "identical_solutions",
    "solution_sha256",
    "tiles_placed_values",
    "occupied_cells_values",
    "largest_tile_values",
    "search_cutoff_values",
    "clock_safeguard_values",
    "effort_type",
    "effort_min",
    "effort_max",
    "effort_range_pct",
    "elapsed_min_s",
    "elapsed_max_s",
    "statuses",
]


def main(argumentos: Optional[List[str]] = None) -> int:
    """Ejecuta la verificacion y devuelve el codigo de salida."""
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.determinismo",
        description=(
            "Repite corridas con entradas identicas y compara las soluciones."
        ),
    )
    analizador.add_argument("--config", default=RUTA_CONFIGURACION)
    analizador.add_argument(
        "--diagnostico",
        action="store_true",
        help=(
            "Corre el diagnostico de sensibilidad a distintos limites de "
            "tiempo en lugar de la prueba oficial."
        ),
    )
    analizador.add_argument("--sobrescribir", action="store_true")
    analizador.add_argument(
        "--experimento",
        default=None,
        help=(
            "Nombre de la carpeta de resultados, en lugar del de la "
            "configuracion. Permite repetir la prueba en otra sesion sin "
            "sobrescribir la anterior."
        ),
    )
    opciones = analizador.parse_args(argumentos)

    ruta_configuracion = os.path.join(corrida.RAIZ_REPOSITORIO, opciones.config)

    with open(ruta_configuracion, "r", encoding="utf-8") as archivo:
        configuracion = json.load(archivo)

    if opciones.diagnostico is True:
        experimento = configuracion["diagnostico"]["experiment"]
        limites = configuracion["diagnostico"]["timeouts_s"]
        repeticiones = 1
    else:
        experimento = configuracion["experiment"]
        limites = [configuracion["timeout_s"]]
        repeticiones = configuracion["repeticiones"]

    if opciones.experimento is not None:
        experimento = opciones.experimento

    semilla = configuracion["semilla_agente"]
    agentes = configuracion["agentes"]
    directorio = os.path.join(DIRECTORIO_RESULTADOS, experimento)

    # El entorno se captura antes de crear la carpeta de resultados: si no,
    # git veria los propios archivos de esta corrida como cambios sin confirmar.
    entorno = metadatos_del_entorno()

    try:
        registro = RegistroExperimento(directorio, COLUMNAS, opciones.sobrescribir)
    except ErrorExperimentoExistente as error:
        print(str(error), file=sys.stderr)
        return 2

    metadatos = {
        "experiment": experimento,
        "fase": "diagnostico" if opciones.diagnostico else "oficial",
        "configuracion": opciones.config.replace(os.sep, "/"),
        "sha256_configuracion": huella_de_configuracion(ruta_configuracion),
        "agentes": agentes,
        "semilla_agente": semilla,
        "timeouts_s": limites,
        "repeticiones": repeticiones,
        "entorno": entorno,
        "inicio": _ahora(),
    }

    instancias = []

    for ruta_relativa in configuracion["instancias"]:
        ruta = os.path.join(corrida.RAIZ_REPOSITORIO, ruta_relativa)
        nombre, n, k, m = corrida.describir_instancia(ruta)
        instancias.append((ruta, nombre, n, k, m))

    total = len(instancias) * len(agentes) * len(limites) * repeticiones
    indice = 0
    filas: List[Dict[str, str]] = []

    for ruta, nombre, n, k, m in instancias:
        for agente in agentes:
            for limite in limites:
                for repeticion in range(1, repeticiones + 1):
                    indice = indice + 1
                    run_id = experimento + "-" + format(indice, "04d")

                    ruta_solucion = os.path.join(
                        directorio,
                        "soluciones",
                        nombre + "__" + agente + "__s" + str(semilla)
                        + "__t" + format(limite, "g")
                        + "__r" + str(repeticion) + ".sol",
                    )

                    fila, detalle = corrida.ejecutar_corrida(
                        experimento=experimento,
                        config_id=nombre,
                        ruta_instancia=ruta,
                        nombre_instancia=nombre,
                        n=n,
                        k=k,
                        m=m,
                        instance_seed=None,
                        agente=agente,
                        agent_seed=semilla,
                        timeout_s=float(limite),
                        ruta_solucion=ruta_solucion,
                        run_id=run_id,
                    )
                    fila["repeat"] = str(repeticion)

                    registro.agregar(fila, detalle)
                    filas.append(fila)
                    _anunciar(indice, total, fila)

    metadatos["fin"] = _ahora()
    registro.escribir_metadatos(metadatos)

    informe = construir_informe(filas)
    ruta_informe = os.path.join(directorio, "informe.csv")
    _escribir_csv(ruta_informe, COLUMNAS_INFORME, informe)

    print("")
    print("crudo=" + corrida.ruta_para_registro(registro.ruta_crudo))
    print("informe=" + corrida.ruta_para_registro(ruta_informe))
    print("")

    if opciones.diagnostico is True:
        return _reportar_diagnostico(informe)

    return _reportar_puerta(informe)


def construir_informe(filas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Agrupa las corridas por entradas identicas y compara sus soluciones.

    Un grupo es la combinacion instancia, agente, semilla y limite de tiempo.
    Las corridas que no quedaron ok cuentan igual en runs y se ven en statuses:
    no se esconde ninguna.
    """
    grupos: Dict[tuple, List[Dict[str, str]]] = {}

    for fila in filas:
        clave = (fila["instance"], fila["agent"], fila["agent_seed"], fila["timeout_s"])
        grupos.setdefault(clave, []).append(fila)

    informe = []

    for (instancia, agente, semilla, limite), grupo in grupos.items():
        huellas = _distintos(fila["solution_sha256"] for fila in grupo)
        esfuerzos = [int(fila["effort"]) for fila in grupo if fila["effort"] != ""]
        tiempos = [float(fila["elapsed_s"]) for fila in grupo if fila["elapsed_s"] != ""]
        todas_con_solucion = all(fila["solution_sha256"] != "" for fila in grupo)

        rango = ""
        if len(esfuerzos) > 0 and min(esfuerzos) > 0:
            rango = format(
                100.0 * (max(esfuerzos) - min(esfuerzos)) / min(esfuerzos), ".2f"
            )

        informe.append({
            "instance": instancia,
            "agent": agente,
            "agent_seed": semilla,
            "timeout_s": limite,
            "runs": str(len(grupo)),
            "n_ok": str(sum(1 for fila in grupo if fila["status"] == "ok")),
            "distinct_solutions": str(len(huellas)),
            "identical_solutions": str(len(huellas) == 1 and todas_con_solucion),
            "solution_sha256": ";".join(huellas),
            "tiles_placed_values": ";".join(_distintos(f["tiles_placed"] for f in grupo)),
            "occupied_cells_values": ";".join(_distintos(f["occupied_cells"] for f in grupo)),
            "largest_tile_values": ";".join(_distintos(f["largest_tile"] for f in grupo)),
            "search_cutoff_values": ";".join(_distintos(f["search_cutoff"] for f in grupo)),
            "clock_safeguard_values": ";".join(_distintos(f.get("clock_safeguard", "") for f in grupo)),
            "effort_type": ";".join(_distintos(f["effort_type"] for f in grupo)),
            "effort_min": str(min(esfuerzos)) if esfuerzos else "",
            "effort_max": str(max(esfuerzos)) if esfuerzos else "",
            "effort_range_pct": rango,
            "elapsed_min_s": format(min(tiempos), ".4f") if tiempos else "",
            "elapsed_max_s": format(max(tiempos), ".4f") if tiempos else "",
            "statuses": ";".join(_distintos(f["status"] for f in grupo)),
        })

    return informe


# ----------------------------------------------------------------------
# Reportes
# ----------------------------------------------------------------------

def _reportar_puerta(informe: List[Dict[str, str]]) -> int:
    """Imprime el veredicto de la prueba oficial y devuelve 0 si se supera."""
    _imprimir_tabla(informe)

    distintas = [g for g in informe if g["identical_solutions"] != "True"]
    con_fallos = [g for g in informe if g["statuses"] != "ok"]
    esfuerzo_variable = [g for g in informe if g["effort_min"] != g["effort_max"]]
    con_salvaguarda = [g for g in informe if "True" in g["clock_safeguard_values"]]

    print("")
    print("Prueba oficial: entradas identicas (instancia, agente, semilla, limite).")

    if len(con_fallos) > 0:
        print("Corridas que no quedaron ok (rechazo, discrepancia o error):")
        for grupo in con_fallos:
            print("  - " + grupo["instance"] + " " + grupo["agent"]
                  + " statuses=" + grupo["statuses"])

    if len(con_salvaguarda) > 0:
        print("El reloj de salvaguarda actuo (clock_safeguard=True) en:")
        for grupo in con_salvaguarda:
            print("  - " + grupo["instance"] + " " + grupo["agent"])

    if len(esfuerzo_variable) > 0:
        print("Esfuerzo distinto entre repeticiones en:")
        for grupo in esfuerzo_variable:
            print("  - " + grupo["instance"] + " " + grupo["agent"] + " "
                  + grupo["effort_min"] + "-" + grupo["effort_max"])

    if (len(distintas) == 0 and len(con_fallos) == 0
            and len(esfuerzo_variable) == 0 and len(con_salvaguarda) == 0):
        print("PUERTA SUPERADA: en todos los grupos las soluciones y el esfuerzo "
              "son identicos, el reloj de salvaguarda no actuo y el validador "
              "acepto todo sin discrepancias.")
        return 0

    if len(distintas) > 0:
        print("PUERTA NO SUPERADA: soluciones distintas con entradas identicas en:")
        for grupo in distintas:
            print("  - " + grupo["instance"] + " " + grupo["agent"]
                  + " soluciones_distintas=" + grupo["distinct_solutions"]
                  + " ocupadas=" + grupo["occupied_cells_values"])

    return 1


def _reportar_diagnostico(informe: List[Dict[str, str]]) -> int:
    """Imprime el diagnostico de sensibilidad. No decide nada."""
    _imprimir_tabla(informe)

    por_par: Dict[tuple, List[Dict[str, str]]] = {}
    for grupo in informe:
        por_par.setdefault((grupo["instance"], grupo["agent"]), []).append(grupo)

    print("")
    print("Diagnostico (NO son entradas identicas: cambia el limite de tiempo).")

    for (instancia, agente), grupos in por_par.items():
        huellas = _distintos(g["solution_sha256"] for g in grupos)
        detalle = ", ".join(
            "T=" + g["timeout_s"].rstrip("0").rstrip(".")
            + ": ocupadas=" + g["occupied_cells_values"]
            + " sha=" + g["solution_sha256"][:10]
            for g in grupos
        )
        cambia = "cambia" if len(huellas) > 1 else "no cambia"
        print("  " + instancia + " " + agente + ": la solucion " + cambia
              + " con el limite (" + detalle + ")")

    return 0


def _imprimir_tabla(informe: List[Dict[str, str]]) -> None:
    """Tabla legible por consola, una linea por grupo."""
    encabezado = (
        format("instancia", "<20") + format("agente", "<16") + format("T", ">5")
        + format("corridas", ">10") + format("ok", ">4") + format("solucs", ">8")
        + format("ocupadas", ">10") + format("corte", ">7") + format("reloj", ">7")
        + format("esfuerzo min-max", ">20") + format("rango%", ">8")
        + format("tiempo min-max s", ">18")
    )
    print(encabezado)
    print("-" * len(encabezado))

    for grupo in informe:
        esfuerzo = grupo["effort_min"] + "-" + grupo["effort_max"]
        tiempo = grupo["elapsed_min_s"] + "-" + grupo["elapsed_max_s"]
        print(
            format(grupo["instance"], "<20") + format(grupo["agent"], "<16")
            + format(grupo["timeout_s"].rstrip("0").rstrip("."), ">5")
            + format(grupo["runs"], ">10") + format(grupo["n_ok"], ">4")
            + format(grupo["distinct_solutions"], ">8")
            + format(grupo["occupied_cells_values"], ">10")
            + format(grupo["search_cutoff_values"] or "-", ">7")
            + format(grupo["clock_safeguard_values"] or "-", ">7")
            + format(esfuerzo, ">20") + format(grupo["effort_range_pct"], ">8")
            + format(tiempo, ">18")
        )


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def _distintos(valores) -> List[str]:
    """Valores no vacios sin repetir, en el orden en que aparecen."""
    vistos: List[str] = []

    for valor in valores:
        if valor != "" and valor not in vistos:
            vistos.append(valor)

    return vistos


def _escribir_csv(ruta: str, columnas: List[str], filas: List[Dict[str, str]]) -> None:
    """Escribe una tabla completa en CSV."""
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=columnas, lineterminator="\n"
        )
        escritor.writeheader()
        escritor.writerows(filas)


def _anunciar(indice: int, total: int, fila: Dict[str, str]) -> None:
    """Una linea de progreso por corrida."""
    print(
        "[" + str(indice) + "/" + str(total) + "] " + fila["instance"]
        + " " + fila["agent"] + " T=" + fila["timeout_s"].rstrip("0").rstrip(".")
        + " r" + fila["repeat"] + " -> " + fila["status"]
        + " ocupadas=" + fila["occupied_cells"]
        + " esfuerzo=" + fila["effort"]
        + " tiempo_s=" + fila["elapsed_s"]
        + " sha=" + fila["solution_sha256"][:10]
    )
    sys.stdout.flush()


def _ahora() -> str:
    """Marca de tiempo ISO sin fracciones de segundo."""
    return datetime.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    sys.exit(main())
