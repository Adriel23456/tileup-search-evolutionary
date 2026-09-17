"""
Codigos de salida del proceso.

Se definen en un solo lugar porque son parte del contrato del programa con
quien lo invoca: un guion de la bateria experimental, el evaluador del curso o
una tuberia de integracion continua distinguen exito de fallo por este numero,
no por el texto impreso.
"""


# La operacion termino correctamente.
CODIGO_SALIDA_EXITO = 0

# La operacion se completo, pero su veredicto es negativo. Lo usa el comando
# de validacion cuando una solucion es rechazada: el programa funciono bien,
# la solucion no.
CODIGO_SALIDA_VEREDICTO_NEGATIVO = 1

# Los datos de entrada son invalidos: archivo ausente, formato incorrecto o
# argumento fuera de rango.
CODIGO_SALIDA_ERROR_ENTRADA = 2

# Se solicito un agente que no esta registrado.
CODIGO_SALIDA_ERROR_AGENTE = 3