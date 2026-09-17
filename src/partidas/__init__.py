"""
Orquestacion de partidas.

Contiene la sesion de partida, que es el punto unico por donde pasan todas las
colocaciones, el contrato de observacion que permite seguir el avance sin
acoplarse a ninguna capa de presentacion, y el ejecutor que corre un agente
sobre una instancia.

La sesion separa dos responsabilidades que no deben mezclarse: el motor decide
si una jugada es legal, y la sesion decide que se registra y a quien se avisa.
"""