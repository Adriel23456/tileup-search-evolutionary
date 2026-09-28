"""
Pruebas del generador de instancias.

Cubren las propiedades que la Etapa A promete: el formato es el oficial, la
semilla determina el resultado por completo, y la instancia se puede ganar.
"""

import pytest

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import MotorTileUp
from src.instancias.errores import ErrorParametrosGenerador
from src.instancias.escritor_instancia import EscritorInstancia
from src.instancias.generador_instancia import GeneradorInstancias
from src.instancias.lector_instancia import LectorInstancia
from src.nombrado import nombres_archivos


def generar(dimension=4, cantidad_colores=3, cantidad_fichas=20, semilla=1):
    """Auxiliar que invoca al generador con valores comodos por defecto."""
    return GeneradorInstancias().generar(
        dimension=dimension,
        cantidad_colores=cantidad_colores,
        cantidad_fichas=cantidad_fichas,
        semilla=semilla,
        nombre="prueba",
    )


def texto_de(generada, semilla):
    """Auxiliar que produce el archivo de una instancia ya generada."""
    return EscritorInstancia().generar_texto(generada.instancia, semilla)


def secuencia_de(instancia):
    """Auxiliar que extrae la secuencia como lista de pares (color, valor)."""
    return [
        (instancia.obtener_ficha(posicion).color,
         instancia.obtener_ficha(posicion).valor)
        for posicion in range(instancia.cantidad_fichas)
    ]


# ----------------------------------------------------------------------
# 1. Determinismo
# ----------------------------------------------------------------------

def test_la_misma_semilla_produce_el_mismo_archivo():
    """Dos corridas con los mismos N, K, M y semilla son indistinguibles."""
    primera = generar(semilla=7)
    segunda = generar(semilla=7)

    assert secuencia_de(primera.instancia) == secuencia_de(segunda.instancia)
    assert primera.colocaciones == segunda.colocaciones
    assert texto_de(primera, 7) == texto_de(segunda, 7)


def test_la_semilla_influye_en_el_resultado():
    """
    Comprueba que la semilla se use, con dos valores concretos.

    Es una prueba de cordura, no una garantia: nada obliga a que dos semillas
    cualesquiera den instancias distintas, y de hecho con M muy pequeno es
    normal que coincidan. Lo unico que el enunciado exige, y lo que la prueba
    anterior comprueba, es la direccion contraria: misma configuracion y misma
    semilla producen exactamente el mismo archivo. Esta prueba existe solo
    porque un generador que ignorara la semilla por completo pasaria aquella.
    """
    assert texto_de(generar(semilla=1), 1) != texto_de(generar(semilla=2), 2)


# ----------------------------------------------------------------------
# 2, 3 y 4. Forma de la secuencia
# ----------------------------------------------------------------------

def test_la_instancia_tiene_exactamente_m_fichas():
    """La secuencia mide justo lo que se pidio, ni una ficha mas ni menos."""
    for cantidad_fichas in [0, 1, 7, 20, 40]:
        generada = generar(cantidad_fichas=cantidad_fichas)
        assert generada.instancia.cantidad_fichas == cantidad_fichas
        assert len(generada.colocaciones) == cantidad_fichas


def test_todos_los_colores_caen_en_el_rango_uno_a_k():
    """Ningun color se sale de 1..K, que es lo que el formato admite."""
    generada = generar(dimension=5, cantidad_colores=4, cantidad_fichas=30)

    for color, _valor in secuencia_de(generada.instancia):
        assert 1 <= color <= 4


def test_todos_los_valores_son_enteros_positivos():
    """El enunciado exige que el valor de una ficha sea un entero positivo."""
    generada = generar(dimension=5, cantidad_colores=4, cantidad_fichas=30)

    for _color, valor in secuencia_de(generada.instancia):
        assert isinstance(valor, int)
        assert valor >= 1


# ----------------------------------------------------------------------
# 5. El parser vigente acepta lo generado
# ----------------------------------------------------------------------

def test_el_lector_actual_reconstruye_la_instancia_generada():
    """El archivo escrito se relee y devuelve exactamente lo mismo."""
    generada = generar(dimension=5, cantidad_colores=3, cantidad_fichas=18, semilla=4)
    contenido = texto_de(generada, 4)

    releida = LectorInstancia().leer_desde_texto(contenido, "prueba")

    assert releida.dimension == generada.instancia.dimension
    assert releida.cantidad_colores == generada.instancia.cantidad_colores
    assert releida.cantidad_fichas == generada.instancia.cantidad_fichas
    assert secuencia_de(releida) == secuencia_de(generada.instancia)


def test_el_archivo_escrito_en_disco_se_lee_igual(tmp_path):
    """La ida y vuelta completa por disco tampoco pierde nada."""
    generada = generar(semilla=3)
    ruta = tmp_path / "subcarpeta" / "generada.txt"

    EscritorInstancia().escribir(str(ruta), generada.instancia, semilla=3)
    releida = LectorInstancia().leer_desde_archivo(str(ruta))

    assert secuencia_de(releida) == secuencia_de(generada.instancia)


def test_dos_escrituras_con_la_misma_semilla_dan_el_mismo_archivo(tmp_path):
    """El criterio de SiguientesPasos: mismo archivo byte a byte."""
    escritor = EscritorInstancia()
    primera = tmp_path / "primera.txt"
    segunda = tmp_path / "segunda.txt"

    escritor.escribir(str(primera), generar(semilla=5).instancia, semilla=5)
    escritor.escribir(str(segunda), generar(semilla=5).instancia, semilla=5)

    assert primera.read_bytes() == segunda.read_bytes()


# ----------------------------------------------------------------------
# Nombrado automatico
# ----------------------------------------------------------------------

def test_el_nombre_automatico_separa_las_semillas():
    """
    Dos semillas de una misma configuracion no pueden compartir archivo.

    Es lo que permite correr la bateria de la Etapa C sin que cada semilla
    sobreescriba a la anterior.
    """
    primera = nombres_archivos.ruta_instancia("gen", 1, 4, 3, 20)
    segunda = nombres_archivos.ruta_instancia("gen", 2, 4, 3, 20)

    assert primera.endswith("gen_s1_n4_k3_m20.txt")
    assert segunda.endswith("gen_s2_n4_k3_m20.txt")
    assert primera != segunda


# ----------------------------------------------------------------------
# 6. La instancia tiene al menos una solucion conocida
# ----------------------------------------------------------------------

def reproducir_el_testigo(generada):
    """
    Juega la partida testigo sobre un tablero limpio usando el motor.

    Devuelve el estado final. Si alguna colocacion fuera ilegal, el motor
    lanzaria ErrorColocacionIlegal y la prueba fallaria sola.
    """
    motor = MotorTileUp()
    estado = EstadoPartida(generada.instancia)

    for fila, columna in generada.colocaciones:
        motor.colocar(estado, fila, columna)

    return estado


def test_el_testigo_gana_la_partida_en_un_caso_holgado():
    """Con M menor que N al cuadrado la partida testigo consume la secuencia."""
    generada = generar(dimension=4, cantidad_colores=3, cantidad_fichas=10, semilla=2)
    estado = reproducir_el_testigo(generada)

    assert estado.cantidad_colocadas == 10
    assert MotorTileUp().es_meta(estado) is True


def test_el_testigo_gana_la_partida_cuando_m_supera_las_celdas():
    """
    El caso que de verdad importa: M muy por encima de N al cuadrado.

    Un tablero 3x3 tiene nueve celdas y aqui se colocan treinta fichas, de modo
    que la partida solo se puede terminar si hay fusiones. Es el regimen donde
    una secuencia puramente aleatoria seria imposible y donde se comprueba que
    el procedimiento constructivo cumple lo que promete.
    """
    generada = generar(dimension=3, cantidad_colores=3, cantidad_fichas=30, semilla=11)
    estado = reproducir_el_testigo(generada)

    assert estado.cantidad_colocadas == 30
    assert MotorTileUp().es_meta(estado) is True


def test_el_testigo_gana_con_varias_configuraciones_y_semillas():
    """
    Barrido corto sobre el tipo de configuraciones que usara la Etapa C.

    No es una bateria experimental: solo comprueba que la garantia no depende
    de haber elegido con cuidado N, K, M o la semilla.
    """
    motor = MotorTileUp()

    for dimension in [2, 3, 5]:
        for cantidad_colores in [1, 2, 4]:
            for semilla in [0, 13]:
                cantidad_fichas = dimension * dimension * 2

                generada = generar(
                    dimension=dimension,
                    cantidad_colores=cantidad_colores,
                    cantidad_fichas=cantidad_fichas,
                    semilla=semilla,
                )
                estado = reproducir_el_testigo(generada)

                assert motor.es_meta(estado) is True


# ----------------------------------------------------------------------
# 7. Parametros invalidos
# ----------------------------------------------------------------------

def test_parametros_invalidos_producen_un_error_controlado():
    """N, K y M fuera de rango se rechazan antes de generar nada."""
    casos_invalidos = [
        (0, 3, 5),    # N debe ser mayor o igual a 1
        (-2, 3, 5),   # N negativo
        (4, 0, 5),    # K debe ser mayor o igual a 1
        (4, 3, -1),   # M no puede ser negativo
    ]

    for dimension, cantidad_colores, cantidad_fichas in casos_invalidos:
        with pytest.raises(ErrorParametrosGenerador):
            generar(
                dimension=dimension,
                cantidad_colores=cantidad_colores,
                cantidad_fichas=cantidad_fichas,
            )


def test_un_tablero_de_una_celda_no_admite_mas_de_una_ficha():
    """
    Con N=1 la unica celda no tiene vecinos y nunca puede haber fusion.

    Pedir dos o mas fichas describe una partida imposible, asi que el generador
    lo rechaza en lugar de entregar una instancia que nadie puede ganar.
    """
    with pytest.raises(ErrorParametrosGenerador):
        generar(dimension=1, cantidad_colores=2, cantidad_fichas=5)

    # El caso que si cabe se genera sin problema.
    generada = generar(dimension=1, cantidad_colores=2, cantidad_fichas=1)
    assert MotorTileUp().es_meta(reproducir_el_testigo(generada)) is True
