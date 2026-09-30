"""
Pruebas del nucleo del runner experimental.

Las primeras comprueban que se interpreta bien lo que imprime la CLI y que cada
situacion recibe la etiqueta de estado correcta. Las ultimas ejecutan corridas
reales de ambos agentes a traves de main.py y del validador.
"""

import hashlib
import os

import pytest

from experimentos import corrida
from experimentos.registro import (
    ErrorExperimentoExistente,
    RegistroExperimento,
    leer_crudo,
)


RUTA_INSTANCIA = os.path.join(
    corrida.RAIZ_REPOSITORIO, "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)

RUTA_BITACORA_HISTORICA = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos", "comparacion_agentes.csv"
)

SALIDA_BUSQUEDA_CORTADA = (
    "Nota: la busqueda se corto por tiempo o por nodos; la solucion se "
    "completo con la politica avida.\n"
    "agente=busqueda_astar instancia=ejemplo_n5_k3_m12 semilla=1 "
    "resultado=victoria colocadas=12/12 ocupadas=6 mayor=11 tiempo_s=8.5123 "
    "nodos_expandidos=68428\n"
    "solucion=C:\\x\\ejemplo.sol\n"
)

SALIDA_EVOLUTIVO = (
    "agente=evolutivo instancia=ejemplo_n5_k3_m12 semilla=7 resultado=victoria "
    "colocadas=12/12 ocupadas=3 mayor=12 tiempo_s=9.8004 "
    "evaluaciones_aptitud=29619\n"
    "solucion=/x/ejemplo.sol\n"
)

SALIDA_VALIDADOR_ACEPTADA = (
    "instancia=ejemplo_n5_k3_m12  (N=5, K=3, M=12)\n"
    "solucion=ejemplo\n"
    "veredicto=ACEPTADA\n"
    "colocadas=12/12 ocupadas=6 mayor=11 suma=39\n"
    "completitud=secuencia_consumida\n"
)


def salida(codigo=0, stdout="", abortado=False):
    """Auxiliar que fabrica la salida de un proceso."""
    return corrida.SalidaProceso(
        argumentos=[],
        codigo=codigo,
        stdout=stdout,
        stderr="",
        segundos_reloj=0.1,
        abortado=abortado,
    )


# ----------------------------------------------------------------------
# Interpretacion de la salida de la CLI
# ----------------------------------------------------------------------

def test_interpreta_la_salida_de_la_busqueda_cortada():
    """Se leen las metricas y el aviso de que A* no llego a la meta."""
    metricas = corrida.interpretar_resolver(SALIDA_BUSQUEDA_CORTADA)

    assert metricas.colocadas == 12
    assert metricas.total == 12
    assert metricas.ocupadas == 6
    assert metricas.mayor == 11
    assert metricas.tiempo_s == pytest.approx(8.5123)
    assert metricas.esfuerzo == 68428
    assert metricas.nombre_esfuerzo == "nodos_expandidos"
    assert metricas.corte_busqueda is True
    assert metricas.ruta_solucion == "C:\\x\\ejemplo.sol"


def test_interpreta_la_salida_del_evolutivo():
    """El evolutivo informa evaluaciones de aptitud y no emite el aviso."""
    metricas = corrida.interpretar_resolver(SALIDA_EVOLUTIVO)

    assert metricas.nombre_esfuerzo == "evaluaciones_aptitud"
    assert metricas.esfuerzo == 29619
    assert metricas.corte_busqueda is False


def test_una_salida_sin_metricas_no_se_interpreta():
    """Sin la linea de metricas no se inventa ningun valor."""
    assert corrida.interpretar_resolver("Instancia invalida: algo\n") is None


def test_interpreta_el_dictamen_del_validador():
    """Se leen veredicto, metricas verificadas y completitud."""
    dictamen = corrida.interpretar_validar(SALIDA_VALIDADOR_ACEPTADA)

    assert dictamen.veredicto == "ACEPTADA"
    assert dictamen.colocadas == 12
    assert dictamen.ocupadas == 6
    assert dictamen.mayor == 11
    assert dictamen.suma == 39
    assert dictamen.completa is True


# ----------------------------------------------------------------------
# Clasificacion del estado
# ----------------------------------------------------------------------

def test_clasificacion_de_cada_situacion():
    """Cada situacion recibe una etiqueta, y solo una."""
    metricas = corrida.interpretar_resolver(SALIDA_BUSQUEDA_CORTADA)
    aceptada = corrida.interpretar_validar(SALIDA_VALIDADOR_ACEPTADA)
    rechazada = corrida.interpretar_validar(
        SALIDA_VALIDADOR_ACEPTADA.replace("ACEPTADA", "RECHAZADA")
    )
    distinta = corrida.interpretar_validar(
        SALIDA_VALIDADOR_ACEPTADA.replace("ocupadas=6", "ocupadas=7")
    )

    clasificar = corrida.clasificar

    assert clasificar(salida(), metricas, salida(0), aceptada) == "ok"
    assert clasificar(salida(), metricas, salida(1), rechazada) == "rejected"
    assert clasificar(salida(), metricas, salida(0), distinta) == "mismatch"
    assert clasificar(salida(abortado=True, codigo=None), None, None, None) == "killed"
    assert clasificar(salida(codigo=2), None, None, None) == "agent_error"
    assert clasificar(salida(), metricas, salida(2), None) == "validator_error"
    # Codigo de salida y veredicto contradictorios: el fallo es del validador.
    assert clasificar(salida(), metricas, salida(1), aceptada) == "validator_error"


# ----------------------------------------------------------------------
# Persistencia
# ----------------------------------------------------------------------

def test_el_registro_no_sobrescribe_un_crudo_existente(tmp_path):
    """Un CSV crudo es un resultado: reemplazarlo exige pedirlo."""
    directorio = str(tmp_path / "experimento")
    RegistroExperimento(directorio, ["a", "b"])

    with pytest.raises(ErrorExperimentoExistente):
        RegistroExperimento(directorio, ["a", "b"])

    RegistroExperimento(directorio, ["a", "b"], sobrescribir=True)


# ----------------------------------------------------------------------
# Corridas reales a traves de main.py
# ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "agente, tipo_esfuerzo, corte_esperado",
    [
        ("busqueda_astar", "expanded_nodes", "False"),
        ("evolutivo", "fitness_evaluations", ""),
    ],
)
def test_una_corrida_real_queda_validada_y_registrada(
        tmp_path, agente, tipo_esfuerzo, corte_esperado):
    """
    Una corrida completa pasa por resolver y por el validador independiente,
    y deja una fila coherente sin tocar la bitacora historica.
    """
    with open(RUTA_BITACORA_HISTORICA, "rb") as archivo:
        huella_antes = hashlib.sha256(archivo.read()).hexdigest()

    ruta_solucion = str(tmp_path / "soluciones" / (agente + ".sol"))

    fila, detalle = corrida.ejecutar_corrida(
        experimento="prueba",
        config_id="ejemplo",
        ruta_instancia=RUTA_INSTANCIA,
        nombre_instancia="ejemplo_n4_k3_m6",
        n=4,
        k=3,
        m=6,
        instance_seed=None,
        agente=agente,
        agent_seed=1,
        timeout_s=0.5,
        ruta_solucion=ruta_solucion,
        run_id="prueba-0001",
    )

    registro = RegistroExperimento(str(tmp_path / "res"), corrida.COLUMNAS_CRUDO)
    registro.agregar(fila, detalle)
    filas = leer_crudo(registro.ruta_crudo)

    with open(RUTA_BITACORA_HISTORICA, "rb") as archivo:
        huella_despues = hashlib.sha256(archivo.read()).hexdigest()

    assert fila["status"] == "ok"
    assert fila["validated"] == "True"
    assert fila["tiles_placed"] == "6"
    assert fila["complete"] == "True"
    assert fila["tiles_placed"] == fila["validator_tiles"]
    assert fila["occupied_cells"] == fila["validator_occupied"]
    assert fila["effort_type"] == tipo_esfuerzo
    assert int(fila["effort"]) > 0
    assert fila["search_cutoff"] == corte_esperado
    assert fila["exceeded_limit"] == "False"
    assert fila["instance_seed"] == ""
    assert len(fila["solution_sha256"]) == 64
    assert detalle["validar"]["codigo"] == 0
    assert filas == [fila]
    assert huella_despues == huella_antes


def test_una_instancia_inexistente_queda_como_error_del_agente(tmp_path):
    """Un fallo de entrada no detiene nada: se registra con su estado."""
    fila, detalle = corrida.ejecutar_corrida(
        experimento="prueba",
        config_id="inexistente",
        ruta_instancia=str(tmp_path / "no_existe.txt"),
        nombre_instancia="no_existe",
        n=4,
        k=3,
        m=6,
        instance_seed=1,
        agente="evolutivo",
        agent_seed=1,
        timeout_s=0.5,
        ruta_solucion=str(tmp_path / "no_existe.sol"),
        run_id="prueba-0002",
    )

    assert fila["status"] == "agent_error"
    assert fila["return_code"] == "2"
    assert fila["tiles_placed"] == ""
    assert fila["validated"] == ""
    assert detalle["validar"] is None
