"""
Reimplementacion independiente de las reglas de TileUp.

Este modulo NO importa nada del paquete dominio. Es una segunda escritura de
las mismas reglas, hecha a proposito con estructuras y recorridos distintos:

  - El tablero es una lista de listas de Python, no dos matrices de NumPy.
  - La componente conexa se recorre en profundidad con una pila explicita, no
    en anchura con una cola doble.

El objetivo es que el validador no herede los errores del motor. Si ambas
implementaciones coinciden en el resultado de una partida, la coincidencia es
evidencia real de correccion; si compartieran codigo, no seria evidencia de
nada.
"""

from typing import List, Optional, Set, Tuple


# Desplazamientos de la vecindad ortogonal, en un orden distinto al del motor
# para que el recorrido tampoco coincida por casualidad.
VECINDAD_ORTOGONAL = (
    (0, 1),
    (1, 0),
    (0, -1),
    (-1, 0),
)


class ResultadoVerificacion:
    """Veredicto de una colocacion verificada."""

    def __init__(self, fue_legal: bool, motivo: str) -> None:
        """Agrupa si la colocacion fue legal y por que."""
        self.fue_legal = fue_legal
        self.motivo = motivo


class TableroVerificacion:
    """
    Tablero de verificacion construido sobre listas de Python.

    Cada celda guarda None si esta vacia, o una tupla (color, valor) si
    contiene una ficha.
    """

    def __init__(self, dimension: int) -> None:
        """Crea un tablero vacio de dimension x dimension celdas."""
        self._dimension = dimension
        self._celdas: List[List[Optional[Tuple[int, int]]]] = []

        for indice_fila in range(dimension):
            fila_nueva: List[Optional[Tuple[int, int]]] = []

            for indice_columna in range(dimension):
                fila_nueva.append(None)

            self._celdas.append(fila_nueva)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def esta_dentro(self, fila: int, columna: int) -> bool:
        """Indica si la coordenada cae dentro de los limites del tablero."""
        if fila < 0:
            return False

        if columna < 0:
            return False

        if fila >= self._dimension:
            return False

        if columna >= self._dimension:
            return False

        return True

    def esta_libre(self, fila: int, columna: int) -> bool:
        """Indica si la celda no contiene ninguna ficha."""
        return self._celdas[fila][columna] is None

    def contar_ocupadas(self) -> int:
        """Cuenta cuantas celdas contienen una ficha."""
        total_ocupadas = 0

        for indice_fila in range(self._dimension):
            for indice_columna in range(self._dimension):
                if self._celdas[indice_fila][indice_columna] is not None:
                    total_ocupadas = total_ocupadas + 1

        return total_ocupadas

    def hay_celdas_libres(self) -> bool:
        """Indica si queda al menos una celda vacia."""
        return self.contar_ocupadas() < (self._dimension * self._dimension)

    def valor_mayor(self) -> int:
        """Devuelve el valor de la ficha mas grande, o 0 si no hay fichas."""
        valor_maximo = 0

        for indice_fila in range(self._dimension):
            for indice_columna in range(self._dimension):
                contenido = self._celdas[indice_fila][indice_columna]

                if contenido is None:
                    continue

                color_de_la_celda, valor_de_la_celda = contenido

                if valor_de_la_celda > valor_maximo:
                    valor_maximo = valor_de_la_celda

        return valor_maximo

    def suma_de_valores(self) -> int:
        """Suma todos los valores presentes en el tablero."""
        suma_total = 0

        for indice_fila in range(self._dimension):
            for indice_columna in range(self._dimension):
                contenido = self._celdas[indice_fila][indice_columna]

                if contenido is None:
                    continue

                color_de_la_celda, valor_de_la_celda = contenido
                suma_total = suma_total + valor_de_la_celda

        return suma_total

    # ------------------------------------------------------------------
    # Aplicacion de una colocacion
    # ------------------------------------------------------------------

    def aplicar_colocacion(self, fila: int, columna: int, color: int,
                           valor: int) -> ResultadoVerificacion:
        """Coloca una ficha y aplica la fusion, verificando la legalidad."""
        if self.esta_dentro(fila, columna) is False:
            return ResultadoVerificacion(
                fue_legal=False,
                motivo=(
                    "la coordenada (" + str(fila) + ", " + str(columna)
                    + ") esta fuera de un tablero de lado "
                    + str(self._dimension)
                ),
            )

        if self.esta_libre(fila, columna) is False:
            return ResultadoVerificacion(
                fue_legal=False,
                motivo=(
                    "la celda (" + str(fila) + ", " + str(columna)
                    + ") ya estaba ocupada"
                ),
            )

        self._celdas[fila][columna] = (color, valor)

        grupo = self._recorrer_grupo_del_mismo_color(fila, columna, color)
        tamano_grupo = len(grupo)

        if tamano_grupo < 2:
            return ResultadoVerificacion(
                fue_legal=True,
                motivo="colocacion sin fusion",
            )

        valor_acumulado = 0

        for fila_del_grupo, columna_del_grupo in grupo:
            contenido = self._celdas[fila_del_grupo][columna_del_grupo]
            color_de_la_celda, valor_de_la_celda = contenido
            valor_acumulado = valor_acumulado + valor_de_la_celda

        for fila_del_grupo, columna_del_grupo in grupo:
            self._celdas[fila_del_grupo][columna_del_grupo] = None

        self._celdas[fila][columna] = (color, valor_acumulado)

        return ResultadoVerificacion(
            fue_legal=True,
            motivo="fusion de " + str(tamano_grupo) + " fichas",
        )

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _recorrer_grupo_del_mismo_color(self, fila: int, columna: int,
                                        color: int) -> List[Tuple[int, int]]:
        """
        Recorre en profundidad la componente conexa maximal del color dado.

        Se usa una pila explicita en lugar de recursion, para que un tablero
        grande no agote la pila de llamadas de Python.
        """
        visitadas: Set[Tuple[int, int]] = set()
        grupo: List[Tuple[int, int]] = []
        pendientes: List[Tuple[int, int]] = [(fila, columna)]

        visitadas.add((fila, columna))

        while len(pendientes) > 0:
            fila_actual, columna_actual = pendientes.pop()
            grupo.append((fila_actual, columna_actual))

            for desplazamiento_fila, desplazamiento_columna in VECINDAD_ORTOGONAL:
                fila_vecina = fila_actual + desplazamiento_fila
                columna_vecina = columna_actual + desplazamiento_columna

                if self.esta_dentro(fila_vecina, columna_vecina) is False:
                    continue

                if (fila_vecina, columna_vecina) in visitadas:
                    continue

                contenido_vecino = self._celdas[fila_vecina][columna_vecina]

                if contenido_vecino is None:
                    continue

                color_vecino, valor_vecino = contenido_vecino

                if color_vecino != color:
                    continue

                visitadas.add((fila_vecina, columna_vecina))
                pendientes.append((fila_vecina, columna_vecina))

        return grupo