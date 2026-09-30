"""
Pruebas de la bitacora opcional de resolver.

Resolver lee la instancia, ejecuta el agente, escribe la solucion e informa
las metricas por salida estandar. Escribir ademas un CSV es opcional: solo
ocurre si se indica --bitacora. Estas pruebas corren con el directorio de
trabajo en una carpeta temporal, para detectar cualquier escritura relativa.
"""

import csv
import hashlib
import os

from src.cli.ejecutor_consola import EjecutorConsola
from src.cli.registro_comandos import RegistroComandos


RAIZ_REPOSITORIO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_INSTANCIA = os.path.join(
    RAIZ_REPOSITORIO, "datos", "instancias", "ejemplo_n4_k3_m6.txt"
)

RUTA_BITACORA_HISTORICA = os.path.join(
    RAIZ_REPOSITORIO, "resultados", "experimentos", "comparacion_agentes.csv"
)


def huella(ruta):
    """Auxiliar que devuelve el hash del archivo, o None si no existe."""
    if os.path.isfile(ruta) is False:
        return None

    with open(ruta, "rb") as archivo:
        return hashlib.sha256(archivo.read()).hexdigest()


def resolver(tmp_path, ruta_bitacora=None):
    """Auxiliar que resuelve la instancia de ejemplo con un agente rapido."""
    return EjecutorConsola().ejecutar_agente(
        ruta_instancia=RUTA_INSTANCIA,
        nombre_agente="aleatorio",
        semilla=0,
        limite_tiempo_segundos=1.0,
        ruta_salida=str(tmp_path / "solucion.sol"),
        silencioso=True,
        ruta_bitacora=ruta_bitacora,
    )


def test_arrancar_la_cli_no_crea_ningun_archivo(tmp_path, monkeypatch):
    """
    Construir los subcomandos, que es lo que hace main.py en cada invocacion,
    no debe escribir nada en el directorio de trabajo.
    """
    monkeypatch.chdir(tmp_path)

    RegistroComandos()

    assert os.listdir(str(tmp_path)) == []


def test_resolver_sin_bitacora_no_escribe_ningun_csv(tmp_path, monkeypatch):
    """Sin --bitacora solo aparece la solucion, y el CSV historico no cambia."""
    monkeypatch.chdir(tmp_path)
    huella_antes = huella(RUTA_BITACORA_HISTORICA)

    codigo = resolver(tmp_path)

    assert codigo == 0
    assert os.listdir(str(tmp_path)) == ["solucion.sol"]
    assert huella(RUTA_BITACORA_HISTORICA) == huella_antes


def test_resolver_con_bitacora_agrega_exactamente_una_fila(tmp_path, monkeypatch):
    """Con --bitacora se crea el CSV pedido, con su encabezado y una fila."""
    monkeypatch.chdir(tmp_path)
    ruta_bitacora = str(tmp_path / "bitacora.csv")

    codigo = resolver(tmp_path, ruta_bitacora=ruta_bitacora)

    with open(ruta_bitacora, "r", encoding="utf-8", newline="") as archivo:
        filas = list(csv.reader(archivo))

    assert codigo == 0
    assert filas[0][0] == "agente"
    assert len(filas) == 2
    assert filas[1][0] == "aleatorio"
    assert filas[1][1] == "ejemplo_n4_k3_m6"
