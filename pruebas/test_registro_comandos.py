"""Pruebas del registro de subcomandos de la linea de comandos."""

import pytest

from src.cli.registro_comandos import (
    ErrorComandoDesconocido,
    RegistroComandos,
)


def test_todos_los_subcomandos_esperados_estan_registrados():
    """El programa debe exponer los seis subcomandos documentados."""
    nombres = RegistroComandos().nombres_disponibles()

    assert "resolver" in nombres
    assert "validar" in nombres
    assert "jugar" in nombres
    assert "instancia" in nombres
    assert "generar" in nombres
    assert "agentes" in nombres


def test_un_subcomando_desconocido_produce_error_controlado():
    """Solicitar un subcomando inexistente lanza un error legible."""
    with pytest.raises(ErrorComandoDesconocido):
        RegistroComandos().obtener("inexistente")


def test_cada_subcomando_declara_nombre_y_ayuda():
    """Todo subcomando debe identificarse y describirse."""
    for comando in RegistroComandos().todos():
        assert len(comando.nombre) > 0
        assert len(comando.ayuda) > 0