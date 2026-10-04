"""Pruebas del punto de entrada principal."""

import main


def test_ayuda_completa_devuelve_codigo_de_exito():
    """--ayuda-completa muestra la ayuda y termina con exito."""
    assert main.main(["--ayuda-completa"]) == 0


def test_falta_subcomando_devuelve_error_de_entrada():
    """Invocar sin subcomando muestra la ayuda general como error."""
    assert main.main([]) == 2
