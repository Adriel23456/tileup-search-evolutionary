"""
Pruebas del criterio de paro por presupuesto determinista.

Ambos agentes se detienen al agotar un presupuesto de trabajo que depende solo
de su entrada; el reloj queda como salvaguarda del limite obligatorio. Mientras
la salvaguarda no actua, la misma entrada produce la misma solucion y el mismo
esfuerzo, que es lo que exige el enunciado.
"""

import hashlib
import os
import time

from src.agentes import agente_busqueda, agente_evolutivo
from src.agentes.agente_busqueda import (
    LIMITE_NODOS_POR_DEFECTO,
    presupuesto_de_nodos,
)
from src.agentes.agente_evolutivo import presupuesto_de_evaluaciones
from src.agentes.registro_agentes import RegistroAgentes
from src.cli.ejecutor_consola import EjecutorConsola
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ruta_instancia(nombre):
    """Auxiliar que arma la ruta de una instancia versionada."""
    return os.path.join(RAIZ, "datos", "instancias", nombre)


def resolver(tmp_path, nombre_agente, instancia, limite, archivo):
    """Planifica, escribe la solucion y devuelve (agente, resultado, hash, s)."""
    agente = RegistroAgentes().construir(nombre_agente, 1)
    ruta = str(tmp_path / archivo)

    inicio = time.perf_counter()
    resultado = EjecutorAgente().ejecutar(
        agente=agente, instancia=instancia, semilla=1,
        limite_tiempo_segundos=limite, ruta_solucion=ruta,
    )
    segundos = time.perf_counter() - inicio

    with open(ruta, "rb") as archivo_solucion:
        huella = hashlib.sha256(archivo_solucion.read()).hexdigest()

    return agente, resultado, huella, segundos, ruta


# ----------------------------------------------------------------------
# A y B. Formulas de los presupuestos
# ----------------------------------------------------------------------

def test_formula_del_presupuesto_de_a_estrella():
    """min(tope de memoria, floor(2200 * T))."""
    assert presupuesto_de_nodos(10.0) == 22000
    assert presupuesto_de_nodos(2.5) == 5500
    assert presupuesto_de_nodos(0.001) == 2
    assert presupuesto_de_nodos(100.0) == LIMITE_NODOS_POR_DEFECTO


def test_formula_del_presupuesto_del_evolutivo():
    """floor(20000 * T / M), al menos 1; con T = 10 reproduce la tabla acordada."""
    tabla = {5: 40000, 8: 25000, 13: 15384, 14: 14285, 16: 12500, 25: 8000, 36: 5555}

    for cantidad_fichas, esperado in tabla.items():
        assert presupuesto_de_evaluaciones(10.0, cantidad_fichas) == esperado

    assert presupuesto_de_evaluaciones(10.0, 0) == 1
    assert presupuesto_de_evaluaciones(0.0001, 36) == 1


# ----------------------------------------------------------------------
# C y D. Misma entrada, misma solucion y mismo esfuerzo
# ----------------------------------------------------------------------

def test_a_estrella_con_presupuesto_es_reproducible(tmp_path):
    """
    En una instancia donde A* no llega a la meta, dos corridas identicas agotan
    el mismo presupuesto y entregan la misma solucion.
    """
    instancia = LectorInstancia().leer_desde_archivo(ruta_instancia("ejemplo_n5_k3_m12.txt"))

    primero = resolver(tmp_path, "busqueda_astar", instancia, 2.0, "a.sol")
    segundo = resolver(tmp_path, "busqueda_astar", instancia, 2.0, "b.sol")

    for agente, resultado, _, _, _ in (primero, segundo):
        assert agente.corto_por_reloj is False
        assert agente.alcanzo_la_meta is False
        assert resultado.metricas.esfuerzo_algoritmo == presupuesto_de_nodos(2.0)

    assert primero[2] == segundo[2]


def test_evolutivo_con_presupuesto_es_reproducible(tmp_path):
    """Dos corridas identicas del evolutivo: mismas evaluaciones, misma solucion."""
    instancia = LectorInstancia().leer_desde_archivo(ruta_instancia("ejemplo_n5_k3_m12.txt"))

    primero = resolver(tmp_path, "evolutivo", instancia, 1.0, "a.sol")
    segundo = resolver(tmp_path, "evolutivo", instancia, 1.0, "b.sol")

    for agente, resultado, _, _, _ in (primero, segundo):
        assert agente.corto_por_reloj is False
        assert resultado.metricas.esfuerzo_algoritmo == presupuesto_de_evaluaciones(1.0, 12)

    assert primero[2] == segundo[2]


# ----------------------------------------------------------------------
# E. La salvaguarda del reloj
# ----------------------------------------------------------------------

def test_la_salvaguarda_actua_queda_registrada_y_respeta_el_limite(
        tmp_path, monkeypatch, capsys):
    """
    Con un T pequeno y un presupuesto que no puede agotarse a tiempo, el reloj
    detiene a ambos agentes: lo indican, la solucion sigue siendo legal y el
    tiempo no excede el limite.
    """
    monkeypatch.setattr(agente_busqueda, "NODOS_POR_SEGUNDO_DE_LIMITE", 10 ** 9)
    monkeypatch.setattr(agente_evolutivo, "COLOCACIONES_POR_SEGUNDO_DE_LIMITE", 10 ** 12)

    limite = 0.3
    instancia = LectorInstancia().leer_desde_archivo(ruta_instancia("ejemplo_n6_k4_m24.txt"))

    for nombre_agente in ("busqueda_astar", "evolutivo"):
        agente, resultado, _, segundos, ruta = resolver(
            tmp_path, nombre_agente, instancia, limite, nombre_agente + ".sol"
        )
        dictamen = Validador().validar(instancia, LectorSolucion().leer_desde_archivo(ruta))

        assert agente.corto_por_reloj is True
        assert resultado.metricas.tiempo_segundos <= limite
        assert segundos < limite + 1.0
        assert dictamen.es_legal is True

    codigo = EjecutorConsola().ejecutar_agente(
        ruta_instancia=ruta_instancia("ejemplo_n6_k4_m24.txt"),
        nombre_agente="evolutivo",
        semilla=1,
        limite_tiempo_segundos=limite,
        ruta_salida=str(tmp_path / "consola.sol"),
        silencioso=True,
    )

    assert codigo == 0
    assert "Advertencia: el reloj de salvaguarda" in capsys.readouterr().out
