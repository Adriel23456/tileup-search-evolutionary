"""Pruebas del agente de busqueda A* y de sus heuristicas."""

import os

from src.agentes.agente_busqueda import AgenteBusquedaAEstrella
from src.agentes.heuristicas import (
    HeuristicaCero,
    HeuristicaCompactacion,
    HeuristicaCotaLiberaciones,
)
from src.dominio.estado_partida import EstadoPartida
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente


RUTA_INSTANCIA_EJEMPLO = os.path.join(
    "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)


def test_la_heuristica_admisible_no_sobreestima_en_un_caso_conocido():
    """En un tablero 2x2 con dos fichas del mismo color, h coincide con h*."""
    contenido = "2 1\n2\n1 1\n1 2\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")
    estado = EstadoPartida(instancia)

    heuristica = HeuristicaCotaLiberaciones()

    # Costo real optimo: colocar sin fusion cuesta (4-1) - 0 = 3, colocar
    # adyacente fusionando dos fichas cuesta (4-1) - 1 = 2. Total 5.
    assert heuristica.estimar(estado) == 5


def test_la_heuristica_admisible_vale_cero_en_la_meta():
    """Sin fichas pendientes, la estimacion debe ser nula."""
    contenido = "2 1\n1\n1 1\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")
    estado = EstadoPartida(instancia)
    estado.avanzar_ficha()

    assert HeuristicaCotaLiberaciones().estimar(estado) == 0
    assert HeuristicaCero().estimar(estado) == 0
    assert HeuristicaCompactacion().estimar(estado) == 0


def test_la_heuristica_agresiva_declara_no_ser_admisible():
    """La heuristica de compactacion debe reportarse como no admisible."""
    assert HeuristicaCompactacion().es_admisible is False
    assert HeuristicaCotaLiberaciones().es_admisible is True
    assert HeuristicaCero().es_admisible is True


def test_a_estrella_resuelve_una_instancia_pequena():
    """A* exacto debe consumir la secuencia completa de una instancia 4x4."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    estado_inicial = EstadoPartida(instancia)

    agente = AgenteBusquedaAEstrella(semilla=0, maximo_sucesores=0)
    colocaciones = agente.planificar(estado_inicial, 10.0)

    assert len(colocaciones) == instancia.cantidad_fichas
    assert agente.esfuerzo_acumulado() > 0


def test_a_estrella_supera_al_azar_en_celdas_ocupadas(tmp_path):
    """La busqueda informada debe dejar el tablero mas despejado que el azar."""
    from src.agentes.agente_aleatorio import AgenteAleatorio

    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    ejecutor = EjecutorAgente()

    resultado_busqueda = ejecutor.ejecutar(
        agente=AgenteBusquedaAEstrella(semilla=0, maximo_sucesores=0),
        instancia=instancia,
        semilla=0,
        limite_tiempo_segundos=10.0,
        ruta_solucion=os.path.join(str(tmp_path), "busqueda.sol"),
    )

    resultado_azar = ejecutor.ejecutar(
        agente=AgenteAleatorio(semilla=0),
        instancia=instancia,
        semilla=0,
        limite_tiempo_segundos=10.0,
        ruta_solucion=os.path.join(str(tmp_path), "azar.sol"),
    )

    assert resultado_busqueda.colocaciones_rechazadas == 0
    assert resultado_busqueda.metricas.celdas_ocupadas <= resultado_azar.metricas.celdas_ocupadas


def test_a_estrella_es_determinista(tmp_path):
    """Dos ejecuciones identicas deben producir la misma solucion."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    estado_inicial = EstadoPartida(instancia)

    primera = AgenteBusquedaAEstrella(semilla=0).planificar(estado_inicial, 5.0)
    segunda = AgenteBusquedaAEstrella(semilla=0).planificar(estado_inicial, 5.0)

    assert primera == segunda


def test_a_estrella_respeta_un_limite_de_tiempo_muy_corto():
    """Con el tiempo agotado, el agente completa la partida con avidez."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    estado_inicial = EstadoPartida(instancia)

    agente = AgenteBusquedaAEstrella(semilla=0, maximo_sucesores=0)
    colocaciones = agente.planificar(estado_inicial, 0.0001)

    assert len(colocaciones) == instancia.cantidad_fichas


def test_el_camino_producido_es_legal_segun_el_validador(tmp_path):
    """La solucion de A* debe pasar el validador independiente."""
    from src.validacion.lector_solucion import LectorSolucion
    from src.validacion.validador import Validador

    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    ruta_salida = os.path.join(str(tmp_path), "busqueda.sol")

    EjecutorAgente().ejecutar(
        agente=AgenteBusquedaAEstrella(semilla=0, maximo_sucesores=0),
        instancia=instancia,
        semilla=0,
        limite_tiempo_segundos=10.0,
        ruta_solucion=ruta_salida,
    )

    solucion = LectorSolucion().leer_desde_archivo(ruta_salida)
    dictamen = Validador().validar(instancia, solucion)

    assert dictamen.es_legal is True
    assert dictamen.esta_completa is True