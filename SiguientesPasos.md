# Siguientes pasos

Notas de trabajo del equipo. No forma parte de la entrega.

Tarea Corta 1 - Agentes de busqueda y evolutivos para TileUp
Inteligencia Artificial (IC-6200) - Instituto Tecnologico de Costa Rica

## Estado actual

| Bloque | Peso | Estado |
|---|---|---|
| Motor y validador | 12 | Completo |
| Agente de busqueda | 16 | Completo |
| Generador de instancias (Etapa A) | - | Completo |
| Agente evolutivo | 16 | Implementado; falta el CSV de calibracion de parametros |
| Comparacion experimental | 14 | Completo (Etapa C) |
| Escalabilidad (grupo de 3) | 12 | Completo (Etapa C) |
| README e informe | 12 | README completo; `INFORME.md` con la parte experimental; faltan las formulaciones (Etapa D) |
| Reproducibilidad | 8 | Completo |
| Repositorio y autoria | 5 | Commits de los tres integrantes; falta la declaracion de IA de Daniel |
| Video y entrega | 5 | No iniciado |

## Lo que ya quedo resuelto

Los pendientes de infraestructura estan cerrados y verificados en frio:

- `setup.ps1` prepara el entorno, instala dependencias, corre las pruebas,
  resuelve la instancia de ejemplo y la valida, todo en una orden. Cubre el
  criterio de aceptacion 1.
- `python -m experimentos.revalidar <bateria>` vuelve a validar todas las
  soluciones de una bateria experimental contra sus instancias, sin ejecutar
  los agentes, y reporta aceptadas y discrepancias.
- La instancia `ciega_n5_k4_m15.txt` se resolvio y valido sin haberse usado
  durante el desarrollo. Cubre el criterio de aceptacion 2.
- Un archivo de instancia mal formado produce un mensaje legible y codigo de
  salida 2, incluso cuando viene guardado como UTF-8 con marca de orden de
  bytes, que es lo que producen Notepad y Excel en Windows.
- `.venv` y `__pycache__` no estan versionados.
- Las soluciones y las bitacoras de resultados si se versionan, como exige el
  enunciado para que el informe pueda verificarse con el validador.

---

## Etapa A - Generador de instancias  [COMPLETA]

**Que es.** Un modulo que produce archivos de instancia a partir de N, K, M y
una semilla, mas un subcomando `generar` para invocarlo.

**Por que va primero.** La comparacion experimental exige 6 o mas
configuraciones con 3 o mas semillas cada una. Son 18 instancias como minimo,
y el modulo de escalabilidad pide mas. A mano no es viable.

**Cuidado con esto.** El generador debe producir instancias resolubles. Una
secuencia totalmente aleatoria con M cercano a N al cuadrado puede ser
imposible para cualquier agente, y entonces la comparacion mide quien pierde
menos en lugar de quien resuelve mejor.

**Cuando esta listo.** El subcomando genera archivos que
`python main.py instancia` acepta, y dos ejecuciones con la misma semilla
producen el mismo archivo byte a byte.

**Como quedo.** Ambas condiciones se cumplen y estan cubiertas por
`pruebas/test_generador_instancia.py`.

- `src/instancias/generador_instancia.py` construye la instancia jugando una
  partida legal completa e inventando cada ficha en el momento de colocarla,
  de modo que la lista de colocaciones resultante es un testigo de
  resolubilidad. La unica regla especial es que cuando queda una sola celda
  vacia y todavia faltan fichas, el color se copia de un vecino para forzar la
  fusion que libera espacio. La fusion la aplica `MotorTileUp`: el generador no
  reescribe ninguna regla del juego.
- `src/instancias/escritor_instancia.py` escribe el formato oficial, con los
  parametros anotados en la cabecera y salto de linea `\n` fijo.
- `src/cli/comandos/comando_generar.py` expone el subcomando `generar`.
- Las instancias de las baterias experimentales se generaron con el en la
  Etapa C y estan en `datos/instancias/`.

---

## Etapa B - Agente evolutivo

**Que es.** El segundo agente que exige el enunciado. Un algoritmo genetico
donde cada individuo es una partida completa y la aptitud mide que tan buena
resulto esa partida.

**Lo que la rubrica exige documentar.** Representacion del individuo, funcion
de aptitud, mecanismo de seleccion, operadores de variacion, politica de
reemplazo y criterio de paro. Cada uno con sus valores y, sobre todo, con el
procedimiento por el cual se fijaron. Un barrido de parametros guardado en un
CSV es la diferencia entre Excelente y Bueno en 16 puntos.

**Trampa a evitar.** El enunciado califica Deficiente un evolutivo que
reimplemente una busqueda exhaustiva bajo otro nombre. La evaluacion de
aptitud debe simular una partida, no explorar sucesores.

**Cuando esta listo.** `python main.py resolver --agente evolutivo` produce
soluciones que el validador acepta, es determinista por semilla, y existe el
CSV de calibracion de parametros.

**Como esta.** Implementado y validado en todas las baterias. Durante la Etapa
C su criterio de paro paso de reloj a presupuesto determinista de evaluaciones
(ver README, *Criterio de paro y determinismo*). **Pendiente:** el CSV de
calibracion de los pesos de aptitud, el tamano de poblacion y la probabilidad
de cruce. El runner `experimentos/bateria.py` puede reutilizarse para ese
barrido.

---

## Etapa C - Experimentacion  [COMPLETA]

**Que es.** Correr ambos agentes sobre todas las instancias generadas y
acumular los resultados. Son dos baterias distintas:

- **Comparacion.** 6 o mas configuraciones por 3 o mas semillas, midiendo
  fichas colocadas, celdas ocupadas, tiempo de computo y medida de esfuerzo.
- **Escalabilidad.** 3 valores de N por 3 de K por 3 semillas, mas al menos
  una grafica de tendencia.

**Lo que se olvida.** Los resultados van con su dispersion entre semillas, no
como un numero unico. Una tabla con un solo valor por celda baja a Bueno.

**Cuando esta listo.** Los CSV estan llenos, la grafica existe, y la
revalidacion acepta todas las soluciones producidas.

**Como quedo.** Comparacion con 36 corridas y escalabilidad con 54, todas ok,
validadas y con `clock_safeguard = False`. Revalidacion 36/36 y 54/54.
Resumenes, graficas e interpretacion en `INFORME.md`; comandos y estructura en
el README, seccion *Experimentacion*. En el camino se detecto que el paro por
reloj rompia el determinismo de A* entre sesiones; se corrigio con presupuestos
de trabajo deterministas y las baterias se repitieron desde cero.

---

## Etapa D - Informe

**Que es.** `INFORME.md` con la formulacion de ambos agentes y la lectura de
los experimentos.

**Como esta.** `INFORME.md` ya contiene la metodologia, la comparacion y la
escalabilidad con su interpretacion. **Pendiente:** agregar la formulacion de
A* (estado, operadores, costo, meta, heuristica y admisibilidad) y la del
evolutivo (representacion, aptitud, seleccion, variacion, reemplazo, paro y
procedimiento de fijacion de parametros).

**Lo que no es.** Una tabla de numeros. El enunciado pide interpretacion: que
parametro domina el costo, en que punto A* deja de terminar dentro del limite,
y como se comporta el evolutivo en ese mismo regimen.

**Ventaja que ya tenemos.** La formulacion de A*, la funcion de costo y el
argumento de admisibilidad estan escritos en el README. Se mueven al informe
casi tal cual.

**Dato util que ya tenemos.** En la instancia 4x4, `busqueda_astar` expande
502 nodos y termina en 0.06 segundos, mientras que `busqueda_dijkstra` agota
su presupuesto sin cerrar la busqueda. Esa es evidencia numerica directa de
cuanto aporta la heuristica.

**Principio de Defensa Tecnica.** Un componente cuya justificacion no conste
en el informe se evalua segun la evidencia disponible, aunque funcione.

---

## Etapa E - Repositorio y autoria

**Que es.** Que los tres integrantes tengan commits reales y que los tres
llenen su seccion en `DECLARACION_IA.md`.

**Por que importa mas de lo que parece.** Un integrante sin commits se evalua
individualmente segun la autoria que pueda demostrarse. Y un documento donde
solo uno declara uso de IA, con un repositorio de tres autores, es justo la
situacion que el enunciado dice que agrava.

**Reparto natural.** Las etapas A, B y C son tres piezas separables. Una por
persona.

**Como esta.** Los tres integrantes tienen commits. **Pendiente:** que Daniel
complete su seccion en `DECLARACION_IA.md`, y que Sebastian revise la suya,
redactada como borrador para las Etapas A y C.

---

## Etapa F - Entrega

**Que es.** El video de maximo diez minutos sin edicion, mas el paquete de
TecDigital.

**Que debe mostrar el video, en orden.** Clonar el repositorio, ejecutar ambos
agentes sobre una instancia, validar las soluciones producidas, y recorrer el
informe.

**Detalle.** Grabar clonando en una carpeta limpia, no en el directorio de
trabajo. Eso es literalmente lo que el evaluador va a hacer.

**Flujo sugerido para el video.**

```powershell
git clone <url>
cd tileup-search-evolutionary
powershell -ExecutionPolicy Bypass -File setup.ps1
.venv\Scripts\python.exe main.py resolver --instancia <instancia> --agentes busqueda_astar evolutivo --semilla 7 --limite-tiempo 10
.venv\Scripts\python.exe main.py validar --instancia <instancia> --solucion <solucion de cada agente>
.venv\Scripts\python.exe -m experimentos.revalidar comparacion
```