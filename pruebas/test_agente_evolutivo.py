"""Pruebas del agente evolutivo de estado estacionario."""

import os

from src.agentes.agente_evolutivo import AgenteEvolutivo
from src.agentes.registro_agentes import RegistroAgentes
from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import MotorTileUp
from src.instancias.lector_instancia import LectorInstancia
from src.partidas.ejecutor_agente import EjecutorAgente
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


RUTA_INSTANCIA_EJEMPLO = os.path.join(
    "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)


def test_el_agente_evolutivo_esta_registrado():
    """La CLI debe poder construir el agente por su nombre público."""
    registro = RegistroAgentes()

    assert "evolutivo" in registro.nombres_disponibles()
    assert registro.construir("evolutivo", semilla=7).nombre == "evolutivo"


def test_la_evaluacion_cuenta_todas_las_reparaciones_virtuales():
    """Una coordenada ocupada se penaliza sin modificar el cromosoma."""
    contenido = "3 4\n4\n1 1\n2 1\n3 1\n4 1\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "reparaciones")
    estado = EstadoPartida(instancia)
    genes = ((0, 0), (0, 0), (0, 0), (0, 0))
    agente = AgenteEvolutivo(semilla=0)

    evaluacion = agente._evaluar(estado, genes, ())

    assert evaluacion.genes == genes
    assert evaluacion.reparaciones_necesarias == 3
    assert evaluacion.indices_reparacion == (1, 2, 3)
    assert evaluacion.fichas_colocadas == 4
    assert len(set(evaluacion.colocaciones_simuladas)) == 4


def test_la_heuristica_prefiere_una_fusion_y_desempata_por_coordenada():
    """La reparación virtual es determinista y favorece fusionar."""
    contenido = "3 1\n2\n1 1\n1 1\n"
    instancia = LectorInstancia().leer_desde_texto(contenido, "heuristica")
    estado = EstadoPartida(instancia)
    motor = MotorTileUp()
    motor.colocar(estado, 1, 1)
    agente = AgenteEvolutivo(semilla=999)

    celda = agente._elegir_celda_guiada(
        estado=estado,
        referencia=(0, 0),
        exigir_cambio=False,
    )

    assert celda == (0, 1)


def test_la_cantidad_de_mutaciones_incluye_cero_uno_dos_y_tres():
    """El sorteo uniforme usa las cuatro cantidades acordadas."""
    agente = AgenteEvolutivo(semilla=21)

    cantidades = {
        agente._cantidad_de_mutaciones(longitud=10)
        for _ in range(100)
    }

    assert cantidades == {0, 1, 2, 3}


def test_la_evaluacion_es_reproducible_sin_depender_del_reloj():
    """El mismo cromosoma tiene siempre la misma evaluación."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    estado = EstadoPartida(instancia)
    genes = ((0, 0), (0, 0), (3, 3), (3, 3), (1, 1), (1, 1))

    primera = AgenteEvolutivo(semilla=1)._evaluar(estado, genes, ())
    segunda = AgenteEvolutivo(semilla=999)._evaluar(estado, genes, ())

    assert primera == segunda


def test_el_agente_produce_una_solucion_aceptada_por_el_validador(tmp_path):
    """La solución elegida nunca contiene reparaciones virtuales."""
    instancia = LectorInstancia().leer_desde_archivo(RUTA_INSTANCIA_EJEMPLO)
    ruta_salida = os.path.join(str(tmp_path), "evolutivo.sol")
    agente = AgenteEvolutivo(semilla=7)

    resultado = EjecutorAgente().ejecutar(
        agente=agente,
        instancia=instancia,
        semilla=7,
        limite_tiempo_segundos=0.1,
        ruta_solucion=ruta_salida,
    )

    solucion = LectorSolucion().leer_desde_archivo(ruta_salida)
    dictamen = Validador().validar(instancia, solucion)

    assert resultado.colocaciones_rechazadas == 0
    assert resultado.metricas.nombre_esfuerzo == "evaluaciones_aptitud"
    assert resultado.metricas.esfuerzo_algoritmo > 0
    assert dictamen.es_legal is True
    assert dictamen.esta_completa is True
