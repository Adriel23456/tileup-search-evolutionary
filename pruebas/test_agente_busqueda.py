"""Pruebas del agente de busqueda A* y de sus heuristicas."""

import os

from src.agentes.agente_aleatorio import AgenteAleatorio
from src.agentes.agente_busqueda import AgenteBusquedaAEstrella
from src.agentes.heuristicas import HeuristicaCero, HeuristicaColoresPendientes
from src.dominio.estado_partida import EstadoPartida
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


RUTA_INSTANCIA_EJEMPLO = os.path.join(
    "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)


def test_la_heuristica_admisible_no_sobreestima_en_un_caso_conocido():
    """En un tablero 2x2 con dos fichas del mismo color, h coincide con h*."""
    contenido = "2 1\n2\n1 1\n1 2\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")
    estado = EstadoPartida(instancia)

    # Costo real optimo: colocar la primera ficha cuesta (4-1) - 0 = 3, y
    # colocar la segunda adyacente fusionando dos fichas cuesta (4-1) - 1 = 2.
    # Total 5, que es justo lo que la heuristica debe estimar.
    assert HeuristicaColoresPendientes().estimar(estado) == 5


def test_las_heuristicas_valen_cero_en_la_meta():
    """Sin fichas pendientes, toda estimacion debe ser nula."""
    contenido = "2 1\n1\n1 1\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")
    estado = EstadoPartida(instancia)
    estado.avanzar_ficha()

    assert HeuristicaColoresPendientes().estimar(estado) == 0
    assert HeuristicaCero().estimar(estado) == 0


def test_ambas_heuristicas_se_declaran_admisibles():
    """Las dos heuristicas implementadas nunca sobreestiman."""
    assert HeuristicaColoresPendientes().es_admisible is True
    assert HeuristicaCero().es_admisible is True


def test_la_heuristica_nula_convierte_a_estrella_en_dijkstra():
    """Con h = 0 la busqueda se ordena solo por el costo real acumulado."""
    contenido = "2 1\n2\n1 1\n1 2\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")
    estado = EstadoPartida(instancia)

    assert HeuristicaCero().estimar(estado) == 0


def test_a_estrella_resuelve_la_instancia_del_enunciado():
    """A* debe consumir la secuencia completa de la instancia de ejemplo."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    estado_inicial = EstadoPartida(instancia)

    agente = AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar")
    colocaciones = agente.planificar(estado_inicial, 10.0)

    assert len(colocaciones) == instancia.cantidad_fichas
    assert agente.esfuerzo_acumulado() > 0


def test_a_estrella_alcanza_el_optimo_del_enunciado(tmp_path):
    """
    En la instancia de ejemplo, A* debe dejar el tablero en tres celdas.

    El enunciado muestra esa cifra en su archivo de solucion de ejemplo, y la
    heuristica admisible garantiza que no existe una solucion mejor.
    """
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)

    resultado = EjecutorAgente().ejecutar(
        agente=AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar"),
        instancia=instancia,
        semilla=0,
        limite_tiempo_segundos=10.0,
        ruta_solucion=os.path.join(str(tmp_path), "busqueda.sol"),
    )

    assert resultado.metricas.fichas_colocadas == 6
    assert resultado.metricas.celdas_ocupadas == 3
    assert resultado.metricas.valor_ficha_mayor == 6
    assert resultado.colocaciones_rechazadas == 0


def test_a_estrella_supera_al_azar_en_celdas_ocupadas(tmp_path):
    """La busqueda informada debe dejar el tablero mas despejado que el azar."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    ejecutor = EjecutorAgente()

    resultado_busqueda = ejecutor.ejecutar(
        agente=AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar"),
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

    assert resultado_busqueda.metricas.celdas_ocupadas <= resultado_azar.metricas.celdas_ocupadas


def test_a_estrella_es_determinista():
    """Dos ejecuciones identicas deben producir la misma solucion."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)

    primera = AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar").planificar(
        EstadoPartida(instancia), 5.0
    )
    segunda = AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar").planificar(
        EstadoPartida(instancia), 5.0
    )

    assert primera == segunda


def test_a_estrella_entrega_solucion_con_el_tiempo_agotado():
    """Sin tiempo para buscar, el agente completa la partida de forma avida."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)

    agente = AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar")
    colocaciones = agente.planificar(EstadoPartida(instancia), 0.0001)

    assert len(colocaciones) == instancia.cantidad_fichas


def test_el_camino_producido_es_legal_segun_el_validador(tmp_path):
    """La solucion de A* debe pasar el validador independiente."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    ruta_salida = os.path.join(str(tmp_path), "busqueda.sol")

    EjecutorAgente().ejecutar(
        agente=AgenteBusquedaAEstrella(semilla=0, nombre="busqueda_astar"),
        instancia=instancia,
        semilla=0,
        limite_tiempo_segundos=10.0,
        ruta_solucion=ruta_salida,
    )

    solucion = LectorSolucion().leer_desde_archivo(ruta_salida)
    dictamen = Validador().validar(instancia, solucion)

    assert dictamen.es_legal is True
    assert dictamen.esta_completa is True