# Declaracion de uso de inteligencia artificial

Tarea Corta 1 - Agentes de busqueda y evolutivos para TileUp
Inteligencia Artificial (IC-6200) - Instituto Tecnologico de Costa Rica

Este documento responde al requisito del enunciado de declarar como se usaron
herramientas de IA, en que partes y que se verifico de forma manual. Se
actualiza durante todo el desarrollo y su version final acompana la entrega.

## Equipo

| Integrante | Carne | Uso de IA declarado |
|---|---|---|
| Adriel S. Chaves Salazar | 2021031465 | Si, detallado abajo |
| Daniel Duarte Cordero | 2022012866 | Pendiente de completar |
| Sebastian Hernandez Bonilla | 2022093651 | Pendiente de completar |

Cada integrante completa su propia seccion. Un apartado vacio significa que
ese integrante todavia no ha declarado su uso, no que no lo haya habido.

## Herramientas utilizadas

| Herramienta | Integrante | Periodo |
|---|---|---|
| Claude (Anthropic), interfaz web | Adriel S. Chaves Salazar | Semanas 8 a 10 |

## Adriel S. Chaves Salazar

### En que partes se uso

| Componente | Grado de uso | Detalle |
|---|---|---|
| Estructura de directorios y convencion de nombrado | Alto | Propuesta inicial generada y luego ajustada a los requisitos del enunciado. |
| Motor del juego (`src/dominio/`) | Alto | Codigo generado a partir de la especificacion del enunciado, revisado contra el texto original regla por regla. |
| Lector de instancias y escritor de soluciones | Alto | Generados a partir del formato definido en el enunciado. |
| Agente de busqueda A* (`src/agentes/`) | Alto | Formulacion del problema, funcion de costo, heuristicas e implementacion. Ver la seccion de verificacion. |
| Validador independiente (`src/validacion/`) | Alto | Reimplementacion de las reglas y comprobaciones de arbitraje. |
| Capa de linea de comandos (`src/cli/`) | Alto | Subcomandos, registro y despacho de argumentos. |
| Interfaz grafica (`src/gui/`) | Alto | Ventana de juego humano en Tkinter. |
| Pruebas automatizadas (`pruebas/`) | Alto | Casos generados a partir de los requisitos del enunciado y ampliados a mano. |
| README y este documento | Alto | Redaccion asistida, contenido tecnico verificado. |
| Decisiones de arquitectura | Medio | La IA propuso alternativas; la eleccion final fue del equipo. Ver abajo. |

### Como se uso

El flujo de trabajo fue conversacional e iterativo. El enunciado completo se
entrego a la herramienta como contexto y a partir de ahi se pidieron
componentes concretos, se revisaron, se corrigieron y se volvieron a pedir.
La herramienta no se uso de forma autonoma: cada respuesta paso por revision
antes de entrar al repositorio.

El aporte intelectual del equipo se concentro en tres puntos:

1. **Definicion de los requisitos del sistema.** La division entre juego
   humano y ejecucion por consola, la exigencia de codigo legible sin atajos
   de sintaxis, el uso de espanol sin caracteres especiales, la aplicacion de
   SOLID y la organizacion de entradas y salidas fueron decisiones del equipo
   impuestas a la herramienta, no sugerencias suyas.

2. **Correccion de propuestas incorrectas.** Varias respuestas se rechazaron y
   se rehicieron. El caso mas relevante: la herramienta propuso inicialmente
   tres ejecutables separados (`main.py`, `jugar.py`, `validar.py`) y lo
   justifico invocando el Principio de Responsabilidad Unica. El equipo
   objeto que SOLID rige clases y modulos, no la cantidad de archivos con
   punto de entrada, y exigio un punto de entrada unico con subcomandos. La
   arquitectura actual es consecuencia de esa objecion. La herramienta
   tambien confundio nombres de archivo de instancia y recomendo un cambio
   que contradecia su propia convencion previa; el equipo lo detecto y lo
   descarto.

3. **Verificacion contra el enunciado y contra la ejecucion real.** Todo lo
   que se detalla en la seccion siguiente.

### Que se verifico de forma manual

**Reglas del juego.** Cada regla del codigo se comparo linea por linea con la
seccion 2 del enunciado: representacion del estado, factor de ramificacion
igual a las celdas vacias, fusion sobre la componente conexa maximal por
vecindad ortogonal, ausencia de encadenamiento de fusiones, y las dos
condiciones de termino. Se comprobo a mano el ejemplo de instancia del
enunciado.

**Funcion de costo del agente de busqueda.** Se verifico algebraicamente que
`g_total = M(N^2 - 2) + ocupadas_finales` para todo camino meta, es decir que
el termino constante es identico entre caminos y por tanto minimizar `g`
equivale a minimizar celdas ocupadas. Tambien se comprobo que el costo nunca
es negativo, condicion necesaria para las garantias de A*.

**Admisibilidad de la heuristica.** El argumento de conservacion se reviso a
mano: `liberaciones_futuras = (ocupadas + restantes) - ocupadas_finales`, y
los dos aportes de la cota (colores pendientes y componentes congeladas) se
verificaron disjuntos porque hablan de colores distintos. Se calculo a mano el
caso del tablero 2x2 con dos fichas del mismo color, donde `h = h* = 5`, y se
convirtio en la prueba `test_la_heuristica_admisible_no_sobreestima_en_un_caso_conocido`.

**Independencia del validador.** Se reviso que `src/validacion/` no importe
nada de `src/dominio/`, que use estructuras distintas (listas de Python frente
a NumPy) y un recorrido distinto (profundidad con pila frente a anchura con
cola), y que no contenga ninguna logica de decision. La coincidencia entre
motor y validador sobre las soluciones producidas se comprueba en
`test_el_camino_producido_es_legal_segun_el_validador`.

**Determinismo.** Se ejecutaron los agentes dos veces con la misma instancia y
semilla y se compararon los archivos de solucion byte a byte. Esta
comprobacion quedo automatizada en `test_determinismo_por_semilla`.

**Defecto encontrado y corregido a mano.** Al revisar la salida real de una
ejecucion, el equipo noto que la barra de progreso se imprimia dos veces. La
causa era que `SesionPartida.finalizar` notificaba a los observadores en cada
llamada, y tanto la colocacion final como el ejecutor la invocaban. Se
diagnostico leyendo el flujo de control, se corrigio haciendo idempotentes
`iniciar` y `finalizar`, y se fijo con la prueba
`test_los_observadores_reciben_una_sola_notificacion_de_fin`.

**Ejecucion completa.** Todos los comandos documentados en el README se
ejecutaron en la maquina del equipo y su salida se verifico. La suite de
pruebas pasa integra.

### Que no se delego

La regla de frontera del enunciado prohibe delegar en una biblioteca o en un
tercero la construccion de aquello que constituye el objeto de aprendizaje.
El equipo la interpreta asi:

- No se uso ninguna biblioteca de busqueda en grafos o en espacios de estados.
  La cola de prioridad es `heapq` de la biblioteca estandar, y el algoritmo A*
  esta escrito en `src/agentes/agente_busqueda.py`.
- No se uso ningun marco de computacion evolutiva ni de optimizacion
  metaheuristica.
- No se uso ningun resolvedor de restricciones, de programacion entera o de
  satisfacibilidad.
- No se tomo el motor del juego de ningun tercero.
- **No se invoca ningun modelo de lenguaje en tiempo de ejecucion.** Los
  agentes deciden sus colocaciones con los algoritmos implementados en el
  repositorio. El programa no realiza ninguna llamada de red.

Las bibliotecas externas usadas son NumPy, para arreglos contiguos y
operaciones vectorizadas, y pytest, como marco de pruebas. Ambas pertenecen a
las capas inferiores que el enunciado permite de forma expresa.

Todo componente presente en la entrega puede ser explicado y fundamentado por
el equipo.

## Daniel Duarte Cordero

Pendiente de completar por el integrante.

## Sebastian Hernandez Bonilla

Pendiente de completar por el integrante.

## Historial de este documento

| Fecha | Cambio |
|---|---|
| Semana 10 | Version inicial, con la declaracion de Adriel S. Chaves Salazar. |