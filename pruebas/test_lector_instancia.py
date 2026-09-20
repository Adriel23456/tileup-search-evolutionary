"""Pruebas unitarias del lector del formato de instancia."""

import pytest

from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.lector_instancia import LectorInstancia


def test_lectura_del_ejemplo_del_enunciado():
    """El ejemplo del enunciado se interpreta correctamente."""
    contenido = (
        "# TileUp -- instancia de ejemplo\n"
        "4 3 # tablero 4x4, 3 colores\n"
        "6   # 6 fichas en la secuencia\n"
        "1 2\n"
        "2 1\n"
        "1 3\n"
        "3 1\n"
        "1 1\n"
        "2 4\n"
    )

    instancia = LectorInstancia().leer_desde_texto(contenido, "ejemplo")

    assert instancia.dimension == 4
    assert instancia.cantidad_colores == 3
    assert instancia.cantidad_fichas == 6
    assert instancia.obtener_ficha(0).color == 1
    assert instancia.obtener_ficha(5).valor == 4


def test_lineas_en_blanco_y_comentarios_se_ignoran():
    """Las lineas vacias y los comentarios no alteran la lectura."""
    contenido = (
        "\n"
        "# comentario suelto\n"
        "2 1\n"
        "\n"
        "1\n"
        "1 9   # ficha unica\n"
    )

    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")

    assert instancia.cantidad_fichas == 1
    assert instancia.obtener_ficha(0).valor == 9


def test_color_mayor_que_k_produce_error():
    """Un color fuera del rango 1..K se rechaza con un error controlado."""
    contenido = "3 2\n1\n5 1\n"

    with pytest.raises(ErrorFormatoInstancia):
        LectorInstancia().leer_desde_texto(contenido, "prueba")


def test_faltan_fichas_produce_error():
    """Declarar mas fichas de las presentes se rechaza."""
    contenido = "3 2\n4\n1 1\n2 1\n"

    with pytest.raises(ErrorFormatoInstancia):
        LectorInstancia().leer_desde_texto(contenido, "prueba")


def test_campo_no_entero_produce_error():
    """Un campo que no es entero se rechaza con un error legible."""
    contenido = "3 dos\n1\n1 1\n"

    with pytest.raises(ErrorFormatoInstancia):
        LectorInstancia().leer_desde_texto(contenido, "prueba")

def test_una_instancia_con_marca_de_orden_de_bytes_se_lee_igual():
    """
    Un archivo guardado por Windows como UTF-8 con BOM debe leerse bien.

    Notepad y muchas herramientas de Windows anteponen la marca de orden de
    bytes al guardar en UTF-8. Sin descartarla, el primer campo del archivo
    llega con un caracter invisible pegado y el lector lo rechaza.
    """
    contenido = "\ufeff4 3\n1\n1 2\n"

    instancia = LectorInstancia().leer_desde_texto(contenido, "prueba")

    assert instancia.dimension == 4
    assert instancia.cantidad_colores == 3
    assert instancia.cantidad_fichas == 1