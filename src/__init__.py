"""
Sistema TileUp: motor del juego, agentes automaticos e interfaz de juego.

La organizacion en paquetes sigue una jerarquia estricta de dependencias, de
abajo hacia arriba:

    dominio  ->  no depende de nada del sistema
    instancias, soluciones, metricas, nombrado  ->  dependen de dominio
    partidas  ->  depende de dominio, instancias, soluciones, metricas
    agentes   ->  depende de dominio
    cli, gui  ->  dependen de todo lo anterior, y de nada mas

Ninguna capa importa a otra de nivel superior. En particular, el dominio se
ejecuta y se prueba sin entorno grafico y sin agentes.
"""