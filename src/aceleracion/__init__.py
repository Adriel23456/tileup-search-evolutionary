"""
Deteccion del backend de computo disponible.

En la etapa actual todo el sistema corre en CPU con NumPy, porque el motor
opera sobre tableros pequenos donde una transferencia a la GPU costaria mas
que el calculo completo.

El paquete existe como punto de extension para el agente evolutivo, que si
puede beneficiarse de evaluar poblaciones completas en lote sobre GPU.
"""