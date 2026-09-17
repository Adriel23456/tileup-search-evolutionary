"""
Capa de linea de comandos.

Contiene el contrato de los subcomandos, sus implementaciones concretas, el
registro que los expone y el ejecutor que corre agentes y reporta metricas.

Implementa el contrato de ejecucion exigido por el enunciado: un punto de
entrada que recibe la instancia, el agente, la semilla y el limite de tiempo,
sin pasos interactivos.

Ningun modulo de este paquete importa Tkinter en su cabecera. El unico
subcomando que necesita la capa grafica, jugar, la importa dentro de su
metodo ejecutar, de modo que resolver una instancia o validar una solucion
nunca carga el entorno grafico.
"""