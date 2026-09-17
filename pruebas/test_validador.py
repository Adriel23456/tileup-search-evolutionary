"""Pruebas del validador independiente."""

import pytest

from src.instancias.lector_instancia import LectorInstancia
from src.validacion.errores import ErrorFormatoSolucion
from src.validacion.lector_solucion import LectorSolucion
from src.validacion.validador import Validador


# Instancia minima usada por la mayoria de las pruebas: tablero 2x2, dos
# colores, tres fichas donde las dos primeras pueden fusionarse.
CONTENIDO_INSTANCIA = "2 2\n3\n1 1\n1 2\n2 5\n"


def construir_instancia():
    """Auxiliar que arma la instancia de prueba."""
    return LectorInstancia().leer_desde_texto(CONTENIDO_INSTANCIA, "prueba")


def validar_texto(contenido_solucion: str):
    """Auxiliar que valida una solucion dada como texto."""
    instancia = construir_instancia()
    solucion = LectorSolucion().leer_desde_texto(contenido_solucion, "prueba")
    return Validador().validar(instancia, solucion)


def test_acepta_una_solucion_legal_y_completa():
    """Una partida legal que consume la secuencia se acepta."""
    contenido = (
        "0 0 0\n"
        "1 0 1\n"
        "2 1 0\n"
        "# colocadas=3 ocupadas=2 mayor=5\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is True
    assert dictamen.esta_completa is True
    assert dictamen.fichas_colocadas == 3
    assert dictamen.celdas_ocupadas == 2
    assert dictamen.valor_ficha_mayor == 5


def test_rechaza_colocacion_sobre_celda_ocupada():
    """Colocar dos fichas en la misma celda es ilegal."""
    contenido = (
        "0 0 0\n"
        "1 0 0\n"
        "# colocadas=2 ocupadas=1 mayor=3\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is False


def test_rechaza_coordenada_fuera_del_tablero():
    """Una coordenada fuera de rango es ilegal."""
    contenido = (
        "0 5 5\n"
        "# colocadas=1 ocupadas=1 mayor=1\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is False


def test_rechaza_indices_fuera_de_orden():
    """Las fichas deben consumirse en orden estricto desde cero."""
    contenido = (
        "1 0 0\n"
        "0 0 1\n"
        "# colocadas=2 ocupadas=2 mayor=2\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is False


def test_rechaza_resumen_que_no_coincide():
    """Un resumen declarado que no coincide con lo verificado se rechaza."""
    contenido = (
        "0 0 0\n"
        "1 0 1\n"
        "2 1 0\n"
        "# colocadas=3 ocupadas=99 mayor=5\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is False


def test_acepta_solucion_parcial_pero_la_marca_incompleta():
    """Una derrota legal se acepta, pero se informa que quedo incompleta."""
    contenido = (
        "0 0 0\n"
        "# colocadas=1 ocupadas=1 mayor=1\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is True
    assert dictamen.esta_completa is False
    assert dictamen.fichas_colocadas == 1


def test_verifica_la_fusion_de_dos_fichas():
    """La fusion suma los valores y libera una celda."""
    contenido = (
        "0 0 0\n"
        "1 0 1\n"
        "# colocadas=2 ocupadas=1 mayor=3\n"
    )

    dictamen = validar_texto(contenido)

    assert dictamen.es_legal is True
    assert dictamen.celdas_ocupadas == 1
    assert dictamen.valor_ficha_mayor == 3


def test_linea_mal_formada_produce_error_controlado():
    """Una linea con dos campos en lugar de tres se rechaza con error."""
    with pytest.raises(ErrorFormatoSolucion):
        LectorSolucion().leer_desde_texto("0 0\n", "prueba")