"""Pruebas del informe de la verificacion de determinismo."""

from experimentos.determinismo import construir_informe


def fila(sha, status="ok", ocupadas="6", esfuerzo="100", limite="10.000000"):
    """Auxiliar que fabrica una fila minima del CSV crudo."""
    return {
        "instance": "ejemplo",
        "agent": "evolutivo",
        "agent_seed": "1",
        "timeout_s": limite,
        "status": status,
        "solution_sha256": sha,
        "tiles_placed": "12",
        "occupied_cells": ocupadas,
        "largest_tile": "9",
        "search_cutoff": "",
        "effort_type": "fitness_evaluations",
        "effort": esfuerzo,
        "elapsed_s": "9.800000",
    }


def test_soluciones_identicas_con_esfuerzo_variable():
    """Mismo hash en todas: identicas, aunque el esfuerzo varie."""
    grupo = construir_informe([
        fila("aaa", esfuerzo="100"),
        fila("aaa", esfuerzo="120"),
    ])[0]

    assert grupo["identical_solutions"] == "True"
    assert grupo["distinct_solutions"] == "1"
    assert grupo["effort_range_pct"] == "20.00"


def test_soluciones_distintas_se_detectan():
    """Dos hashes distintos con entradas identicas no son deterministas."""
    grupo = construir_informe([fila("aaa"), fila("bbb", ocupadas="5")])[0]

    assert grupo["identical_solutions"] == "False"
    assert grupo["distinct_solutions"] == "2"
    assert grupo["occupied_cells_values"] == "6;5"


def test_una_corrida_sin_solucion_no_cuenta_como_identica():
    """Si falta una solucion, no se puede afirmar que todas coinciden."""
    grupo = construir_informe([fila("aaa"), fila("", status="agent_error")])[0]

    assert grupo["identical_solutions"] == "False"
    assert grupo["runs"] == "2"
    assert grupo["n_ok"] == "1"
    assert grupo["statuses"] == "ok;agent_error"


def test_limites_distintos_son_grupos_distintos():
    """Cambiar el limite de tiempo cambia las entradas: otro grupo."""
    informe = construir_informe([
        fila("aaa", limite="5.000000"),
        fila("bbb", limite="10.000000"),
    ])

    assert len(informe) == 2
    assert all(grupo["identical_solutions"] == "True" for grupo in informe)
