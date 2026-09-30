"""
Graficas de una bateria a partir de su CSV crudo.

Lee exclusivamente resultados/experimentos/<experimento>/crudo.csv y escribe
PNG en resultados/experimentos/<experimento>/graficas/. Ningun valor esta
codificado a mano: todo sale de las corridas con status=ok, y si alguna no lo
esta el pie de la figura muestra n_ok/n_total.

Cada figura muestra las semillas individuales como puntos y, encima, la media
con barras de una desviacion estandar muestral.

El esfuerzo de A* (nodos expandidos) y el del evolutivo (evaluaciones de
aptitud) se dibujan siempre en paneles separados, cada uno con su unidad: no
son magnitudes comparables entre si.

Uso, desde la raiz del repositorio:
    python -m experimentos.graficas comparacion
    python -m experimentos.graficas escalabilidad
"""

import argparse
import os
import statistics
import sys
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from experimentos import corrida  # noqa: E402
from experimentos.registro import leer_crudo  # noqa: E402
from src.agentes.agente_busqueda import presupuesto_de_nodos  # noqa: E402


DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos"
)

AGENTE_BUSQUEDA = "busqueda_astar"
AGENTE_EVOLUTIVO = "evolutivo"

ETIQUETAS_AGENTE = {
    AGENTE_BUSQUEDA: "A* (busqueda_astar)",
    AGENTE_EVOLUTIVO: "Evolutivo",
}

COLORES_AGENTE = {
    AGENTE_BUSQUEDA: "#1f77b4",
    AGENTE_EVOLUTIVO: "#d62728",
}

COLORES_SERIE = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a"]


# ----------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------

def _valores(filas: List[Dict[str, str]], columna: str) -> List[float]:
    """Valores numericos de una columna, omitiendo vacios."""
    return [float(fila[columna]) for fila in filas if fila[columna] != ""]


def _media_y_desviacion(valores: List[float]):
    """Media y desviacion estandar muestral (0 si hay un solo valor)."""
    media = statistics.mean(valores)
    desviacion = statistics.stdev(valores) if len(valores) >= 2 else 0.0
    return media, desviacion


def _pie(filas: List[Dict[str, str]]) -> str:
    """Pie de figura con la procedencia y el conteo de corridas validas."""
    ok = sum(1 for fila in filas if fila["status"] == corrida.STATUS_OK)
    return (
        "Fuente: crudo.csv. Corridas ok: " + str(ok) + "/" + str(len(filas))
        + ". Puntos: semillas individuales; barras: media ± 1 desviacion estandar."
    )


def _ok(filas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Solo las corridas validas."""
    return [fila for fila in filas if fila["status"] == corrida.STATUS_OK]


def _limite(filas: List[Dict[str, str]]) -> float:
    """Limite de tiempo comun de la bateria."""
    return float(filas[0]["timeout_s"])


# ----------------------------------------------------------------------
# Comparacion
# ----------------------------------------------------------------------

def graficar_comparacion(filas: List[Dict[str, str]], directorio: str) -> List[str]:
    """Figura de calidad y tiempo, y figura de esfuerzo por agente."""
    validas = _ok(filas)
    configuraciones = _en_orden(fila["config_id"] for fila in filas)
    posiciones = {config: indice for indice, config in enumerate(configuraciones)}
    desplazamiento = {AGENTE_BUSQUEDA: -0.15, AGENTE_EVOLUTIVO: 0.15}
    limite = _limite(filas)

    figura, ejes = plt.subplots(1, 3, figsize=(16, 5))
    paneles = [
        ("fraccion", "Fichas colocadas / M", "Fraccion de la secuencia colocada"),
        ("occupied_cells", "Celdas ocupadas al terminar", "Celdas"),
        ("elapsed_s", "Tiempo de planificacion", "Segundos"),
    ]

    for eje, (columna, titulo, unidad) in zip(ejes, paneles):
        for agente in (AGENTE_BUSQUEDA, AGENTE_EVOLUTIVO):
            for config in configuraciones:
                grupo = [
                    f for f in validas
                    if f["agent"] == agente and f["config_id"] == config
                ]
                if len(grupo) == 0:
                    continue

                if columna == "fraccion":
                    valores = [
                        float(f["tiles_placed"]) / float(f["M"]) for f in grupo
                    ]
                else:
                    valores = _valores(grupo, columna)

                x = posiciones[config] + desplazamiento[agente]
                _puntos_y_media(eje, x, valores, COLORES_AGENTE[agente])

        if columna == "elapsed_s":
            eje.axhline(limite, color="gray", linestyle=":", linewidth=1)
            eje.text(-0.4, limite, " limite T", va="bottom", color="gray", fontsize=8)

        eje.set_title(titulo)
        eje.set_ylabel(unidad)
        eje.set_xlabel("Configuracion (N, K, M)")
        _etiquetas_de_configuracion(eje, configuraciones)

    _leyenda_de_agentes(ejes[0])
    figura.suptitle(
        "Comparacion: ambos agentes sobre las mismas instancias "
        "(3 semillas por configuracion, T = " + format(limite, "g") + " s)"
    )
    figura.text(0.01, 0.01, _pie(filas), fontsize=8, color="dimgray")
    rutas = [_guardar(figura, directorio, "comparacion_calidad_y_tiempo.png")]

    figura, ejes = plt.subplots(1, 2, figsize=(14, 5))
    paneles = [
        (AGENTE_BUSQUEDA, "A*: nodos expandidos", "Nodos expandidos (escala log)"),
        (AGENTE_EVOLUTIVO, "Evolutivo: evaluaciones de aptitud",
         "Evaluaciones de aptitud (escala log)"),
    ]

    for eje, (agente, titulo, unidad) in zip(ejes, paneles):
        for config in configuraciones:
            grupo = [
                f for f in validas if f["agent"] == agente and f["config_id"] == config
            ]
            if len(grupo) > 0:
                _puntos_y_media(
                    eje, posiciones[config], _valores(grupo, "effort"),
                    COLORES_AGENTE[agente],
                )

        if agente == AGENTE_BUSQUEDA:
            eje.axhline(presupuesto_de_nodos(limite), color="gray", linestyle=":", linewidth=1)
            eje.text(
                -0.4, presupuesto_de_nodos(limite), " presupuesto de nodos para T",
                va="bottom", color="gray", fontsize=8,
            )

        eje.set_yscale("log")
        eje.set_title(titulo)
        eje.set_ylabel(unidad)
        eje.set_xlabel("Configuracion (N, K, M)")
        _etiquetas_de_configuracion(eje, configuraciones)

    figura.suptitle(
        "Comparacion: esfuerzo de cada agente en su propia unidad "
        "(nodos y evaluaciones no son comparables entre si)"
    )
    figura.text(0.01, 0.01, _pie(filas), fontsize=8, color="dimgray")
    rutas.append(_guardar(figura, directorio, "comparacion_esfuerzo.png"))

    return rutas


# ----------------------------------------------------------------------
# Escalabilidad
# ----------------------------------------------------------------------

def graficar_escalabilidad(filas: List[Dict[str, str]], directorio: str) -> List[str]:
    """Una figura frente a N (una linea por K) y otra frente a K (una por N)."""
    return [
        _figura_escalabilidad(filas, directorio, "N", "K", "escalabilidad_vs_n.png"),
        _figura_escalabilidad(filas, directorio, "K", "N", "escalabilidad_vs_k.png"),
    ]


def _figura_escalabilidad(filas, directorio, factor, fijo, nombre_archivo) -> str:
    """
    Seis paneles frente a un factor, con una linea por valor del otro.

    Fila superior, A*: tiempo, nodos expandidos y proporcion de corridas en
    que la busqueda se corto. Fila inferior, evolutivo: tiempo, evaluaciones
    de aptitud, y celdas ocupadas de ambos agentes.
    """
    validas = _ok(filas)
    niveles = sorted({int(fila[fijo]) for fila in filas})
    limite = _limite(filas)

    figura, ejes = plt.subplots(2, 3, figsize=(17, 9))

    paneles = [
        (ejes[0][0], AGENTE_BUSQUEDA, "elapsed_s", "A*: tiempo", "Segundos", False),
        (ejes[0][1], AGENTE_BUSQUEDA, "effort", "A*: nodos expandidos",
         "Nodos expandidos (escala log)", True),
        (ejes[1][0], AGENTE_EVOLUTIVO, "elapsed_s", "Evolutivo: tiempo", "Segundos", False),
        (ejes[1][1], AGENTE_EVOLUTIVO, "effort", "Evolutivo: evaluaciones de aptitud",
         "Evaluaciones de aptitud (escala log)", True),
    ]

    for eje, agente, columna, titulo, unidad, logaritmica in paneles:
        for indice, nivel in enumerate(niveles):
            _serie(eje, validas, agente, factor, fijo, nivel, columna,
                   COLORES_SERIE[indice], fijo + "=" + str(nivel), "-")

        if columna == "elapsed_s":
            eje.axhline(limite, color="gray", linestyle=":", linewidth=1)
        if agente == AGENTE_BUSQUEDA and columna == "effort":
            eje.axhline(presupuesto_de_nodos(limite), color="gray", linestyle=":", linewidth=1)
        if logaritmica is True:
            eje.set_yscale("log")

        eje.set_title(titulo)
        eje.set_ylabel(unidad)
        eje.set_xlabel(factor)
        eje.legend(fontsize=8)

    eje = ejes[0][2]
    for indice, nivel in enumerate(niveles):
        xs = sorted({int(f[factor]) for f in filas if int(f[fijo]) == nivel})
        proporciones = []
        for x in xs:
            grupo = [
                f for f in filas
                if f["agent"] == AGENTE_BUSQUEDA
                and int(f[fijo]) == nivel and int(f[factor]) == x
            ]
            cortes = sum(1 for f in grupo if f["search_cutoff"] == "True")
            proporciones.append(cortes / float(len(grupo)))
        eje.plot(xs, proporciones, marker="o", color=COLORES_SERIE[indice],
                 label=fijo + "=" + str(nivel))
    eje.set_ylim(-0.05, 1.05)
    eje.set_title("A*: corridas con corte de busqueda")
    eje.set_ylabel("Proporcion de semillas (search_cutoff)")
    eje.set_xlabel(factor)
    eje.legend(fontsize=8)

    eje = ejes[1][2]
    for indice, nivel in enumerate(niveles):
        for agente, estilo in ((AGENTE_BUSQUEDA, "-"), (AGENTE_EVOLUTIVO, "--")):
            _serie(eje, validas, agente, factor, fijo, nivel, "occupied_cells",
                   COLORES_SERIE[indice],
                   ("A* " if agente == AGENTE_BUSQUEDA else "Evo ") + fijo + "=" + str(nivel),
                   estilo)
    eje.set_title("Celdas ocupadas (A* continua, Evo discontinua)")
    eje.set_ylabel("Celdas")
    eje.set_xlabel(factor)
    eje.legend(fontsize=7, ncol=2)

    for fila_de_ejes in ejes:
        for eje in fila_de_ejes:
            eje.set_xticks(sorted({int(f[factor]) for f in filas}))

    figura.suptitle(
        "Escalabilidad frente a " + factor + " (una linea por valor de " + fijo
        + "; M = round(0.5 N^2); 3 semillas; T = " + format(limite, "g") + " s)"
    )
    figura.text(0.01, 0.005, _pie(filas), fontsize=8, color="dimgray")
    return _guardar(figura, directorio, nombre_archivo)


def _serie(eje, filas, agente, factor, fijo, nivel, columna, color, etiqueta, estilo):
    """Una linea de medias con barras de desviacion y los puntos por semilla."""
    xs = sorted({int(f[factor]) for f in filas if int(f[fijo]) == nivel})
    medias = []
    desviaciones = []
    xs_con_datos = []

    for x in xs:
        grupo = [
            f for f in filas
            if f["agent"] == agente and int(f[fijo]) == nivel and int(f[factor]) == x
        ]
        valores = _valores(grupo, columna)
        if len(valores) == 0:
            continue

        media, desviacion = _media_y_desviacion(valores)
        xs_con_datos.append(x)
        medias.append(media)
        desviaciones.append(desviacion)
        eje.scatter([x] * len(valores), valores, s=12, color=color, alpha=0.4)

    eje.errorbar(
        xs_con_datos, medias, yerr=desviaciones, color=color, linestyle=estilo,
        marker="o", capsize=3, label=etiqueta,
    )


# ----------------------------------------------------------------------
# Auxiliares de dibujo
# ----------------------------------------------------------------------

def _puntos_y_media(eje, x, valores, color):
    """Puntos por semilla y media con barra de una desviacion estandar."""
    if len(valores) == 0:
        return

    media, desviacion = _media_y_desviacion(valores)
    eje.scatter([x] * len(valores), valores, s=16, color=color, alpha=0.45)
    eje.errorbar([x], [media], yerr=[desviacion], color=color, marker="_",
                 markersize=14, capsize=4, linewidth=1.5)


def _etiquetas_de_configuracion(eje, configuraciones):
    """Rotula el eje x con los identificadores de configuracion."""
    eje.set_xticks(range(len(configuraciones)))
    eje.set_xticklabels(configuraciones, rotation=30, ha="right", fontsize=8)


def _leyenda_de_agentes(eje):
    """Leyenda comun con el color de cada agente."""
    for agente in (AGENTE_BUSQUEDA, AGENTE_EVOLUTIVO):
        eje.scatter([], [], color=COLORES_AGENTE[agente], label=ETIQUETAS_AGENTE[agente])
    eje.legend(fontsize=8, loc="lower left")


def _guardar(figura, directorio, nombre_archivo) -> str:
    """Guarda la figura y devuelve su ruta."""
    os.makedirs(directorio, exist_ok=True)
    ruta = os.path.join(directorio, nombre_archivo)
    figura.tight_layout(rect=(0, 0.03, 1, 0.95))
    figura.savefig(ruta, dpi=120)
    plt.close(figura)
    return ruta


def _en_orden(valores) -> List[str]:
    """Valores sin repetir en el orden en que aparecen."""
    vistos: List[str] = []
    for valor in valores:
        if valor not in vistos:
            vistos.append(valor)
    return vistos


GRAFICADORES = {
    "comparacion": graficar_comparacion,
    "escalabilidad": graficar_escalabilidad,
}


def main(argumentos: Optional[List[str]] = None) -> int:
    """Punto de entrada: genera las graficas de la bateria indicada."""
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.graficas",
        description="Genera las graficas de una bateria desde su CSV crudo.",
    )
    analizador.add_argument("experimento", choices=sorted(GRAFICADORES))
    opciones = analizador.parse_args(argumentos)

    directorio = os.path.join(DIRECTORIO_RESULTADOS, opciones.experimento)
    filas = leer_crudo(os.path.join(directorio, "crudo.csv"))
    rutas = GRAFICADORES[opciones.experimento](filas, os.path.join(directorio, "graficas"))

    for ruta in rutas:
        print("grafica=" + corrida.ruta_para_registro(ruta))

    return 0


if __name__ == "__main__":
    sys.exit(main())
