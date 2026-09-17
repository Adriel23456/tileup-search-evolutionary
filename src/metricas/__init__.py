"""
Metricas reportables y bitacoras de resultados.

Agrupa la estructura de metricas que se informa por salida estandar al
terminar una partida y la bitacora acumulada de partidas humanas, que sirve
como linea base de comparacion en el informe final.

La medida de esfuerzo es generica a proposito: el agente de busqueda reporta
nodos expandidos y el evolutivo evaluaciones de aptitud, sin que la estructura
de metricas tenga que cambiar.
"""