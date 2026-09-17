"""Pruebas unitarias de las reglas del juego."""

import pytest

from src.dominio.estado_partida import EstadoPartida
from src.dominio.ficha import Ficha
from src.dominio.motor import (
    ErrorColocacionIlegal,
    EstadoTerminacion,
    MotorTileUp,
)
from src.instancias.instancia import Instancia


def construir_estado(dimension, cantidad_colores, fichas):
    """Auxiliar que arma un estado inicial a partir de una lista de fichas."""
    instancia = Instancia(
        dimension=dimension,
        cantidad_colores=cantidad_colores,
        fichas=fichas,
        nombre="prueba",
    )
    return EstadoPartida(instancia)


def test_colocacion_sin_fusion():
    """Una ficha aislada permanece donde fue colocada."""
    estado = construir_estado(3, 2, [Ficha(1, 4)])
    motor = MotorTileUp()

    resultado = motor.colocar(estado, 1, 1)

    assert resultado.hubo_fusion is False
    assert resultado.tamano_componente == 1
    assert estado.tablero.cantidad_ocupadas == 1
    assert estado.tablero.obtener_ficha(1, 1).valor == 4


def test_fusion_de_dos_fichas():
    """Dos fichas adyacentes del mismo color se fusionan en una sola."""
    estado = construir_estado(3, 2, [Ficha(1, 2), Ficha(1, 3)])
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)
    resultado = motor.colocar(estado, 0, 1)

    assert resultado.hubo_fusion is True
    assert resultado.tamano_componente == 2
    assert resultado.valor_resultante == 5
    assert estado.tablero.cantidad_ocupadas == 1
    assert estado.tablero.obtener_ficha(0, 1).valor == 5
    assert estado.tablero.esta_vacia(0, 0) is True


def test_fusion_de_componente_de_tres_o_mas():
    """Una componente de tres fichas se colapsa en la celda colocada."""
    fichas = [Ficha(1, 1), Ficha(1, 2), Ficha(1, 4)]
    estado = construir_estado(3, 2, fichas)
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)
    motor.colocar(estado, 0, 2)
    resultado = motor.colocar(estado, 0, 1)

    assert resultado.hubo_fusion is True
    assert resultado.tamano_componente == 3
    assert resultado.valor_resultante == 7
    assert estado.tablero.cantidad_ocupadas == 1
    assert estado.tablero.obtener_ficha(0, 1).valor == 7


def test_la_fusion_conserva_la_suma_total():
    """La suma de valores del tablero no depende de las decisiones tomadas."""
    fichas = [Ficha(1, 3), Ficha(1, 5), Ficha(2, 2)]
    estado = construir_estado(3, 2, fichas)
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)
    motor.colocar(estado, 0, 1)
    motor.colocar(estado, 2, 2)

    assert estado.tablero.suma_total_valores() == 10


def test_deteccion_de_victoria():
    """La partida se gana al consumir toda la secuencia."""
    estado = construir_estado(2, 1, [Ficha(1, 1)])
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)

    assert motor.evaluar_terminacion(estado) == EstadoTerminacion.VICTORIA
    assert motor.es_meta(estado) is True


def test_deteccion_de_derrota():
    """La partida se pierde si el tablero se llena con fichas pendientes."""
    fichas = [Ficha(1, 1), Ficha(2, 1)]
    estado = construir_estado(1, 2, fichas)
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)

    assert motor.evaluar_terminacion(estado) == EstadoTerminacion.DERROTA


def test_colocacion_en_celda_ocupada_es_ilegal():
    """El motor rechaza colocar sobre una celda que ya tiene ficha."""
    fichas = [Ficha(1, 1), Ficha(2, 1)]
    estado = construir_estado(2, 2, fichas)
    motor = MotorTileUp()

    motor.colocar(estado, 0, 0)

    with pytest.raises(ErrorColocacionIlegal):
        motor.colocar(estado, 0, 0)


def test_acciones_legales_igualan_las_celdas_vacias():
    """El factor de ramificacion es exactamente la cantidad de celdas vacias."""
    fichas = [Ficha(1, 1), Ficha(2, 1)]
    estado = construir_estado(3, 2, fichas)
    motor = MotorTileUp()

    motor.colocar(estado, 1, 1)

    assert len(motor.acciones_legales(estado)) == 8