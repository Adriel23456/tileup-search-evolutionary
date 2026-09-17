"""Errores controlados de lectura y validacion de soluciones."""


class ErrorFormatoSolucion(Exception):
    """
    Se lanza cuando un archivo de solucion esta mal formado.

    Igual que con las instancias, un archivo invalido debe producir un mensaje
    legible y un codigo de salida distinto de cero, nunca una traza sin
    controlar.
    """

    def __init__(self, mensaje: str, numero_linea: int = -1) -> None:
        """Construye el error, opcionalmente con el numero de linea afectado."""
        self.numero_linea = numero_linea

        if numero_linea >= 0:
            mensaje_completo = "Linea " + str(numero_linea) + ": " + mensaje
        else:
            mensaje_completo = mensaje

        super().__init__(mensaje_completo)