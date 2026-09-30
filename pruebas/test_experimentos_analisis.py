"""
Pruebas del resumen, la revalidacion y las graficas de una bateria.

El resumen y las graficas se prueban con filas fabricadas; la revalidacion con
una corrida real que despues se altera a proposito.
"""

import os
import shutil

from experimentos import corrida
from experimentos.graficas import graficar_comparacion, graficar_escalabilidad
from experimentos.resumen import resumir
from experimentos.revalidar import revalidar_fila


def fila(agente="busqueda_astar", config_id="n4_k2_m8", n="4", k="2", m="8",
         status="ok", ocupadas="3", esfuerzo="100", tiempo="0.5",
         corte="False", semilla="1", reloj="False"):
    """Auxiliar que fabrica una fila minima del CSV crudo."""
    tipo = "expanded_nodes" if agente == "busqueda_astar" else "fitness_evaluations"
    ok = status == "ok"
    return {
        "experiment": "prueba", "config_id": config_id, "instance": "x",
        "N": n, "K": k, "M": m, "rho": "0.5",
        "instance_seed": semilla, "agent": agente, "agent_seed": semilla,
        "timeout_s": "10.000000", "status": status,
        "validated": "True" if ok else "",
        "tiles_placed": m if ok else "", "occupied_cells": ocupadas if ok else "",
        "largest_tile": "9" if ok else "", "elapsed_s": tiempo if ok else "",
        "effort": esfuerzo if ok else "", "effort_type": tipo if ok else "",
        "complete": "True" if ok else "",
        "search_cutoff": corte if (ok and agente == "busqueda_astar") else "",
        "clock_safeguard": reloj if ok else "",
        "solution_path": "x.sol" if ok else "", "run_id": "r" + semilla,
    }


# ----------------------------------------------------------------------
# Resumen
# ----------------------------------------------------------------------

def test_el_resumen_muestra_la_dispersion_entre_semillas():
    """Media, desviacion estandar muestral, minimo y maximo por agente."""
    resumen = resumir([
        fila(ocupadas="2", semilla="1"),
        fila(ocupadas="3", semilla="2"),
        fila(ocupadas="4", semilla="3"),
    ])[0]

    assert resumen["n_total"] == "3"
    assert resumen["n_ok"] == "3"
    assert resumen["occupied_mean"] == "3"
    assert resumen["occupied_std"] == "1"
    assert resumen["occupied_min"] == "2"
    assert resumen["occupied_max"] == "4"
    assert resumen["effort_type"] == "expanded_nodes"


def test_una_corrida_fallida_no_se_promedia_pero_se_cuenta():
    """Las estadisticas usan solo las ok; n_total incluye todas."""
    resumen = resumir([
        fila(ocupadas="2", semilla="1"),
        fila(ocupadas="4", semilla="2"),
        fila(status="agent_error", semilla="3"),
    ])[0]

    assert resumen["n_total"] == "3"
    assert resumen["n_ok"] == "2"
    assert resumen["occupied_mean"] == "3"
    assert resumen["prop_validated"] == "0.6667"


def test_los_esfuerzos_de_agentes_distintos_nunca_se_mezclan():
    """Cada fila del resumen corresponde a un solo agente y a una sola unidad."""
    resumen = resumir([
        fila(agente="busqueda_astar", esfuerzo="100"),
        fila(agente="evolutivo", esfuerzo="50000"),
    ])

    assert [r["agent"] for r in resumen] == ["busqueda_astar", "evolutivo"]
    assert resumen[0]["effort_mean"] == "100"
    assert resumen[1]["effort_mean"] == "50000"
    assert resumen[1]["effort_type"] == "fitness_evaluations"
    assert resumen[1]["prop_search_cutoff"] == ""


def test_el_resumen_expone_el_corte_de_busqueda_y_la_salvaguarda():
    """Proporcion de busquedas cortadas y de corridas con salvaguarda."""
    resumen = resumir([
        fila(corte="True", semilla="1"),
        fila(corte="True", semilla="2", reloj="True"),
        fila(corte="False", semilla="3"),
    ])[0]

    assert resumen["prop_search_cutoff"] == "0.6667"
    assert resumen["prop_clock_safeguard"] == "0.3333"


# ----------------------------------------------------------------------
# Revalidacion
# ----------------------------------------------------------------------

def test_la_revalidacion_acepta_una_solucion_intacta_y_detecta_una_alterada(tmp_path):
    """
    Una corrida real se revalida sin problemas; si su archivo de solucion se
    altera despues, la revalidacion lo detecta.
    """
    directorio_instancias = tmp_path / "datos" / "instancias"
    directorio_instancias.mkdir(parents=True)
    ruta_instancia = directorio_instancias / "ejemplo_n4_k3_m6.txt"
    shutil.copy(
        os.path.join(corrida.RAIZ_REPOSITORIO, "datos", "instancias", "ejemplo_n4_k3_m6.txt"),
        str(ruta_instancia),
    )

    ruta_solucion = tmp_path / "solucion.sol"
    registro, _ = corrida.ejecutar_corrida(
        experimento="prueba", config_id="ejemplo",
        ruta_instancia=str(ruta_instancia), nombre_instancia="ejemplo_n4_k3_m6",
        n=4, k=3, m=6, instance_seed=None, agente="busqueda_astar",
        agent_seed=1, timeout_s=2.0, ruta_solucion=str(ruta_solucion),
        run_id="prueba-0001",
    )
    registro["solution_path"] = "solucion.sol"

    assert revalidar_fila(registro, str(tmp_path)) == []

    lineas = ruta_solucion.read_text(encoding="utf-8").splitlines()
    ruta_solucion.write_text("\n".join(lineas[:-2] + lineas[-1:]) + "\n", encoding="utf-8")

    problemas = revalidar_fila(registro, str(tmp_path))

    assert any("SHA-256" in problema for problema in problemas)
    assert len(problemas) >= 2


# ----------------------------------------------------------------------
# Graficas
# ----------------------------------------------------------------------

def test_las_graficas_se_generan_desde_filas_crudas(tmp_path):
    """Solo se comprueba que se escriben los archivos, sin mirar pixeles."""
    filas = []
    for n, m in (("3", "5"), ("4", "8")):
        for k in ("2", "3"):
            for agente in ("busqueda_astar", "evolutivo"):
                for semilla in ("1", "2"):
                    filas.append(fila(
                        agente=agente, config_id="n" + n + "_k" + k + "_m" + m,
                        n=n, k=k, m=m, semilla=semilla, esfuerzo="1" + semilla + "00",
                    ))

    rutas = graficar_comparacion(filas, str(tmp_path / "comparacion"))
    rutas += graficar_escalabilidad(filas, str(tmp_path / "escalabilidad"))

    assert len(rutas) == 4
    assert all(os.path.getsize(ruta) > 0 for ruta in rutas)
