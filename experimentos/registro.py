"""
Persistencia de un experimento: CSV crudo, registros y metadatos.

Cada experimento vive en su propio directorio de resultados:

  crudo.csv         Una fila por corrida. Es la fuente primaria de verdad.
  registros.jsonl   Comandos, stdout y stderr completos de cada corrida,
                    enlazados por run_id. Evidencia auxiliar.
  metadatos.json    Commit, maquina, Python y configuracion usada.

Las filas se escriben a medida que terminan las corridas, de modo que una
interrupcion no pierde lo que ya se ejecuto.
"""

import csv
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
from typing import Dict, List

from experimentos.corrida import RAIZ_REPOSITORIO


NOMBRE_CRUDO = "crudo.csv"
NOMBRE_REGISTROS = "registros.jsonl"
NOMBRE_METADATOS = "metadatos.json"


class ErrorExperimentoExistente(Exception):
    """Se lanza al intentar sobrescribir un CSV crudo sin pedirlo."""


class RegistroExperimento:
    """Escribe el CSV crudo y los registros de un experimento."""

    def __init__(self, directorio: str, columnas: List[str],
                 sobrescribir: bool = False) -> None:
        """
        Prepara el directorio del experimento.

        Un CSV crudo existente es un resultado, posiblemente versionado, asi
        que no se reemplaza salvo que se pida de forma explicita.
        """
        self.directorio = directorio
        self.columnas = list(columnas)
        self.ruta_crudo = os.path.join(directorio, NOMBRE_CRUDO)
        self.ruta_registros = os.path.join(directorio, NOMBRE_REGISTROS)
        self.ruta_metadatos = os.path.join(directorio, NOMBRE_METADATOS)

        if os.path.isfile(self.ruta_crudo) is True and sobrescribir is False:
            raise ErrorExperimentoExistente(
                "Ya existe " + self.ruta_crudo + ". Use --sobrescribir para "
                "reemplazarlo."
            )

        os.makedirs(directorio, exist_ok=True)

        with open(self.ruta_crudo, "w", encoding="utf-8", newline="") as archivo:
            csv.writer(archivo).writerow(self.columnas)

        with open(self.ruta_registros, "w", encoding="utf-8", newline="\n"):
            pass

    def agregar(self, fila: Dict[str, str], detalle: Dict) -> None:
        """Agrega una corrida al CSV crudo y su detalle a los registros."""
        with open(self.ruta_crudo, "a", encoding="utf-8", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self.columnas)
            escritor.writerow(fila)

        with open(self.ruta_registros, "a", encoding="utf-8", newline="\n") as archivo:
            archivo.write(json.dumps(detalle, ensure_ascii=False) + "\n")

    def escribir_metadatos(self, metadatos: Dict) -> None:
        """Escribe los metadatos del experimento."""
        with open(self.ruta_metadatos, "w", encoding="utf-8", newline="\n") as archivo:
            json.dump(metadatos, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")


def leer_crudo(ruta_crudo: str) -> List[Dict[str, str]]:
    """Lee un CSV crudo como lista de filas."""
    with open(ruta_crudo, "r", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def metadatos_del_entorno() -> Dict:
    """
    Reune lo necesario para saber donde y con que codigo se obtuvo un
    resultado: los tiempos dependen de la maquina, y las soluciones del commit.
    """
    return {
        "commit": _git(["rev-parse", "HEAD"]),
        "cambios_sin_confirmar": _git(["status", "--porcelain"]) != "",
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "procesador": platform.processor(),
        "nucleos_logicos": os.cpu_count(),
        "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def huella_de_configuracion(ruta_configuracion: str) -> str:
    """Devuelve el SHA-256 del archivo de configuracion usado."""
    with open(ruta_configuracion, "rb") as archivo:
        return hashlib.sha256(archivo.read()).hexdigest()


def _git(argumentos: List[str]) -> str:
    """Consulta git en la raiz del repositorio; vacio si no esta disponible."""
    try:
        proceso = subprocess.run(
            ["git"] + argumentos,
            cwd=RAIZ_REPOSITORIO,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    if proceso.returncode != 0:
        return ""

    return proceso.stdout.strip()
