"""Pruebas del orquestador de baterias experimentales."""

import json
import os

from experimentos.bateria import calcular_m, ejecutar_bateria, expandir_configuraciones
from experimentos.registro import leer_crudo


def test_m_se_redondea_hacia_arriba_en_la_mitad():
    """Sin redondeo de banquero: 4.5 da 5 y 12.5 da 13."""
    assert calcular_m(3, 0.5) == 5
    assert calcular_m(5, 0.5) == 13
    assert calcular_m(4, 1.0) == 16
    assert calcular_m(3, 1.5) == 14


def test_la_rejilla_se_expande_en_su_producto():
    """Cada combinacion de N, K y rho es una configuracion."""
    configuraciones = expandir_configuraciones(
        {"rejilla": {"N": [3, 4], "K": [2], "rho": [0.5, 1.0]}}
    )

    assert len(configuraciones) == 4
    assert configuraciones[0] == {"N": 3, "K": 2, "M": 5, "rho": 0.5}


def cargar_configuracion(nombre):
    """Auxiliar que lee una configuracion versionada del repositorio."""
    ruta = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "experimentos", "configuracion", nombre,
    )
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def corridas_esperadas(configuracion):
    """Configuraciones x semillas x agentes."""
    return (
        len(expandir_configuraciones(configuracion))
        * len(configuracion["semillas"])
        * len(configuracion["agentes"])
    )


def test_la_comparacion_formal_tiene_las_seis_configuraciones_acordadas():
    """6 configuraciones x 3 semillas pareadas x 2 agentes = 36 corridas."""
    configuracion = cargar_configuracion("comparacion.json")
    triples = [(c["N"], c["K"], c["M"]) for c in expandir_configuraciones(configuracion)]

    assert triples == [(3, 4, 14), (4, 4, 8), (4, 2, 16), (5, 2, 13), (5, 4, 25), (6, 4, 36)]
    assert configuracion["semillas"] == [1, 2, 3]
    assert configuracion["agentes"] == ["busqueda_astar", "evolutivo"]
    assert configuracion["timeout_s"] == 10
    assert corridas_esperadas(configuracion) == 36


def test_la_escalabilidad_es_el_factorial_de_tres_n_por_tres_k():
    """3 N x 3 K con rho = 0.5, 3 semillas pareadas, 2 agentes = 54 corridas."""
    configuracion = cargar_configuracion("escalabilidad.json")
    configuraciones = expandir_configuraciones(configuracion)
    triples = {(c["N"], c["K"], c["M"]) for c in configuraciones}

    assert triples == {
        (n, k, m) for n, m in [(3, 5), (4, 8), (5, 13)] for k in [2, 3, 4]
    }
    assert all(c["rho"] == 0.5 for c in configuraciones)
    assert configuracion["semillas"] == [1, 2, 3]
    assert configuracion["agentes"] == ["busqueda_astar", "evolutivo"]
    assert configuracion["timeout_s"] == 10
    assert corridas_esperadas(configuracion) == 54


def test_mini_bateria_con_ambos_agentes_sobre_la_misma_instancia(tmp_path):
    """
    Una configuracion y una semilla: una sola instancia generada, y ambos
    agentes corren sobre ese mismo archivo con la semilla pareada.
    """
    configuracion = {
        "experiment": "mini",
        "timeout_s": 0.5,
        "agentes": ["busqueda_astar", "evolutivo"],
        "semillas": [1],
        "configuraciones": [{"N": 3, "K": 2, "M": 4}],
    }
    ruta_configuracion = tmp_path / "mini.json"
    ruta_configuracion.write_text(json.dumps(configuracion), encoding="utf-8")

    registro = ejecutar_bateria(
        configuracion=configuracion,
        ruta_configuracion=str(ruta_configuracion),
        directorio_resultados=str(tmp_path / "resultados"),
        raiz_datos=str(tmp_path),
    )
    filas = leer_crudo(registro.ruta_crudo)

    instancias = os.listdir(str(tmp_path / "datos" / "instancias"))

    assert instancias == ["mini_s1_n3_k2_m4.txt"]
    assert [fila["agent"] for fila in filas] == ["busqueda_astar", "evolutivo"]
    assert all(fila["status"] == "ok" for fila in filas)
    assert all(fila["validated"] == "True" for fila in filas)
    assert all(fila["instance"] == "mini_s1_n3_k2_m4" for fila in filas)
    assert all(fila["instance_seed"] == "1" and fila["agent_seed"] == "1" for fila in filas)
    assert all(fila["rho"] == "0.4444" for fila in filas)
    assert os.path.isfile(registro.ruta_metadatos)
