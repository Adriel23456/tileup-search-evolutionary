"""
Subcomandos concretos de la linea de comandos.

Cada modulo de este paquete contiene una clase que implementa la interfaz
Comando y resuelve exactamente una tarea del programa: resolver una instancia
con agentes, validar una solucion, abrir la ventana de juego, revisar el
formato de una instancia, listar los agentes o informar el backend de computo.

Los comandos son capas delgadas. No contienen logica del juego ni de los
algoritmos: interpretan argumentos, delegan en los modulos del sistema e
informan el resultado.
"""