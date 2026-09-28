"""
Generador de instancias de TileUp parametrizado por N, K, M y una semilla.

El problema que resuelve este modulo no es producir numeros al azar, sino
producir instancias que se puedan ganar. Una secuencia totalmente aleatoria con
M mayor que N al cuadrado puede ser imposible para cualquier agente, y entonces
la comparacion experimental mediria quien pierde menos en lugar de quien
resuelve mejor.

La solucion es constructiva: el generador no inventa la secuencia y despues
comprueba si se puede ganar, sino que juega una partida legal completa e
inventa cada ficha en el momento de colocarla. El plan de colocaciones que
resulta es por tanto un testigo de que la instancia tiene al menos una
solucion.

Que la partida nunca se atasque descansa en una sola observacion: colocar una
ficha ocupa a lo sumo una celda neta, porque sin fusion ocupa una, y con una
fusion de tamano |G| se retiran |G| celdas y queda una, es decir se liberan
|G| - 1. Basta entonces garantizar que al empezar cada paso quede al menos una
celda vacia, y eso se consigue asi:

  - Si hay dos o mas celdas vacias, despues del paso queda al menos una.
  - Si queda exactamente una y todavia faltan fichas, esa celda tiene vecinos
    y todos estan ocupados, porque es la unica vacia. El generador copia el
    color de uno de ellos, con lo que |G| >= 2, la fusion libera |G| - 1 >= 1
    celdas y el invariante se restablece.
  - Si queda exactamente una y esa es la ultima ficha, se coloca y se gana.

Las reglas del juego no se reescriben aqui: la fusion la aplica MotorTileUp,
igual que para el jugador humano y para los agentes.
"""

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.dominio.estado_partida import EstadoPartida
from src.dominio.ficha import Ficha
from src.dominio.motor import MotorTileUp
from src.dominio.tablero import DESPLAZAMIENTOS_ORTOGONALES, Tablero
from src.instancias.errores import ErrorParametrosGenerador
from src.instancias.instancia import Instancia


# Valor maximo de una ficha recien generada. Los valores se sortean de forma
# uniforme en 1..VALOR_MAXIMO_FICHA. No hace falta una distribucion mas
# elaborada: el enunciado solo exige que el valor sea un entero positivo, y un
# solo digito mantiene el archivo legible y alineado, igual que las instancias
# de ejemplo que ya estan versionadas. La fusion ya se encarga de que aparezcan
# valores grandes durante la partida.
VALOR_MAXIMO_FICHA = 9


@dataclass(frozen=True)
class InstanciaGenerada:
    """
    Instancia recien generada junto con la partida que la hizo posible.

    El campo colocaciones es la lista de celdas (fila, columna) que el
    generador uso al construir la secuencia, en el orden de las fichas.
    Reproducirla sobre un tablero vacio consume las M fichas y gana la partida,
    de modo que sirve de testigo de resolubilidad y es lo que comprueban las
    pruebas.
    """

    instancia: Instancia
    colocaciones: List[Tuple[int, int]]


class GeneradorInstancias:
    """Construye instancias resolubles de TileUp a partir de N, K, M y semilla."""

    def __init__(self) -> None:
        """Construye el generador con el motor que aplica las reglas."""
        self._motor = MotorTileUp()

    def generar(self, dimension: int, cantidad_colores: int,
                cantidad_fichas: int, semilla: int,
                nombre: str = "generada") -> InstanciaGenerada:
        """
        Genera una instancia jugando una partida legal completa.

        Todo el azar proviene del generador sembrado con la semilla recibida,
        de modo que los mismos N, K, M y semilla producen siempre la misma
        instancia.
        """
        self._validar_parametros(dimension, cantidad_colores, cantidad_fichas)

        generador_azar = random.Random(semilla)
        tablero = Tablero(dimension)

        fichas: List[Ficha] = []
        colocaciones: List[Tuple[int, int]] = []

        for indice_ficha in range(cantidad_fichas):
            quedan_fichas_despues = indice_ficha < cantidad_fichas - 1

            celda, color = self._elegir_celda_y_color(
                tablero=tablero,
                cantidad_colores=cantidad_colores,
                quedan_fichas_despues=quedan_fichas_despues,
                generador_azar=generador_azar,
            )

            valor = generador_azar.randint(1, VALOR_MAXIMO_FICHA)
            ficha = Ficha(color=color, valor=valor)

            self._colocar_con_el_motor(tablero, ficha, celda)

            fichas.append(ficha)
            colocaciones.append(celda)

        instancia = Instancia(
            dimension=dimension,
            cantidad_colores=cantidad_colores,
            fichas=fichas,
            nombre=nombre,
        )

        return InstanciaGenerada(instancia=instancia, colocaciones=colocaciones)

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _validar_parametros(self, dimension: int, cantidad_colores: int,
                            cantidad_fichas: int) -> None:
        """
        Comprueba que los parametros describan una instancia generable.

        Ademas de los rangos obvios hay una restriccion real del procedimiento:
        en un tablero de 1x1 la unica celda no tiene vecinos, de modo que nunca
        puede haber fusion y no cabe mas de una ficha.
        """
        if dimension < 1:
            raise ErrorParametrosGenerador(
                "N debe ser mayor o igual a 1, se recibio: " + str(dimension)
            )

        if cantidad_colores < 1:
            raise ErrorParametrosGenerador(
                "K debe ser mayor o igual a 1, se recibio: "
                + str(cantidad_colores)
            )

        if cantidad_fichas < 0:
            raise ErrorParametrosGenerador(
                "M no puede ser negativo, se recibio: " + str(cantidad_fichas)
            )

        if dimension == 1 and cantidad_fichas > 1:
            raise ErrorParametrosGenerador(
                "Con N=1 el tablero tiene una sola celda y sin vecinos no hay "
                "fusion posible, asi que no cabe mas de una ficha; se pidieron "
                + str(cantidad_fichas) + ". Use N mayor o igual a 2."
            )

    def _elegir_celda_y_color(self, tablero: Tablero, cantidad_colores: int,
                              quedan_fichas_despues: bool,
                              generador_azar: random.Random) -> Tuple[Tuple[int, int], int]:
        """
        Decide donde va la ficha y de que color es.

        El caso normal es libre: una celda vacia al azar y un color uniforme en
        1..K. El caso especial es la unica regla que garantiza la resolubilidad:
        si solo queda una celda vacia y todavia faltan fichas, colocar sin
        fusion llenaria el tablero y perderia la partida, asi que se copia el
        color de un vecino para forzar la fusion que libera espacio.
        """
        celdas_vacias = tablero.celdas_vacias()

        if len(celdas_vacias) == 1 and quedan_fichas_despues is True:
            celda_forzada = celdas_vacias[0]
            color_vecino = self._color_de_un_vecino(tablero, celda_forzada)

            # Con N >= 2 siempre hay vecino, porque esa celda es la unica vacia
            # y _validar_parametros ya descarto el unico tablero sin vecinos.
            # La comprobacion es la red que evita que una instancia imposible
            # se cuele en silencio si ese razonamiento dejara de valer.
            if color_vecino is not None:
                return (celda_forzada, color_vecino)

        indice_elegido = generador_azar.randrange(len(celdas_vacias))
        celda_elegida = celdas_vacias[indice_elegido]
        color_elegido = generador_azar.randint(1, cantidad_colores)

        return (celda_elegida, color_elegido)

    def _color_de_un_vecino(self, tablero: Tablero,
                            celda: Tuple[int, int]) -> Optional[int]:
        """
        Devuelve el color del primer vecino ortogonal ocupado, o None si no hay.

        Se recorre en el orden fijo de DESPLAZAMIENTOS_ORTOGONALES para que la
        eleccion no dependa de nada distinto de la semilla.
        """
        fila, columna = celda

        for desplazamiento_fila, desplazamiento_columna in DESPLAZAMIENTOS_ORTOGONALES:
            fila_vecina = fila + desplazamiento_fila
            columna_vecina = columna + desplazamiento_columna

            if tablero.coordenada_valida(fila_vecina, columna_vecina) is False:
                continue

            ficha_vecina = tablero.obtener_ficha(fila_vecina, columna_vecina)

            if ficha_vecina is not None:
                return ficha_vecina.color

        return None

    def _colocar_con_el_motor(self, tablero: Tablero, ficha: Ficha,
                              celda: Tuple[int, int]) -> None:
        """
        Coloca la ficha en el tablero delegando la fusion en el motor.

        El motor lee la ficha pendiente de un EstadoPartida, que a su vez cuelga
        de una Instancia. Como aqui la secuencia se va inventando paso a paso,
        se arma una instancia de una sola ficha y un estado que envuelve el
        mismo objeto Tablero que se viene construyendo; el motor lo modifica en
        sitio. El rodeo vale la pena, porque asi la regla de fusion no se
        reescribe en ninguna parte de este modulo.
        """
        instancia_del_paso = Instancia(
            dimension=tablero.dimension,
            cantidad_colores=ficha.color,
            fichas=[ficha],
            nombre="paso_del_generador",
        )

        estado_del_paso = EstadoPartida(
            instancia=instancia_del_paso,
            tablero=tablero,
            indice_ficha_actual=0,
        )

        fila, columna = celda
        self._motor.colocar(estado_del_paso, fila, columna)
