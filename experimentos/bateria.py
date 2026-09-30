"""
Bateria experimental: generar instancias y correr los agentes sobre ellas.

Lee una configuracion JSON versionada y, para cada configuracion (N, K, M) y
cada semilla s:

  1. genera UNA instancia con el generador real (main.py generar --semilla s);
  2. corre cada agente sobre ese mismo archivo con --semilla s;
  3. valida cada solucion con el validador independiente.

Semillas pareadas: la semilla s genera la instancia y esa misma s se entrega al
agente. Aun asi, instance_seed y agent_seed se registran en columnas separadas,
porque cumplen funciones distintas.

Todo es secuencial, sin paralelismo: correr varios agentes a la vez haria que
compitieran por la CPU y distorsionaria los tiempos medidos.

La configuracion admite dos formas de declarar las configuraciones:

  "rejilla": {"N": [...], "K": [...], "rho": [...]}
      Producto de valores. M = floor(rho * N^2 + 0.5), es decir redondeo hacia
      arriba en la mitad. rho = M / N^2 es una herramienta metodologica nuestra
      para fijar M respecto al tamano del tablero, no un requisito del enunciado.

  "configuraciones": [{"N": .., "K": .., "M": ..}, ...]
      Lista explicita. rho se registra como M / N^2.

Uso, desde la raiz del repositorio:
    python -m experimentos.bateria experimentos/configuracion/piloto.json
"""

import argparse
import datetime
import json
import math
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
from src.nombrado import nombres_archivos


DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos"
)

COLUMNAS = corrida.COLUMNAS_CRUDO + ["rho"]

# Estado propio de la bateria para cuando la instancia no pudo generarse. Cada
# agente previsto recibe igualmente su fila, para que el fallo quede visible.
STATUS_ERROR_GENERACION = "generation_error"

# Guiones cuyo contenido se registra en los metadatos, para poder saber con que
# version del runner se obtuvo cada resultado aunque no estuviera confirmada.
GUIONES_REGISTRADOS = [
    os.path.join("experimentos", "bateria.py"),
    os.path.join("experimentos", "corrida.py"),
    os.path.join("experimentos", "registro.py"),
]


def calcular_m(n: int, rho: float) -> int:
    """M = floor(rho * N^2 + 0.5): redondeo explicito, sin el de banquero."""
    return int(math.floor(rho * n * n + 0.5))


def expandir_configuraciones(configuracion: Dict) -> List[Dict]:
    """Devuelve la lista de configuraciones {N, K, M, rho} a ejecutar."""
    if "rejilla" in configuracion:
        rejilla = configuracion["rejilla"]
        resultado = []

        for n in rejilla["N"]:
            for k in rejilla["K"]:
                for rho in rejilla["rho"]:
                    resultado.append({
                        "N": n, "K": k, "M": calcular_m(n, rho), "rho": rho,
                    })

        return resultado

    return [
        {
            "N": c["N"], "K": c["K"], "M": c["M"],
            "rho": round(c["M"] / float(c["N"] * c["N"]), 4),
        }
        for c in configuracion["configuraciones"]
    ]


def ejecutar_bateria(configuracion: Dict, ruta_configuracion: str,
                     directorio_resultados: str, raiz_datos: str,
                     sobrescribir: bool = False) -> RegistroExperimento:
    """
    Ejecuta la bateria completa y devuelve su registro.

    raiz_datos es la carpeta bajo la cual se guardan instancias y soluciones
    con la convencion del proyecto (datos/instancias, datos/soluciones). Es la
    raiz del repositorio salvo en las pruebas.
    """
    experimento = configuracion["experiment"]
    agentes = configuracion["agentes"]
    semillas = configuracion["semillas"]
    limite = float(configuracion["timeout_s"])
    configuraciones = expandir_configuraciones(configuracion)

    # El entorno se captura antes de crear la carpeta de resultados: si no,
    # git veria los propios archivos de esta corrida como cambios sin confirmar.
    entorno = metadatos_del_entorno()
    registro = RegistroExperimento(directorio_resultados, COLUMNAS, sobrescribir)

    metadatos = {
        "experiment": experimento,
        "configuracion": corrida.ruta_para_registro(ruta_configuracion),
        "sha256_configuracion": huella_de_configuracion(ruta_configuracion),
        "sha256_guiones": {
            guion.replace(os.sep, "/"): corrida.huella_archivo(
                os.path.join(corrida.RAIZ_REPOSITORIO, guion)
            )
            for guion in GUIONES_REGISTRADOS
        },
        "agentes": agentes,
        "semillas_pareadas": semillas,
        "timeout_s": limite,
        "configuraciones": configuraciones,
        "entorno": entorno,
        "inicio": _ahora(),
    }

    total = len(configuraciones) * len(semillas) * len(agentes)
    indice = 0

    for config in configuraciones:
        config_id = (
            "n" + str(config["N"]) + "_k" + str(config["K"]) + "_m" + str(config["M"])
        )

        for semilla in semillas:
            nombre_instancia, ruta_instancia, error = _generar_instancia(
                experimento, config, semilla, raiz_datos
            )

            for agente in agentes:
                indice = indice + 1
                run_id = experimento + "-" + format(indice, "04d")

                if error is not None:
                    fila, detalle = _fila_sin_instancia(
                        experimento, config_id, config, semilla, agente,
                        limite, run_id, error,
                    )
                else:
                    ruta_solucion = os.path.join(
                        raiz_datos,
                        nombres_archivos.ruta_solucion(
                            nombre_instancia, agente, semilla
                        ),
                    )
                    fila, detalle = corrida.ejecutar_corrida(
                        experimento=experimento,
                        config_id=config_id,
                        ruta_instancia=ruta_instancia,
                        nombre_instancia=nombre_instancia,
                        n=config["N"],
                        k=config["K"],
                        m=config["M"],
                        instance_seed=semilla,
                        agente=agente,
                        agent_seed=semilla,
                        timeout_s=limite,
                        ruta_solucion=ruta_solucion,
                        run_id=run_id,
                    )

                fila["rho"] = format(config["rho"], "g")
                registro.agregar(fila, detalle)
                _anunciar(indice, total, fila)

    metadatos["fin"] = _ahora()
    registro.escribir_metadatos(metadatos)

    return registro


# ----------------------------------------------------------------------
# Auxiliares
# ----------------------------------------------------------------------

def _generar_instancia(experimento: str, config: Dict, semilla: int,
                       raiz_datos: str):
    """
    Genera la instancia con main.py generar y devuelve (nombre, ruta, error).

    Se genera una sola vez por configuracion y semilla; todos los agentes
    reciben exactamente ese archivo.
    """
    nombre_archivo = nombres_archivos.nombre_archivo_instancia(
        experimento, semilla, config["N"], config["K"], config["M"]
    )
    ruta = os.path.join(
        raiz_datos, nombres_archivos.DIRECTORIO_INSTANCIAS, nombre_archivo
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    salida = corrida.ejecutar_main(
        [
            "generar",
            "--n", str(config["N"]),
            "--k", str(config["K"]),
            "--m", str(config["M"]),
            "--semilla", str(semilla),
            "--salida", ruta,
        ],
        120.0,
    )

    if salida.abortado is True or salida.codigo != 0 or os.path.isfile(ruta) is False:
        error = (
            "generar fallo (codigo " + str(salida.codigo) + "): "
            + salida.stderr.strip()
        )
        return (os.path.splitext(nombre_archivo)[0], ruta, error)

    return (os.path.splitext(nombre_archivo)[0], ruta, None)


def _fila_sin_instancia(experimento, config_id, config, semilla, agente,
                        limite, run_id, error):
    """Fila visible para una corrida que no pudo hacerse por falta de instancia."""
    fila = {columna: "" for columna in corrida.COLUMNAS_CRUDO}
    fila.update({
        "experiment": experimento,
        "config_id": config_id,
        "N": str(config["N"]),
        "K": str(config["K"]),
        "M": str(config["M"]),
        "instance_seed": str(semilla),
        "agent": agente,
        "agent_seed": str(semilla),
        "timeout_s": format(limite, ".6f"),
        "status": STATUS_ERROR_GENERACION,
        "run_id": run_id,
        "timestamp": _ahora(),
    })
    detalle = {"run_id": run_id, "error_generacion": error}
    return (fila, detalle)


def _anunciar(indice: int, total: int, fila: Dict[str, str]) -> None:
    """Una linea de progreso por corrida."""
    print(
        "[" + str(indice) + "/" + str(total) + "] " + fila["config_id"]
        + " rho=" + fila["rho"] + " s=" + fila["instance_seed"]
        + " " + fila["agent"] + " -> " + fila["status"]
        + " colocadas=" + fila["tiles_placed"] + "/" + fila["M"]
        + " ocupadas=" + fila["occupied_cells"]
        + " tiempo_s=" + fila["elapsed_s"]
        + " esfuerzo=" + fila["effort"]
        + " corte=" + (fila["search_cutoff"] or "-")
    )
    sys.stdout.flush()


def _ahora() -> str:
    """Marca de tiempo ISO sin fracciones de segundo."""
    return datetime.datetime.now().isoformat(timespec="seconds")


def main(argumentos: Optional[List[str]] = None) -> int:
    """Punto de entrada: ejecuta la bateria descrita en un JSON."""
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.bateria",
        description="Genera instancias y corre los agentes sobre ellas.",
    )
    analizador.add_argument("configuracion", help="Ruta del JSON de la bateria.")
    analizador.add_argument("--sobrescribir", action="store_true")
    opciones = analizador.parse_args(argumentos)

    ruta_configuracion = os.path.join(corrida.RAIZ_REPOSITORIO, opciones.configuracion)

    with open(ruta_configuracion, "r", encoding="utf-8") as archivo:
        configuracion = json.load(archivo)

    directorio = os.path.join(DIRECTORIO_RESULTADOS, configuracion["experiment"])

    try:
        registro = ejecutar_bateria(
            configuracion=configuracion,
            ruta_configuracion=ruta_configuracion,
            directorio_resultados=directorio,
            raiz_datos=corrida.RAIZ_REPOSITORIO,
            sobrescribir=opciones.sobrescribir,
        )
    except ErrorExperimentoExistente as error:
        print(str(error), file=sys.stderr)
        return 2

    print("")
    print("crudo=" + corrida.ruta_para_registro(registro.ruta_crudo))
    print("registros=" + corrida.ruta_para_registro(registro.ruta_registros))
    print("metadatos=" + corrida.ruta_para_registro(registro.ruta_metadatos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
