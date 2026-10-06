"""
Calibracion simple del agente evolutivo por barrido de un parametro a la vez.

Procedimiento, fijado ANTES de ver los resultados:

  1. Se parte de una configuracion base (poblacion 20, torneo 3, cruce 0.70).
  2. Se evalua la base y seis variantes. Cada variante cambia un solo
     parametro y deja los otros dos en su valor base.
  3. Todas se corren sobre las mismas instancias de calibracion, que no
     coinciden con ninguna configuracion de las baterias formales, con
     semillas pareadas (la semilla genera la instancia y se entrega al agente).
  4. Gana la configuracion con menor media de celdas ocupadas. Ante empate gana
     la base, y entre variantes empatadas la de menor tiempo medio.

Los pesos de la aptitud (100/10/25) no se barren: replican el orden del
concurso, primero fichas colocadas y luego celdas ocupadas.

Cada solucion se valida con el validador independiente. El tiempo de cada
corrida lo fija el presupuesto determinista de evaluaciones del agente, de modo
que las celdas ocupadas no dependen de la velocidad de la maquina.

Uso, desde la raiz del repositorio y sin usar el equipo mientras corre:
    python -m experimentos.calibracion_evolutivo
    python -m experimentos.calibracion_evolutivo --sobrescribir
"""

import argparse
import csv
import json
import os
import platform
import statistics
import sys
import tempfile
from typing import Dict, List, Tuple

from experimentos import corrida
from src.agentes.agente_evolutivo import AgenteEvolutivo
from src.instancias.lector_instancia import LectorInstancia
from src.nombrado import nombres_archivos
from src.partidas.ejecutor_agente import EjecutorAgente
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


# Configuracion base: coincide con los valores por defecto del agente.
BASE = {
    "tamano_poblacion": 20,
    "tamano_torneo": 3,
    "probabilidad_cruce": 0.70,
}

# Valores alternativos de cada parametro, uno a la vez.
ALTERNATIVAS = {
    "tamano_poblacion": [10, 40],
    "tamano_torneo": [2, 5],
    "probabilidad_cruce": [0.50, 0.90],
}

# Prefijo corto de cada parametro en el nombre de la configuracion.
PREFIJOS = {
    "tamano_poblacion": "poblacion",
    "tamano_torneo": "torneo",
    "probabilidad_cruce": "cruce",
}

# Instancias de calibracion (N, K, M). Distintas de las baterias formales.
CONFIGURACIONES_DE_INSTANCIA = [(4, 3, 12), (5, 3, 20), (6, 4, 30)]

# Semillas pareadas: la misma semilla genera la instancia y se entrega al agente.
SEMILLAS = [101, 102, 103]

ETIQUETA_INSTANCIAS = "calibracion"
LIMITE_TIEMPO_SEGUNDOS = 10.0

DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos",
    "calibracion_evolutivo",
)

COLUMNAS_CRUDO = [
    "configuracion", "poblacion", "torneo", "cruce",
    "n", "k", "m", "semilla",
    "colocadas", "ocupadas", "tiempo_s", "evaluaciones",
    "valida", "salvaguarda_reloj",
]

COLUMNAS_RESUMEN = [
    "configuracion", "poblacion", "torneo", "cruce",
    "corridas", "corridas_validas",
    "ocupadas_media", "ocupadas_desv", "ocupadas_min", "ocupadas_max",
    "tiempo_medio_s", "tiempo_desv_s", "evaluaciones_media",
    "salvaguarda_reloj",
]


def construir_configuraciones() -> List[Tuple[str, Dict]]:
    """Devuelve la base y las seis variantes, en orden fijo."""
    configuraciones = [("base", dict(BASE))]

    for parametro in ["tamano_poblacion", "tamano_torneo", "probabilidad_cruce"]:
        for valor in ALTERNATIVAS[parametro]:
            variante = dict(BASE)
            variante[parametro] = valor
            nombre = PREFIJOS[parametro] + "=" + str(valor)
            configuraciones.append((nombre, variante))

    return configuraciones


def generar_instancia(n: int, k: int, m: int, semilla: int) -> str:
    """Genera la instancia con el subcomando real y devuelve su ruta."""
    nombre_archivo = nombres_archivos.nombre_archivo_instancia(
        ETIQUETA_INSTANCIAS, semilla, n, k, m
    )
    ruta = os.path.join(
        corrida.RAIZ_REPOSITORIO, nombres_archivos.DIRECTORIO_INSTANCIAS,
        nombre_archivo,
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    salida = corrida.ejecutar_main(
        ["generar", "--n", str(n), "--k", str(k), "--m", str(m),
         "--semilla", str(semilla), "--salida", ruta],
        120.0,
    )

    if salida.codigo != 0 or os.path.isfile(ruta) is False:
        raise RuntimeError(
            "No se pudo generar la instancia: " + salida.stderr.strip()
        )

    return ruta


def correr_una(configuracion: Dict, instancia, semilla: int,
               directorio_temporal: str) -> Dict:
    """Corre el agente, valida la solucion y devuelve las metricas."""
    agente = AgenteEvolutivo(
        semilla=semilla,
        tamano_poblacion=configuracion["tamano_poblacion"],
        tamano_torneo=configuracion["tamano_torneo"],
        probabilidad_cruce=configuracion["probabilidad_cruce"],
    )

    ruta_solucion = os.path.join(directorio_temporal, "solucion.sol")

    resultado = EjecutorAgente().ejecutar(
        agente=agente,
        instancia=instancia,
        semilla=semilla,
        limite_tiempo_segundos=LIMITE_TIEMPO_SEGUNDOS,
        ruta_solucion=ruta_solucion,
    )

    solucion = LectorSolucion().leer_desde_archivo(ruta_solucion)
    dictamen = Validador().validar(instancia, solucion)

    es_valida = (
        dictamen.es_legal is True
        and dictamen.esta_completa is True
        and resultado.colocaciones_rechazadas == 0
    )

    return {
        "colocadas": resultado.metricas.fichas_colocadas,
        "ocupadas": resultado.metricas.celdas_ocupadas,
        "tiempo_s": resultado.metricas.tiempo_segundos,
        "evaluaciones": resultado.metricas.esfuerzo_algoritmo,
        "valida": es_valida,
        "salvaguarda_reloj": agente.corto_por_reloj,
    }


def resumir(nombre: str, configuracion: Dict, filas: List[Dict]) -> Dict:
    """Agrega las corridas de una configuracion."""
    propias = [f for f in filas if f["configuracion"] == nombre]
    ocupadas = [f["ocupadas"] for f in propias]
    tiempos = [f["tiempo_s"] for f in propias]
    evaluaciones = [f["evaluaciones"] for f in propias]

    return {
        "configuracion": nombre,
        "poblacion": configuracion["tamano_poblacion"],
        "torneo": configuracion["tamano_torneo"],
        "cruce": configuracion["probabilidad_cruce"],
        "corridas": len(propias),
        "corridas_validas": len([f for f in propias if f["valida"] is True]),
        "ocupadas_media": round(statistics.mean(ocupadas), 4),
        "ocupadas_desv": round(statistics.stdev(ocupadas), 4),
        "ocupadas_min": min(ocupadas),
        "ocupadas_max": max(ocupadas),
        "tiempo_medio_s": round(statistics.mean(tiempos), 4),
        "tiempo_desv_s": round(statistics.stdev(tiempos), 4),
        "evaluaciones_media": round(statistics.mean(evaluaciones), 1),
        "salvaguarda_reloj": len(
            [f for f in propias if f["salvaguarda_reloj"] is True]
        ),
    }


def elegir_ganadora(resumenes: List[Dict]) -> Dict:
    """
    Aplica la regla fijada de antemano.

    Menor media de celdas ocupadas; ante empate, la base; entre variantes
    empatadas, menor tiempo medio.
    """
    def clave(resumen: Dict) -> tuple:
        es_variante = 0 if resumen["configuracion"] == "base" else 1
        return (resumen["ocupadas_media"], es_variante, resumen["tiempo_medio_s"])

    return min(resumenes, key=clave)


def escribir_csv(ruta: str, columnas: List[str], filas: List[Dict]) -> None:
    """Escribe un CSV con encabezado."""
    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def main(argumentos=None) -> int:
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.calibracion_evolutivo",
        description="Calibracion del agente evolutivo por barrido simple.",
    )
    analizador.add_argument("--sobrescribir", action="store_true")
    opciones = analizador.parse_args(argumentos)

    ruta_crudo = os.path.join(DIRECTORIO_RESULTADOS, "crudo.csv")

    if os.path.isfile(ruta_crudo) is True and opciones.sobrescribir is False:
        print(
            "Ya existe " + corrida.ruta_para_registro(ruta_crudo)
            + ". Use --sobrescribir para reemplazarlo.",
            file=sys.stderr,
        )
        return 2

    os.makedirs(DIRECTORIO_RESULTADOS, exist_ok=True)

    lector = LectorInstancia()
    configuraciones = construir_configuraciones()
    filas: List[Dict] = []

    total = (
        len(configuraciones) * len(CONFIGURACIONES_DE_INSTANCIA) * len(SEMILLAS)
    )
    contador = 0

    with tempfile.TemporaryDirectory() as directorio_temporal:
        for (n, k, m) in CONFIGURACIONES_DE_INSTANCIA:
            for semilla in SEMILLAS:
                ruta = generar_instancia(n, k, m, semilla)
                instancia = lector.leer_desde_archivo(ruta)

                for nombre, configuracion in configuraciones:
                    contador = contador + 1
                    metricas = correr_una(
                        configuracion, instancia, semilla, directorio_temporal
                    )

                    fila = {
                        "configuracion": nombre,
                        "poblacion": configuracion["tamano_poblacion"],
                        "torneo": configuracion["tamano_torneo"],
                        "cruce": configuracion["probabilidad_cruce"],
                        "n": n, "k": k, "m": m, "semilla": semilla,
                    }
                    fila.update(metricas)
                    filas.append(fila)

                    print(
                        "[" + str(contador) + "/" + str(total) + "] "
                        + nombre.ljust(14) + " n" + str(n) + "_k" + str(k)
                        + "_m" + str(m) + " s=" + str(semilla)
                        + " ocupadas=" + str(metricas["ocupadas"])
                        + " valida=" + str(metricas["valida"])
                    )
                    sys.stdout.flush()

    resumenes = [
        resumir(nombre, configuracion, filas)
        for nombre, configuracion in configuraciones
    ]
    ganadora = elegir_ganadora(resumenes)

    escribir_csv(ruta_crudo, COLUMNAS_CRUDO, filas)
    escribir_csv(
        os.path.join(DIRECTORIO_RESULTADOS, "resumen.csv"),
        COLUMNAS_RESUMEN, resumenes,
    )

    metadatos = {
        "base": BASE,
        "alternativas": ALTERNATIVAS,
        "instancias": CONFIGURACIONES_DE_INSTANCIA,
        "semillas_pareadas": SEMILLAS,
        "limite_tiempo_s": LIMITE_TIEMPO_SEGUNDOS,
        "regla": "menor media de ocupadas; empate: base; luego menor tiempo",
        "ganadora": ganadora["configuracion"],
        "python": platform.python_version(),
        "plataforma": platform.platform(),
    }
    with open(os.path.join(DIRECTORIO_RESULTADOS, "metadatos.json"),
              "w", encoding="utf-8") as archivo:
        json.dump(metadatos, archivo, indent=2, ensure_ascii=False)

    print("")
    print("configuracion   ocupadas_media  desv   min max  tiempo_s  validas  salvaguarda")
    for r in resumenes:
        print(
            r["configuracion"].ljust(15),
            format(r["ocupadas_media"], ".2f").rjust(10),
            format(r["ocupadas_desv"], ".2f").rjust(6),
            str(r["ocupadas_min"]).rjust(4),
            str(r["ocupadas_max"]).rjust(3),
            format(r["tiempo_medio_s"], ".2f").rjust(9),
            (str(r["corridas_validas"]) + "/" + str(r["corridas"])).rjust(8),
            str(r["salvaguarda_reloj"]).rjust(8),
        )

    print("")
    print("ganadora=" + ganadora["configuracion"])
    return 0


if __name__ == "__main__":
    sys.exit(main())