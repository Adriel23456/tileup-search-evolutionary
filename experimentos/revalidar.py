"""
Revalidacion de una bateria sin volver a ejecutar los agentes.

Recorre todas las soluciones listadas en resultados/experimentos/<experimento>/
crudo.csv y las somete de nuevo al validador independiente (main.py validar).
Para cada una comprueba:

  - que el archivo de solucion no cambio desde la corrida (SHA-256);
  - que la solucion es legal;
  - que colocadas, ocupadas y ficha mayor verificadas coinciden con las que el
    agente informo en su corrida.

Sirve para que cualquiera pueda comprobar los resultados versionados del
informe con el validador, como exige el enunciado.

Uso, desde la raiz del repositorio:
    python -m experimentos.revalidar comparacion
    python -m experimentos.revalidar escalabilidad
"""

import argparse
import os
import sys
from typing import Dict, List, Optional

from experimentos import corrida
from experimentos.registro import leer_crudo
from src.nombrado import nombres_archivos


DIRECTORIO_RESULTADOS = os.path.join(
    corrida.RAIZ_REPOSITORIO, "resultados", "experimentos"
)


def revalidar_fila(fila: Dict[str, str], raiz_datos: str) -> List[str]:
    """
    Revalida la solucion de una corrida.

    Devuelve la lista de discrepancias encontradas; vacia si todo coincide.
    """
    ruta_solucion = os.path.join(raiz_datos, fila["solution_path"])
    ruta_instancia = os.path.join(
        raiz_datos,
        nombres_archivos.DIRECTORIO_INSTANCIAS,
        fila["instance"] + nombres_archivos.EXTENSION_INSTANCIA,
    )

    if os.path.isfile(ruta_solucion) is False:
        return ["no existe la solucion " + fila["solution_path"]]

    if os.path.isfile(ruta_instancia) is False:
        return ["no existe la instancia " + fila["instance"]]

    problemas: List[str] = []

    if corrida.huella_archivo(ruta_solucion) != fila["solution_sha256"]:
        problemas.append("la solucion cambio desde la corrida (SHA-256 distinto)")

    salida = corrida.ejecutar_main(
        ["validar", "--instancia", ruta_instancia, "--solucion", ruta_solucion],
        corrida.TIMEOUT_VALIDADOR_S,
    )
    dictamen = corrida.interpretar_validar(salida.stdout)

    if dictamen is None:
        return problemas + ["el validador no produjo un dictamen interpretable"]

    if dictamen.veredicto != "ACEPTADA":
        problemas.append("el validador la rechaza")

    comparaciones = [
        ("colocadas", dictamen.colocadas, fila["tiles_placed"]),
        ("ocupadas", dictamen.ocupadas, fila["occupied_cells"]),
        ("mayor", dictamen.mayor, fila["largest_tile"]),
    ]

    for nombre, verificado, informado in comparaciones:
        if str(verificado) != informado:
            problemas.append(
                nombre + " verificadas " + str(verificado)
                + " frente a " + informado + " informadas"
            )

    return problemas


def revalidar(filas: List[Dict[str, str]], raiz_datos: str) -> int:
    """Revalida todas las filas con solucion e imprime el recuento."""
    con_solucion = [fila for fila in filas if fila["solution_path"] != ""]
    sin_solucion = len(filas) - len(con_solucion)
    aceptadas = 0

    for fila in con_solucion:
        problemas = revalidar_fila(fila, raiz_datos)

        if len(problemas) == 0:
            aceptadas = aceptadas + 1
        else:
            print(fila["run_id"] + " " + fila["instance"] + " " + fila["agent"]
                  + ": " + "; ".join(problemas))

    print(
        "revalidacion: " + str(aceptadas) + "/" + str(len(con_solucion))
        + " aceptadas y coincidentes"
    )

    if sin_solucion > 0:
        print("corridas sin solucion que revalidar: " + str(sin_solucion))

    return 0 if aceptadas == len(con_solucion) and sin_solucion == 0 else 1


def main(argumentos: Optional[List[str]] = None) -> int:
    """Punto de entrada: revalida la bateria indicada."""
    analizador = argparse.ArgumentParser(
        prog="python -m experimentos.revalidar",
        description="Vuelve a validar todas las soluciones de una bateria.",
    )
    analizador.add_argument("experimento", help="comparacion o escalabilidad")
    opciones = analizador.parse_args(argumentos)

    ruta_crudo = os.path.join(DIRECTORIO_RESULTADOS, opciones.experimento, "crudo.csv")
    return revalidar(leer_crudo(ruta_crudo), corrida.RAIZ_REPOSITORIO)


if __name__ == "__main__":
    sys.exit(main())
