# Declaracion de uso de inteligencia artificial

Tarea Corta 1 - Agentes de busqueda y evolutivos para TileUp
Inteligencia Artificial (IC-6200) - Instituto Tecnologico de Costa Rica

Este documento responde al requisito del enunciado de declarar como se usaron
herramientas de IA, en que partes y que se verifico de forma manual.

## Equipo

| Integrante | Carne | Uso de IA declarado |
|---|---|---|
| Adriel S. Chaves Salazar | 2021031465 | Si, detallado abajo |
| Daniel Duarte Cordero | 2022012866 | Pendiente de completar |
| Sebastian Hernandez Bonilla | 2022093651 | Si, Etapas A y C, detallado abajo |

Cada integrante completa su propia seccion. Un apartado vacio significa que
ese integrante todavia no ha declarado su uso, no que no lo haya habido.

## Herramientas utilizadas

| Herramienta | Integrante | Periodo |
|---|---|---|
| Claude (Anthropic), interfaz web | Adriel S. Chaves Salazar | Semanas 8 a 10 |
| Claude Code (Anthropic), agente de programacion | Sebastian Hernandez Bonilla | Etapas A y C |

## Adriel S. Chaves Salazar

### Resumen

La herramienta se uso principalmente para la **infraestructura** del
programa: la capa de linea de comandos, la interfaz grafica de juego humano,
la organizacion de los modulos en capas y la escritura de archivos. El
**nucleo evaluable** del trabajo, es decir el motor del juego y el agente de
busqueda, se desarrollo de forma iterativa con la herramienta, pero cada
decision algoritmica y cada argumento matematico fueron formulados,
verificados y en varios casos corregidos por el estudiante.

### En que partes se uso

| Componente | Grado de uso | Detalle |
|---|---|---|
| Capa de linea de comandos (`src/cli/`) | Alto | Subcomandos, registro, despacho de argumentos y codigos de salida. Infraestructura, no logica del juego. |
| Interfaz grafica (`src/gui/`) | Alto | Ventana de juego humano en Tkinter. Infraestructura, no logica del juego. |
| Organizacion en capas y convencion de nombrado | Alto | Estructura de directorios y patrones de nombre, ajustados varias veces segun las objeciones del estudiante. |
| Lectura de instancias y escritura de soluciones | Alto | Generados a partir del formato definido en el enunciado. |
| Bitacoras de resultados (`src/metricas/`) | Alto | Acumulacion de metricas en CSV. Infraestructura. |
| Motor del juego (`src/dominio/`) | Medio | Escritura asistida, con las reglas verificadas linea por linea contra la seccion 2 del enunciado. |
| Agente de busqueda (`src/agentes/`) | Medio | Escritura asistida. La formulacion del problema, la funcion de costo y el argumento de admisibilidad se verificaron a mano, y se corrigieron errores de la herramienta. |
| Validador independiente (`src/validacion/`) | Medio | Escritura asistida, con la independencia respecto al motor verificada a mano. |
| Pruebas automatizadas (`pruebas/`) | Alto | Casos derivados de los requisitos del enunciado. |
| README y este documento | Alto | Redaccion asistida, contenido tecnico verificado. |
| Decisiones de arquitectura | Bajo | La herramienta propuso alternativas; la eleccion final fue del estudiante, y en varios casos contra la propuesta de la herramienta. |

### Como se uso

El flujo fue conversacional e iterativo. El enunciado completo se entrego
como contexto y a partir de ahi se pidieron componentes concretos, se
revisaron, se corrigieron y se volvieron a pedir. La herramienta no se uso de
forma autonoma: cada respuesta paso por revision antes de entrar al
repositorio, y varias fueron rechazadas por completo.

### Aportacion intelectual del estudiante

**Requisitos del sistema.** La separacion entre juego humano y ejecucion por
consola, la exigencia de codigo legible sin atajos de sintaxis, el uso de
espanol sin caracteres especiales, la aplicacion de SOLID y la organizacion
de entradas y salidas fueron decisiones impuestas a la herramienta, no
sugerencias suyas.

**Rechazo de propuestas incorrectas.** Se rechazaron y rehicieron varias
respuestas. Los casos con consecuencias en el codigo entregado:

1. *Tres ejecutables en lugar de uno.* La herramienta propuso `main.py`,
   `jugar.py` y `validar.py` separados, y lo justifico invocando el Principio
   de Responsabilidad Unica. El estudiante objeto que SOLID rige clases y
   modulos, no la cantidad de archivos con punto de entrada, y exigio un
   punto de entrada unico con subcomandos. La arquitectura actual es
   consecuencia de esa objecion.

2. *Busqueda en haz presentada como A\*.* La primera version del agente podaba
   los sucesores a seis por nodo, lo que convierte A* en una busqueda en haz y
   le quita la optimalidad. El estudiante exigio ajustarse al algoritmo visto
   en clase, y la poda se elimino.

3. *Heuristica innecesariamente compleja.* La primera heuristica contaba
   "componentes congeladas" ademas de colores pendientes, con un argumento
   costoso de evaluar y dificil de defender. Se sustituyo por la cota de
   colores pendientes, que es mas simple y se justifica en tres frases.

4. *Variantes de agente no pedidas.* La herramienta registro cuatro variantes
   del agente de busqueda cuando el enunciado pide una. Se redujeron a la
   variante del enunciado mas una linea base de Dijkstra que sirve al informe.

5. *Nombrado inconsistente.* Los agentes se llamaban `busqueda` y
   `busqueda_dijkstra`, dos criterios distintos para lo mismo. El estudiante
   exigio un unico patron, `busqueda_<heuristica>`, que es el vigente.

### Que se verifico de forma manual

**Reglas del juego.** Cada regla del codigo se comparo con la seccion 2 del
enunciado: representacion del estado, factor de ramificacion igual a las
celdas vacias, fusion sobre la componente conexa maximal por vecindad
ortogonal, ausencia de encadenamiento de fusiones, y las dos condiciones de
termino. El ejemplo de instancia del enunciado se resolvio a mano y se
comparo con la salida del programa.

**Funcion de costo.** Se verifico algebraicamente que
`g_total = M(N^2 - 2) + ocupadas_finales` para todo camino meta, es decir que
el termino constante es identico entre caminos y por tanto minimizar `g`
equivale a minimizar celdas ocupadas. Tambien se comprobo que el costo nunca
es negativo, condicion necesaria para las garantias de A*.

**Admisibilidad de la heuristica.** El argumento de conservacion se derivo a
mano:
`liberaciones_futuras = ocupadas_ahora + R - ocupadas_finales`. Se calculo el
caso del tablero 2x2 con dos fichas del mismo color, donde `h = h* = 5`, y se
convirtio en la prueba
`test_la_heuristica_admisible_no_sobreestima_en_un_caso_conocido`.

**Falta de consistencia.** El estudiante verifico que
`h(n) - h(n') = costo(a) + (colores(n) - colores(n'))`, que excede `costo(a)`
cuando un color desaparece de la secuencia pendiente. La heuristica es por
tanto admisible pero no consistente, lo que obliga a reabrir nodos cerrados
en A* sobre grafos. Esa correccion esta en el codigo y documentada en el
README.

**Independencia del validador.** Se reviso que `src/validacion/` no importe
nada de `src/dominio/`, que use estructuras distintas (listas de Python frente
a NumPy) y un recorrido distinto (profundidad con pila frente a anchura con
cola), y que no contenga ninguna logica de decision.

**Determinismo.** Se ejecutaron los agentes dos veces con la misma instancia y
semilla y se compararon los archivos de solucion. Quedo automatizado en
`test_determinismo_por_semilla`.

### Defectos encontrados por el estudiante en el codigo asistido

1. *Barra de progreso duplicada.* `SesionPartida.finalizar` notificaba a los
   observadores en cada llamada, y tanto la colocacion final como el ejecutor
   la invocaban. Se corrigio haciendo idempotentes `iniciar` y `finalizar`, y
   se fijo con `test_los_observadores_reciben_una_sola_notificacion_de_fin`.

2. *Limite de tiempo excedido.* Con `--limite-tiempo 20` el agente tardaba
   20.97 segundos, porque el completado avido ocurria fuera del presupuesto.
   El enunciado descalifica al agente que excede el limite. Se corrigio
   reservando una fraccion del presupuesto para esa fase.

3. *Heuristica evaluada antes de podar.* En la version con poda, la heuristica
   se evaluaba en los 36 sucesores para luego descartar 30. Se detecto al
   observar que una ejecucion de 30 segundos no producia salida alguna.

4. *Resultados no registrados.* Ninguna ejecucion de agente escribia en
   `resultados/`. Se detecto revisando el directorio tras una tanda completa,
   y se corrigio agregando la bitacora de ejecuciones.

5. *Codigo muerto.* Se identificaron y eliminaron metodos que ninguna parte
   del sistema llamaba, agregados por la herramienta durante iteraciones
   anteriores.

### Que no se delego

La regla de frontera del enunciado prohibe delegar en una biblioteca o en un
tercero la construccion de aquello que constituye el objeto de aprendizaje:

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

Las unicas bibliotecas externas son NumPy y pytest, que el enunciado permite
de forma expresa. En la Etapa C se agrego matplotlib, tambien permitida, solo
para las graficas de la experimentacion.

Todo componente presente en la entrega puede ser explicado y fundamentado por
el estudiante.

## Daniel Duarte Cordero

Pendiente de completar por el integrante.

## Sebastian Hernandez Bonilla

### En que partes se uso

| Componente | Grado de uso | Detalle |
|---|---|---|
| Generador de instancias (Etapa A) | Alto | `src/instancias/generador_instancia.py`, `escritor_instancia.py`, subcomando `generar` y sus pruebas. |
| Infraestructura experimental (Etapa C) | Alto | Guiones de `experimentos/`: runner, revalidacion, resumen, graficas y prueba de determinismo. |
| Criterio de paro determinista de ambos agentes | Medio | Presupuestos de trabajo con el reloj como salvaguarda. No se cambio ningun otro componente de los algoritmos. |
| Redaccion del analisis experimental | Alto | Secciones experimentales de `INFORME.md` y del README, redactadas a partir de los CSV formales. |

### Como se uso

La herramienta trabajo sobre el repositorio con instrucciones por etapas y
puertas de control explicitas: debia detenerse y mostrar evidencia antes de
cada decision relevante, y no podia modificar los agentes, el motor ni el
validador sin aprobacion.

### Decisiones y verificaciones del estudiante

- Decidio las semillas pareadas (la misma `s` genera la instancia y se entrega
  al agente), el uso de `rho = M / N^2`, las seis configuraciones de la
  comparacion, la rejilla de escalabilidad y el limite `T = 10 s`, a partir de
  la evidencia del piloto.
- Exigio que `resolver` no escribiera por defecto en un CSV global.
- Al aparecer una solucion distinta de A* con entradas identicas, detuvo las
  baterias, descarto los resultados obtenidos hasta entonces como formales y
  exigio una correccion general del criterio de paro, con evidencia antes de
  cualquier cambio de codigo.
- Aprobo los valores de los presupuestos (2200 y 20000) segun la regla de
  calibracion propuesta, y fijo como condicion de validez `clock_safeguard =
  False` en todas las corridas formales.
- Reviso en cada fase la evidencia reportada (hashes, estados, revalidacion) e
  hizo los commits manualmente.

La redaccion de esta seccion la propuso la herramienta y queda sujeta a la
revision del integrante.

## Historial de este documento

| Fecha | Cambio |
|---|---|
| Semana 10 | Version inicial, con la declaracion de Adriel S. Chaves Salazar. |
| 2026-09-30 | Declaracion de Sebastian Hernandez Bonilla para las Etapas A y C. |