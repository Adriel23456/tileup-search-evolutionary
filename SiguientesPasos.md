# Siguientes pasos

Notas de trabajo del equipo. No forma parte de la entrega.

Tarea Corta 1 - Agentes de busqueda y evolutivos para TileUp
Inteligencia Artificial (IC-6200) - Instituto Tecnologico de Costa Rica

## Estado actual

| Bloque | Peso | Estado |
|---|---|---|
| Motor y validador | 12 | Completo |
| Agente de busqueda | 16 | Completo |
| Agente evolutivo | 16 | No iniciado |
| Comparacion experimental | 14 | No iniciado |
| Escalabilidad (grupo de 3) | 12 | No iniciado |
| README e informe | 12 | README completo; informe no iniciado |
| Reproducibilidad | 8 | Completo |
| Repositorio y autoria | 5 | Solo un autor con commits |
| Video y entrega | 5 | No iniciado |

Asegurados 36 de 100. Faltan 42 del bloque tecnico y 22 del de
profesionalidad.

## Lo que ya quedo resuelto

Los pendientes de infraestructura estan cerrados y verificados en frio:

- `setup.ps1` prepara el entorno, instala dependencias, corre las pruebas,
  resuelve la instancia de ejemplo y la valida, todo en una orden. Cubre el
  criterio de aceptacion 1.
- `validar_lote.ps1` valida todas las soluciones del repositorio contra sus
  instancias y reporta aceptadas y rechazadas.
- La instancia `ciega_n5_k4_m15.txt` se resolvio y valido sin haberse usado
  durante el desarrollo. Cubre el criterio de aceptacion 2.
- Un archivo de instancia mal formado produce un mensaje legible y codigo de
  salida 2, incluso cuando viene guardado como UTF-8 con marca de orden de
  bytes, que es lo que producen Notepad y Excel en Windows.
- `.venv` y `__pycache__` no estan versionados.
- Las soluciones y las bitacoras de resultados si se versionan, como exige el
  enunciado para que el informe pueda verificarse con el validador.

---

## Etapa A - Generador de instancias

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

---

## Etapa C - Experimentacion

**Que es.** Correr ambos agentes sobre todas las instancias generadas y
acumular los resultados. Son dos baterias distintas:

- **Comparacion.** 6 o mas configuraciones por 3 o mas semillas, midiendo
  fichas colocadas, celdas ocupadas, tiempo de computo y medida de esfuerzo.
- **Escalabilidad.** 3 valores de N por 3 de K por 3 semillas, mas al menos
  una grafica de tendencia.

**Lo que se olvida.** Los resultados van con su dispersion entre semillas, no
como un numero unico. Una tabla con un solo valor por celda baja a Bueno.

**Cuando esta listo.** Los CSV estan llenos, la grafica existe, y
`validar_lote.ps1` acepta todas las soluciones producidas.

---

## Etapa D - Informe

**Que es.** `INFORME.md` con la formulacion de ambos agentes y la lectura de
los experimentos.

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
powershell -ExecutionPolicy Bypass -File validar_lote.ps1
```