"""
Estructura de datos del tablero de TileUp.

Esta clase conoce la geometria del tablero (celdas, vecindad, componentes
conexas) pero NO conoce las reglas del juego. Las reglas viven en el motor.
Esta separacion respeta el Principio de Responsabilidad Unica de SOLID.
"""

from collections import deque
from typing import List, Optional, Set, Tuple

import numpy

from src.dominio.ficha import Ficha


# Constante que marca una celda vacia dentro de la matriz de colores.
COLOR_CELDA_VACIA = 0

# Desplazamientos de la vecindad ortogonal: arriba, abajo, izquierda, derecha.
DESPLAZAMIENTOS_ORTOGONALES = (
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
)


class Tablero:
    """
    Cuadricula de N x N celdas.

    Internamente se usan dos matrices de NumPy en lugar de una matriz de
    objetos:
      - _colores: entero por celda, 0 significa celda vacia.
      - _valores: entero por celda, 0 cuando la celda esta vacia.

    Esta representacion es contigua en memoria y barata de copiar, que es la
    operacion mas frecuente cuando la busqueda expande sucesores.
    """

    def __init__(self, dimension: int) -> None:
        """Crea un tablero vacio de dimension x dimension celdas."""
        if dimension < 1:
            raise ValueError(
                "La dimension del tablero debe ser mayor o igual a 1, "
                "se recibio: " + str(dimension)
            )

        self._dimension = dimension
        self._colores = numpy.zeros((dimension, dimension), dtype=numpy.int32)
        self._valores = numpy.zeros((dimension, dimension), dtype=numpy.int64)
        self._cantidad_ocupadas = 0

    # ------------------------------------------------------------------
    # Consultas basicas
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        """Devuelve N, el lado del tablero."""
        return self._dimension

    @property
    def cantidad_celdas(self) -> int:
        """Devuelve la cantidad total de celdas del tablero."""
        return self._dimension * self._dimension

    @property
    def cantidad_ocupadas(self) -> int:
        """Devuelve cuantas celdas contienen una ficha en este momento."""
        return self._cantidad_ocupadas

    @property
    def cantidad_vacias(self) -> int:
        """Devuelve cuantas celdas estan libres en este momento."""
        return self.cantidad_celdas - self._cantidad_ocupadas

    def esta_lleno(self) -> bool:
        """Indica si no queda ninguna celda vacia."""
        return self.cantidad_vacias == 0

    def coordenada_valida(self, fila: int, columna: int) -> bool:
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

    def esta_vacia(self, fila: int, columna: int) -> bool:
        """Indica si la celda indicada no contiene ninguna ficha."""
        if self.coordenada_valida(fila, columna) is False:
            raise IndexError(
                "Coordenada fuera del tablero: ("
                + str(fila) + ", " + str(columna) + ")"
            )

        return int(self._colores[fila][columna]) == COLOR_CELDA_VACIA

    def obtener_ficha(self, fila: int, columna: int) -> Optional[Ficha]:
        """Devuelve la ficha de la celda, o None si la celda esta vacia."""
        if self.esta_vacia(fila, columna) is True:
            return None

        color = int(self._colores[fila][columna])
        valor = int(self._valores[fila][columna])
        return Ficha(color=color, valor=valor)

    def celdas_vacias(self) -> List[Tuple[int, int]]:
        """
        Devuelve la lista de coordenadas libres.

        El tamano de esta lista es exactamente el factor de ramificacion del
        estado, tal como lo define el enunciado.
        """
        coordenadas_libres: List[Tuple[int, int]] = []

        for fila in range(self._dimension):
            for columna in range(self._dimension):
                if int(self._colores[fila][columna]) == COLOR_CELDA_VACIA:
                    coordenadas_libres.append((fila, columna))

        return coordenadas_libres

    def valor_ficha_mayor(self) -> int:
        """Devuelve el valor de la ficha mas grande, o 0 si no hay fichas."""
        if self._cantidad_ocupadas == 0:
            return 0

        return int(self._valores.max())

    def suma_total_valores(self) -> int:
        """
        Devuelve la suma de todos los valores presentes en el tablero.

        La fusion conserva la suma, por lo que este numero no depende de las
        decisiones del agente. Sirve de invariante en las pruebas.
        """
        return int(self._valores.sum())

    # ------------------------------------------------------------------
    # Modificaciones
    # ------------------------------------------------------------------

    def escribir_ficha(self, fila: int, columna: int, ficha: Ficha) -> None:
        """
        Escribe una ficha en una celda que debe estar vacia.

        Es una operacion de bajo nivel: no aplica fusion. El motor decide
        cuando llamarla.
        """
        if self.esta_vacia(fila, columna) is False:
            raise ValueError(
                "La celda (" + str(fila) + ", " + str(columna)
                + ") ya esta ocupada"
            )

        self._colores[fila][columna] = ficha.color
        self._valores[fila][columna] = ficha.valor
        self._cantidad_ocupadas = self._cantidad_ocupadas + 1

    def vaciar_celda(self, fila: int, columna: int) -> None:
        """Deja una celda libre. La usa el motor durante la fusion."""
        if self.esta_vacia(fila, columna) is True:
            return

        self._colores[fila][columna] = COLOR_CELDA_VACIA
        self._valores[fila][columna] = 0
        self._cantidad_ocupadas = self._cantidad_ocupadas - 1

    # ------------------------------------------------------------------
    # Conectividad
    # ------------------------------------------------------------------

    def componente_conexa(self, fila: int, columna: int) -> List[Tuple[int, int]]:
        """
        Calcula la componente conexa maximal del mismo color que contiene a la
        celda indicada, usando vecindad ortogonal.

        Es un recorrido en anchura tal como se vio en clase: la frontera es
        una cola FIFO y un conjunto de visitadas evita procesar dos veces la
        misma celda. La celda de origen debe estar ocupada.
        """
        if self.esta_vacia(fila, columna) is True:
            raise ValueError(
                "No existe componente conexa desde una celda vacia: ("
                + str(fila) + ", " + str(columna) + ")"
            )

        color_objetivo = int(self._colores[fila][columna])

        visitadas: Set[Tuple[int, int]] = set()
        componente: List[Tuple[int, int]] = []
        frontera: deque = deque()

        frontera.append((fila, columna))
        visitadas.add((fila, columna))

        while len(frontera) > 0:
            fila_actual, columna_actual = frontera.popleft()
            componente.append((fila_actual, columna_actual))

            for desplazamiento_fila, desplazamiento_columna in DESPLAZAMIENTOS_ORTOGONALES:
                fila_vecina = fila_actual + desplazamiento_fila
                columna_vecina = columna_actual + desplazamiento_columna

                if self.coordenada_valida(fila_vecina, columna_vecina) is False:
                    continue

                if (fila_vecina, columna_vecina) in visitadas:
                    continue

                if int(self._colores[fila_vecina][columna_vecina]) != color_objetivo:
                    continue

                visitadas.add((fila_vecina, columna_vecina))
                frontera.append((fila_vecina, columna_vecina))

        return componente

    # ------------------------------------------------------------------
    # Copia e identidad
    # ------------------------------------------------------------------

    def copiar(self) -> "Tablero":
        """Devuelve una copia profunda e independiente del tablero."""
        copia = Tablero(self._dimension)
        copia._colores = self._colores.copy()
        copia._valores = self._valores.copy()
        copia._cantidad_ocupadas = self._cantidad_ocupadas
        return copia

    def clave_hash(self) -> bytes:
        """
        Devuelve una clave inmutable que identifica el contenido del tablero.

        Es lo que permite usar la lista cerrada de la busqueda como un
        conjunto, igual que el 'explored' del pseudocodigo de clase.
        """
        return self._colores.tobytes() + self._valores.tobytes()