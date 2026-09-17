"""Pruebas de integracion de la ejecucion de un agente."""

import os

from src.agentes.agente_aleatorio import AgenteAleatorio
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente


RUTA_INSTANCIA_PEQUENA = os.path.join(
    "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)


def test_ejecucion_completa_produce_solucion(tmp_path):
    """Una ejecucion completa escribe un archivo de solucion valido."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_PEQUENA)
    agente = AgenteAleatorio(semilla=42)
    ruta_salida = os.path.join(str(tmp_path), "prueba.sol")

    resultado = EjecutorAgente().ejecutar(
        agente=agente,
        instancia=instancia,
        semilla=42,
        limite_tiempo_segundos=5.0,
        ruta_solucion=ruta_salida,
    )

    assert os.path.isfile(ruta_salida) is True
    assert resultado.colocaciones_rechazadas == 0
    assert resultado.metricas.fichas_colocadas == instancia.cantidad_fichas


def test_determinismo_por_semilla(tmp_path):
    """Dos ejecuciones con la misma semilla producen la misma solucion."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_PEQUENA)

    ruta_primera = os.path.join(str(tmp_path), "primera.sol")
    ruta_segunda = os.path.join(str(tmp_path), "segunda.sol")

    EjecutorAgente().ejecutar(
        agente=AgenteAleatorio(semilla=7),
        instancia=instancia,
        semilla=7,
        limite_tiempo_segundos=5.0,
        ruta_solucion=ruta_primera,
    )

    EjecutorAgente().ejecutar(
        agente=AgenteAleatorio(semilla=7),
        instancia=instancia,
        semilla=7,
        limite_tiempo_segundos=5.0,
        ruta_solucion=ruta_segunda,
    )

    with open(ruta_primera, "r", encoding="utf-8") as archivo:
        contenido_primera = archivo.read()

    with open(ruta_segunda, "r", encoding="utf-8") as archivo:
        contenido_segunda = archivo.read()

    assert contenido_primera == contenido_segunda


def test_semillas_distintas_producen_soluciones_distintas(tmp_path):
    """Semillas distintas normalmente llevan a decisiones distintas."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_PEQUENA)

    ruta_a = os.path.join(str(tmp_path), "semilla_a.sol")
    ruta_b = os.path.join(str(tmp_path), "semilla_b.sol")

    EjecutorAgente().ejecutar(
        agente=AgenteAleatorio(semilla=1),
        instancia=instancia,
        semilla=1,
        limite_tiempo_segundos=5.0,
        ruta_solucion=ruta_a,
    )

    EjecutorAgente().ejecutar(
        agente=AgenteAleatorio(semilla=999),
        instancia=instancia,
        semilla=999,
        limite_tiempo_segundos=5.0,
        ruta_solucion=ruta_b,
    )

    assert os.path.isfile(ruta_a) is True
    assert os.path.isfile(ruta_b) is True