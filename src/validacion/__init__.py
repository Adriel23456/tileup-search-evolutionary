"""
Validacion independiente de soluciones de TileUp.

Este paquete contiene un programa de arbitraje: dada una instancia y un
archivo de solucion, reproduce la partida paso a paso y dictamina si la
solucion es legal.

Su rasgo central es la independencia. El verificador de reglas de este
paquete NO usa el motor del paquete dominio: reimplementa la colocacion y la
fusion desde cero, con estructuras de datos distintas y un recorrido distinto.
De ese modo el validador no hereda los posibles errores del motor y puede
servir de contraste real, no de eco.

Tampoco comparte codigo de decision con ningun agente: el validador no elige
donde colocar nada, solo comprueba lo que otro decidio.
"""