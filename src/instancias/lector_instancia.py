"""
Lectura del formato de instancia definido en el enunciado.

Formato:
  - Las lineas en blanco se ignoran.
  - Todo lo que sigue a un caracter '#' se ignora hasta el fin de linea.
  - Primera linea util: N y K separados por espacio.
  - Segunda linea util: M.
  - Siguientes M lineas utiles: color y valor de cada ficha, en orden.
"""

import os
from typing import List

from src.dominio.ficha import Ficha
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.instancia import Instancia


# Marca de orden de bytes que Windows antepone a los archivos UTF-8. Hay que
# descartarla antes de interpretar el contenido, porque de lo contrario el
# primer campo del archivo llega con un caracter invisible pegado y el lector
# lo rechaza con un mensaje que no explica nada.
MARCA_DE_ORDEN_DE_BYTES = "\ufeff"


class LectorInstancia:
    """
    Convierte un archivo de texto en un objeto Instancia.

    Es la unica clase del sistema que conoce el formato de entrada. Si el
    formato cambiara, solo este archivo se modifica, lo que cumple el
    Principio Abierto/Cerrado respecto al resto del sistema.
    """

    def leer_desde_archivo(self, ruta_archivo: str) -> Instancia:
        """Lee y valida una instancia desde la ruta indicada."""
        if os.path.isfile(ruta_archivo) is False:
            raise ErrorFormatoInstancia(
                "No se encontro el archivo de instancia: " + str(ruta_archivo)
            )

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except OSError as error_de_lectura:
            raise ErrorFormatoInstancia(
                "No se pudo leer el archivo de instancia: "
                + str(error_de_lectura)
            )

        nombre_instancia = os.path.splitext(os.path.basename(ruta_archivo))[0]
        return self.leer_desde_texto(contenido, nombre_instancia)

    def leer_desde_texto(self, contenido: str,
                         nombre_instancia: str = "sin_nombre") -> Instancia:
        """Lee y valida una instancia a partir de su contenido en texto."""
        if contenido.startswith(MARCA_DE_ORDEN_DE_BYTES) is True:
            contenido = contenido[len(MARCA_DE_ORDEN_DE_BYTES):]

            
        lineas_utiles = self._extraer_lineas_utiles(contenido)

        if len(lineas_utiles) < 2:
            raise ErrorFormatoInstancia(
                "El archivo debe contener al menos la linea de N y K "
                "y la linea de M"
            )

        dimension, cantidad_colores = self._leer_dimension_y_colores(
            lineas_utiles[0]
        )
        cantidad_fichas = self._leer_cantidad_fichas(lineas_utiles[1])

        lineas_de_fichas = lineas_utiles[2:]

        if len(lineas_de_fichas) < cantidad_fichas:
            raise ErrorFormatoInstancia(
                "Se declararon " + str(cantidad_fichas) + " fichas pero el "
                "archivo solo contiene " + str(len(lineas_de_fichas))
            )

        fichas = self._leer_fichas(
            lineas_de_fichas, cantidad_fichas, cantidad_colores
        )

        try:
            return Instancia(
                dimension=dimension,
                cantidad_colores=cantidad_colores,
                fichas=fichas,
                nombre=nombre_instancia,
            )
        except ValueError as error_de_validacion:
            raise ErrorFormatoInstancia(str(error_de_validacion))

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _extraer_lineas_utiles(self, contenido: str) -> List[tuple]:
        """
        Elimina comentarios y lineas vacias.

        Devuelve una lista de tuplas (numero_de_linea_original, texto_limpio)
        para poder reportar errores con la ubicacion exacta.
        """
        lineas_utiles: List[tuple] = []
        numero_linea = 0

        for linea_original in contenido.splitlines():
            numero_linea = numero_linea + 1

            posicion_comentario = linea_original.find("#")

            if posicion_comentario >= 0:
                linea_sin_comentario = linea_original[:posicion_comentario]
            else:
                linea_sin_comentario = linea_original

            linea_limpia = linea_sin_comentario.strip()

            if len(linea_limpia) == 0:
                continue

            lineas_utiles.append((numero_linea, linea_limpia))

        return lineas_utiles

    def _leer_dimension_y_colores(self, linea_util: tuple) -> tuple:
        """Interpreta la linea que declara N y K."""
        numero_linea, texto = linea_util
        campos = texto.split()

        if len(campos) != 2:
            raise ErrorFormatoInstancia(
                "Se esperaban exactamente dos enteros (N y K), "
                "se encontraron " + str(len(campos)),
                numero_linea,
            )

        dimension = self._convertir_a_entero(campos[0], "N", numero_linea)
        cantidad_colores = self._convertir_a_entero(campos[1], "K", numero_linea)

        if dimension < 1:
            raise ErrorFormatoInstancia(
                "N debe ser mayor o igual a 1", numero_linea
            )

        if cantidad_colores < 1:
            raise ErrorFormatoInstancia(
                "K debe ser mayor o igual a 1", numero_linea
            )

        return (dimension, cantidad_colores)

    def _leer_cantidad_fichas(self, linea_util: tuple) -> int:
        """Interpreta la linea que declara M."""
        numero_linea, texto = linea_util
        campos = texto.split()

        if len(campos) != 1:
            raise ErrorFormatoInstancia(
                "Se esperaba exactamente un entero (M), "
                "se encontraron " + str(len(campos)),
                numero_linea,
            )

        cantidad_fichas = self._convertir_a_entero(campos[0], "M", numero_linea)

        if cantidad_fichas < 0:
            raise ErrorFormatoInstancia(
                "M no puede ser negativo", numero_linea
            )

        return cantidad_fichas

    def _leer_fichas(self, lineas_de_fichas: List[tuple], cantidad_fichas: int,
                     cantidad_colores: int) -> List[Ficha]:
        """Interpreta las M lineas de fichas."""
        fichas: List[Ficha] = []

        for posicion in range(cantidad_fichas):
            numero_linea, texto = lineas_de_fichas[posicion]
            campos = texto.split()

            if len(campos) != 2:
                raise ErrorFormatoInstancia(
                    "Se esperaban dos enteros (color y valor), "
                    "se encontraron " + str(len(campos)),
                    numero_linea,
                )

            color = self._convertir_a_entero(campos[0], "color", numero_linea)
            valor = self._convertir_a_entero(campos[1], "valor", numero_linea)

            if color < 1:
                raise ErrorFormatoInstancia(
                    "El color debe ser mayor o igual a 1", numero_linea
                )

            if color > cantidad_colores:
                raise ErrorFormatoInstancia(
                    "El color " + str(color) + " excede el valor de K ("
                    + str(cantidad_colores) + ")",
                    numero_linea,
                )

            if valor < 1:
                raise ErrorFormatoInstancia(
                    "El valor de la ficha debe ser un entero positivo",
                    numero_linea,
                )

            fichas.append(Ficha(color=color, valor=valor))

        return fichas

    def _convertir_a_entero(self, texto: str, nombre_campo: str,
                            numero_linea: int) -> int:
        """Convierte texto a entero produciendo un error legible si falla."""
        try:
            return int(texto)
        except ValueError:
            raise ErrorFormatoInstancia(
                "El campo " + nombre_campo + " no es un entero valido: '"
                + texto + "'",
                numero_linea,
            )