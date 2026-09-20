"""
Lectura del formato de solucion definido en el enunciado.

Formato:
  - Una linea por colocacion con tres enteros: indice de ficha, fila, columna.
  - Las lineas que comienzan con '#' son comentarios.
  - La ultima linea comienza con '#' y resume colocadas, ocupadas y mayor.

Este modulo solo interpreta el archivo. No juzga si la partida es legal: de
eso se encarga el validador.
"""

import os
from typing import List, Optional, Tuple

from src.validacion.errores import ErrorFormatoSolucion


# Claves que identifican la linea de resumen dentro de los comentarios.
CLAVE_COLOCADAS = "colocadas="
CLAVE_OCUPADAS = "ocupadas="
CLAVE_MAYOR = "mayor="

# Marca de orden de bytes que Windows antepone a los archivos UTF-8.
MARCA_DE_ORDEN_DE_BYTES = "\ufeff"


class ResumenDeclarado:
    """Valores que el archivo de solucion afirma haber alcanzado."""

    def __init__(self, colocadas: int, ocupadas: int, mayor: int) -> None:
        """Guarda los tres valores declarados en la linea de resumen."""
        self.colocadas = colocadas
        self.ocupadas = ocupadas
        self.mayor = mayor


class SolucionLeida:
    """Contenido interpretado de un archivo de solucion."""

    def __init__(self, colocaciones: List[Tuple[int, int, int]],
                 resumen: Optional[ResumenDeclarado], nombre: str) -> None:
        """Agrupa las colocaciones y el resumen declarado, si existe."""
        self.colocaciones = colocaciones
        self.resumen = resumen
        self.nombre = nombre

    @property
    def cantidad_colocaciones(self) -> int:
        """Devuelve cuantas colocaciones contiene el archivo."""
        return len(self.colocaciones)


class LectorSolucion:
    """Convierte un archivo de solucion en un objeto SolucionLeida."""

    def leer_desde_archivo(self, ruta_archivo: str) -> SolucionLeida:
        """Lee e interpreta una solucion desde la ruta indicada."""
        if os.path.isfile(ruta_archivo) is False:
            raise ErrorFormatoSolucion(
                "No se encontro el archivo de solucion: " + str(ruta_archivo)
            )

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except OSError as error_de_lectura:
            raise ErrorFormatoSolucion(
                "No se pudo leer el archivo de solucion: "
                + str(error_de_lectura)
            )

        nombre = os.path.splitext(os.path.basename(ruta_archivo))[0]
        return self.leer_desde_texto(contenido, nombre)

    def leer_desde_texto(self, contenido: str,
                         nombre: str = "sin_nombre") -> SolucionLeida:
        """Lee e interpreta una solucion a partir de su contenido en texto."""
        
        if contenido.startswith(MARCA_DE_ORDEN_DE_BYTES) is True:
            contenido = contenido[len(MARCA_DE_ORDEN_DE_BYTES):]

        colocaciones: List[Tuple[int, int, int]] = []
        resumen: Optional[ResumenDeclarado] = None
        numero_linea = 0

        for linea_original in contenido.splitlines():
            numero_linea = numero_linea + 1
            linea_limpia = linea_original.strip()

            if len(linea_limpia) == 0:
                continue

            if linea_limpia.startswith("#") is True:
                resumen_de_esta_linea = self._interpretar_comentario(
                    linea_limpia
                )

                if resumen_de_esta_linea is not None:
                    resumen = resumen_de_esta_linea

                continue

            colocaciones.append(
                self._interpretar_colocacion(linea_limpia, numero_linea)
            )

        return SolucionLeida(
            colocaciones=colocaciones,
            resumen=resumen,
            nombre=nombre,
        )

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _interpretar_colocacion(self, texto: str,
                                numero_linea: int) -> Tuple[int, int, int]:
        """Interpreta una linea de colocacion con tres enteros."""
        campos = texto.split()

        if len(campos) != 3:
            raise ErrorFormatoSolucion(
                "Se esperaban tres enteros (indice, fila, columna), "
                "se encontraron " + str(len(campos)),
                numero_linea,
            )

        indice_ficha = self._convertir_a_entero(
            campos[0], "indice de ficha", numero_linea
        )
        fila = self._convertir_a_entero(campos[1], "fila", numero_linea)
        columna = self._convertir_a_entero(campos[2], "columna", numero_linea)

        return (indice_ficha, fila, columna)

    def _interpretar_comentario(self, texto: str) -> Optional[ResumenDeclarado]:
        """
        Extrae el resumen de una linea de comentario, si lo contiene.

        Un comentario que no incluya las tres claves se considera una nota
        libre y se ignora sin error.
        """
        if texto.find(CLAVE_COLOCADAS) < 0:
            return None

        if texto.find(CLAVE_OCUPADAS) < 0:
            return None

        if texto.find(CLAVE_MAYOR) < 0:
            return None

        colocadas = self._extraer_valor_de_clave(texto, CLAVE_COLOCADAS)
        ocupadas = self._extraer_valor_de_clave(texto, CLAVE_OCUPADAS)
        mayor = self._extraer_valor_de_clave(texto, CLAVE_MAYOR)

        if colocadas is None:
            return None

        if ocupadas is None:
            return None

        if mayor is None:
            return None

        return ResumenDeclarado(
            colocadas=colocadas,
            ocupadas=ocupadas,
            mayor=mayor,
        )

    def _extraer_valor_de_clave(self, texto: str,
                                clave: str) -> Optional[int]:
        """Lee el entero que sigue a una clave del tipo 'nombre=valor'."""
        posicion_clave = texto.find(clave)

        if posicion_clave < 0:
            return None

        posicion_valor = posicion_clave + len(clave)
        caracteres_del_valor: List[str] = []

        for posicion in range(posicion_valor, len(texto)):
            caracter_actual = texto[posicion]

            if caracter_actual.isdigit() is True:
                caracteres_del_valor.append(caracter_actual)
            else:
                break

        if len(caracteres_del_valor) == 0:
            return None

        return int("".join(caracteres_del_valor))

    def _convertir_a_entero(self, texto: str, nombre_campo: str,
                            numero_linea: int) -> int:
        """Convierte texto a entero produciendo un error legible si falla."""
        try:
            return int(texto)
        except ValueError:
            raise ErrorFormatoSolucion(
                "El campo " + nombre_campo + " no es un entero valido: '"
                + texto + "'",
                numero_linea,
            )