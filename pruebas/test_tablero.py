"""Pruebas unitarias de la estructura del tablero."""

from src.dominio.ficha import Ficha
from src.dominio.tablero import Tablero


def test_tablero_nuevo_esta_vacio():
    """Un tablero recien creado no tiene ninguna celda ocupada."""
    tablero = Tablero(4)

    assert tablero.cantidad_ocupadas == 0
    assert tablero.cantidad_vacias == 16
    assert tablero.esta_lleno() is False


def test_escribir_y_leer_ficha():
    """Una ficha escrita puede leerse con los mismos valores."""
    tablero = Tablero(3)
    tablero.escribir_ficha(1, 1, Ficha(color=2, valor=7))

    ficha_leida = tablero.obtener_ficha(1, 1)

    assert ficha_leida.color == 2
    assert ficha_leida.valor == 7
    assert tablero.cantidad_ocupadas == 1


def test_celdas_vacias_refleja_el_estado():
    """La lista de celdas vacias coincide con el conteo interno."""
    tablero = Tablero(3)
    tablero.escribir_ficha(0, 0, Ficha(color=1, valor=1))
    tablero.escribir_ficha(2, 2, Ficha(color=1, valor=1))

    celdas_libres = tablero.celdas_vacias()

    assert len(celdas_libres) == 7
    assert (0, 0) not in celdas_libres
    assert (2, 2) not in celdas_libres


def test_componente_conexa_ortogonal():
    """La componente conexa no incluye vecinos diagonales."""
    tablero = Tablero(3)
    tablero.escribir_ficha(0, 0, Ficha(color=1, valor=1))
    tablero.escribir_ficha(0, 1, Ficha(color=1, valor=1))
    tablero.escribir_ficha(1, 1, Ficha(color=1, valor=1))
    tablero.escribir_ficha(2, 2, Ficha(color=1, valor=1))

    componente = tablero.componente_conexa(0, 0)

    assert len(componente) == 3
    assert (2, 2) not in componente


def test_copiar_produce_tableros_independientes():
    """Modificar la copia no altera el tablero original."""
    tablero = Tablero(3)
    tablero.escribir_ficha(0, 0, Ficha(color=1, valor=5))

    copia = tablero.copiar()
    copia.vaciar_celda(0, 0)

    assert tablero.cantidad_ocupadas == 1
    assert copia.cantidad_ocupadas == 0