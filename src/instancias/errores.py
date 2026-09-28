"""Errores controlados de lectura de instancias."""


class ErrorFormatoInstancia(Exception):
    """
    Se lanza cuando un archivo de instancia esta mal formado.

    El enunciado exige que un archivo invalido produzca un mensaje legible y
    un codigo de salida distinto de cero, nunca una traza sin controlar.
    """

    def __init__(self, mensaje: str, numero_linea: int = -1) -> None:
        """Construye el error, opcionalmente con el numero de linea afectado."""
        self.numero_linea = numero_linea

        if numero_linea >= 0:
            mensaje_completo = "Linea " + str(numero_linea) + ": " + mensaje
        else:
            mensaje_completo = mensaje

        super().__init__(mensaje_completo)


class ErrorParametrosGenerador(Exception):
    """
    Se lanza cuando los parametros pedidos al generador no describen una
    instancia generable.

    Igual que con un archivo mal formado, el programa debe responder con un
    mensaje legible y un codigo de salida distinto de cero, nunca con una traza
    sin controlar.
    """
