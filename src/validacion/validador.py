"""
Arbitraje de una solucion de TileUp.

El validador recibe una instancia y un archivo de solucion, reproduce la
partida paso a paso con el verificador independiente de reglas y dictamina si
la solucion es legal, informando fichas colocadas y celdas ocupadas al final.

Comprueba cuatro cosas:
  1. Los indices de ficha son 0, 1, 2, ... consecutivos y en orden.
  2. Cada colocacion cae dentro del tablero y sobre una celda vacia.
  3. La partida no continua despues de haberse perdido.
  4. El resumen declarado en el archivo coincide con lo verificado.

Una solucion incompleta no es ilegal: el enunciado obliga a escribir la
solucion aun cuando la partida termine en derrota. El dictamen distingue
legalidad de completitud.
"""

from typing import List, Optional

from src.instancias.instancia import Instancia
from src.validacion.lector_solucion import SolucionLeida
from src.validacion.verificador_reglas import TableroVerificacion


class DictamenValidacion:
    """Resultado completo de validar una solucion."""

    def __init__(self, es_legal: bool, esta_completa: bool,
                 fichas_colocadas: int, fichas_totales: int,
                 celdas_ocupadas: int, valor_ficha_mayor: int,
                 suma_de_valores: int, motivos: List[str]) -> None:
        """Agrupa el veredicto y las metricas verificadas."""
        self.es_legal = es_legal
        self.esta_completa = esta_completa
        self.fichas_colocadas = fichas_colocadas
        self.fichas_totales = fichas_totales
        self.celdas_ocupadas = celdas_ocupadas
        self.valor_ficha_mayor = valor_ficha_mayor
        self.suma_de_valores = suma_de_valores
        self.motivos = motivos

    def como_texto(self) -> str:
        """Genera el informe legible del dictamen."""
        lineas: List[str] = []

        if self.es_legal is True:
            lineas.append("veredicto=ACEPTADA")
        else:
            lineas.append("veredicto=RECHAZADA")

        lineas.append(
            "colocadas=" + str(self.fichas_colocadas)
            + "/" + str(self.fichas_totales)
            + " ocupadas=" + str(self.celdas_ocupadas)
            + " mayor=" + str(self.valor_ficha_mayor)
            + " suma=" + str(self.suma_de_valores)
        )

        if self.esta_completa is True:
            lineas.append("completitud=secuencia_consumida")
        else:
            lineas.append("completitud=secuencia_incompleta")

        for motivo in self.motivos:
            lineas.append("  - " + motivo)

        return "\n".join(lineas)


class Validador:
    """Reproduce y arbitra una solucion contra su instancia."""

    def validar(self, instancia: Instancia,
                solucion: SolucionLeida) -> DictamenValidacion:
        """Ejecuta las cuatro comprobaciones y devuelve el dictamen."""
        tablero = TableroVerificacion(instancia.dimension)
        motivos: List[str] = []

        es_legal = True
        fichas_colocadas = 0

        for posicion in range(solucion.cantidad_colocaciones):
            indice_declarado, fila, columna = solucion.colocaciones[posicion]

            motivo_de_orden = self._revisar_orden(
                indice_declarado, posicion, instancia
            )

            if motivo_de_orden is not None:
                motivos.append(motivo_de_orden)
                es_legal = False
                break

            motivo_de_tablero_lleno = self._revisar_tablero_disponible(
                tablero, posicion
            )

            if motivo_de_tablero_lleno is not None:
                motivos.append(motivo_de_tablero_lleno)
                es_legal = False
                break

            ficha = instancia.obtener_ficha(posicion)

            resultado = tablero.aplicar_colocacion(
                fila=fila,
                columna=columna,
                color=ficha.color,
                valor=ficha.valor,
            )

            if resultado.fue_legal is False:
                motivos.append(
                    "Colocacion " + str(posicion) + " ilegal: "
                    + resultado.motivo
                )
                es_legal = False
                break

            fichas_colocadas = fichas_colocadas + 1

        celdas_ocupadas = tablero.contar_ocupadas()
        valor_mayor = tablero.valor_mayor()
        suma_de_valores = tablero.suma_de_valores()

        motivo_de_suma = self._revisar_conservacion_de_suma(
            instancia, fichas_colocadas, suma_de_valores
        )

        if motivo_de_suma is not None:
            motivos.append(motivo_de_suma)
            es_legal = False

        motivo_de_resumen = self._revisar_resumen_declarado(
            solucion, fichas_colocadas, celdas_ocupadas, valor_mayor
        )

        if motivo_de_resumen is not None:
            motivos.append(motivo_de_resumen)
            es_legal = False

        esta_completa = fichas_colocadas == instancia.cantidad_fichas

        if es_legal is True and esta_completa is False:
            motivos.append(
                "La secuencia quedo incompleta: se colocaron "
                + str(fichas_colocadas) + " de "
                + str(instancia.cantidad_fichas) + " fichas"
            )

        return DictamenValidacion(
            es_legal=es_legal,
            esta_completa=esta_completa,
            fichas_colocadas=fichas_colocadas,
            fichas_totales=instancia.cantidad_fichas,
            celdas_ocupadas=celdas_ocupadas,
            valor_ficha_mayor=valor_mayor,
            suma_de_valores=suma_de_valores,
            motivos=motivos,
        )

    # ------------------------------------------------------------------
    # Comprobaciones individuales
    # ------------------------------------------------------------------

    def _revisar_orden(self, indice_declarado: int, posicion: int,
                       instancia: Instancia) -> Optional[str]:
        """Comprueba que las fichas se consuman en orden y sin saltos."""
        if indice_declarado != posicion:
            return (
                "La colocacion en la posicion " + str(posicion)
                + " declara el indice de ficha " + str(indice_declarado)
                + "; las fichas se consumen en orden estricto desde cero"
            )

        if posicion >= instancia.cantidad_fichas:
            return (
                "La solucion contiene mas colocaciones ("
                + str(posicion + 1) + ") que fichas en la secuencia ("
                + str(instancia.cantidad_fichas) + ")"
            )

        return None

    def _revisar_tablero_disponible(self, tablero: TableroVerificacion,
                                    posicion: int) -> Optional[str]:
        """Comprueba que la partida no continue despues de una derrota."""
        if tablero.hay_celdas_libres() is True:
            return None

        return (
            "La colocacion " + str(posicion) + " ocurre con el tablero lleno; "
            "la partida ya habia terminado en derrota"
        )

    def _revisar_conservacion_de_suma(self, instancia: Instancia,
                                      fichas_colocadas: int,
                                      suma_de_valores: int) -> Optional[str]:
        """
        Comprueba que la fusion haya conservado la suma de valores.

        El enunciado observa que el valor total presente en el tablero no
        depende de las decisiones del agente. Es por tanto un invariante
        exacto y una prueba barata de que la reproduccion fue fiel.
        """
        suma_esperada = 0

        for posicion in range(fichas_colocadas):
            suma_esperada = suma_esperada + instancia.obtener_ficha(posicion).valor

        if suma_esperada == suma_de_valores:
            return None

        return (
            "La suma de valores del tablero es " + str(suma_de_valores)
            + " pero las " + str(fichas_colocadas) + " fichas colocadas suman "
            + str(suma_esperada) + "; la fusion debe conservar la suma"
        )

    def _revisar_resumen_declarado(self, solucion: SolucionLeida,
                                   fichas_colocadas: int,
                                   celdas_ocupadas: int,
                                   valor_mayor: int) -> Optional[str]:
        """Compara el resumen del archivo con lo verificado."""
        if solucion.resumen is None:
            return (
                "El archivo no incluye la linea de resumen que el formato "
                "exige"
            )

        discrepancias: List[str] = []

        if solucion.resumen.colocadas != fichas_colocadas:
            discrepancias.append(
                "colocadas declaradas " + str(solucion.resumen.colocadas)
                + " frente a " + str(fichas_colocadas) + " verificadas"
            )

        if solucion.resumen.ocupadas != celdas_ocupadas:
            discrepancias.append(
                "ocupadas declaradas " + str(solucion.resumen.ocupadas)
                + " frente a " + str(celdas_ocupadas) + " verificadas"
            )

        if solucion.resumen.mayor != valor_mayor:
            discrepancias.append(
                "mayor declarado " + str(solucion.resumen.mayor)
                + " frente a " + str(valor_mayor) + " verificado"
            )

        if len(discrepancias) == 0:
            return None

        return "El resumen no coincide: " + "; ".join(discrepancias)