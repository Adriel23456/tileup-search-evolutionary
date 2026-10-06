# Informe — Agentes de búsqueda y evolutivos para TileUp

Tarea Corta 1 — Inteligencia Artificial (IC-6200) — Instituto Tecnológico de
Costa Rica.

Este informe documenta la formulación de ambos agentes y la evidencia
experimental reproducible. Es complementario al `README.md`: este último explica
cómo ejecutar el proyecto; aquí se justifican las decisiones de los agentes y
se interpretan los resultados. Todas las afirmaciones cuantitativas se
restringen a las baterías y al entorno reportados.

Los resultados formales de comparación y escalabilidad provienen de los CSV
`crudo.csv` y sus resúmenes. Los parámetros del agente evolutivo se sometieron
a un barrido de calibración, descrito en la sección 1.2, con sus propios CSV.
En cada sección se distingue lo que se observó de lo que se concluye.

## 1. Formulación de los agentes

### 1.1 Agente de búsqueda: A*

#### Formulación del problema

A* explora distintas formas de colocar las fichas. En cada paso puede usar
cualquier celda vacía y prefiere los caminos que parecen dejar menos celdas
ocupadas al final. Para decidir qué camino revisar primero, toma en cuenta los
colores que todavía faltan: si aún quedan varios colores, sabe que algunos no
podrán fusionarse entre sí y deberán ocupar espacio al final.

| Elemento | Definición |
|---|---|
| Estado | `⟨tablero, i⟩`, donde `i` indica cuál ficha toca colocar. |
| Estado inicial | Tablero vacío e `i = 0`. |
| Siguiente acción | Colocar la ficha `i` en cualquier celda vacía y aplicar la fusión. |
| Ramificación | La cantidad de celdas vacías. |
| Meta | `i = M`, es decir, ya se colocaron las `M` fichas. |

El costo de una colocación es:

```text
costo = (N² − 1) − liberadas,   liberadas = |G| − 1
```

`G` es el grupo que se fusiona al colocar la ficha. Una fusión grande libera
más celdas, así que su costo es menor. Al terminar una partida se cumple:

```text
Σ liberadas = M − ocupadas_finales
g_total = M(N² − 2) + ocupadas_finales
```

La primera parte de `g_total` es igual para todas las soluciones de la misma
partida. Por eso, minimizar el costo equivale a dejar menos celdas ocupadas.

**Por qué se usa este costo.** Cada colocación añade una ficha al tablero. Si
no hay fusión, el grupo tiene tamaño `|G| = 1`, no se libera ninguna celda y el
costo queda en `N² − 1`, el valor más alto posible. Si al colocar una ficha se
forma un grupo de tamaño 3, se liberan `3 − 1 = 2` celdas y el costo baja en 2.
Así, una jugada que junta muchas fichas iguales resulta más barata que una que
deja una ficha aislada.

La constante `N² − 1` no cambia qué jugada es mejor; solo evita costos
negativos. Lo importante es la parte que se resta: cuantas más celdas libera
una jugada, menor es su costo.

**De dónde sale `g_total`.** En una partida con `M` fichas, se parte de cero
fichas en el tablero. Cada colocación suma una, y cada fusión resta las celdas
que libera. Por eso:

```text
ocupadas_finales = M − Σ liberadas
```

La suma de los costos de las `M` colocaciones es:

```text
g_total = M(N² − 1) − Σ liberadas
```

Al sustituir `Σ liberadas` por `M − ocupadas_finales`, se obtiene
`g_total = M(N² − 2) + ocupadas_finales`. Como `M(N² − 2)` es igual para toda
solución de esa partida, al comparar dos planes solo queda la diferencia en
`ocupadas_finales`. Esa es la razón por la que este costo representa el
objetivo del juego.

#### Cómo decide A*

La lista abierta es una cola de prioridad ordenada por `f = g + h`: `g` es el
costo acumulado y `h` estima el costo que aún falta. La lista cerrada guarda
estados que ya se revisaron, y el puntero `padre` permite reconstruir las
colocaciones al llegar a una solución.

Para estimar cuánto costo falta, A* usa:

```text
h(n) = max(0, R(N² − 1) − max(0, O + R − C))
```

Aquí `R` son las fichas pendientes, `O` las celdas ocupadas ahora y `C` los
colores distintos que aún faltan. La idea es sencilla: al final debe quedar al
menos una celda por cada color pendiente, porque ya no habrá otra ficha de ese
color para fusionarla.

**De dónde sale `h(n)`.** Quedan `R` colocaciones, por lo que, antes de contar
fusiones, el costo que falta sería `R(N² − 1)`. Para bajarlo necesitamos saber
cuántas celdas se podrían liberar como máximo. Ahora hay `O` celdas ocupadas y
todavía se colocarán `R` fichas: entre ambas cosas habrá `O + R` celdas antes
de las fusiones futuras. Sin embargo, como quedan `C` colores, al final al
menos `C` celdas deben permanecer. Por tanto, las liberaciones futuras no
pueden superar:

```text
liberaciones_futuras ≤ max(0, O + R − C)
```

Al restar ese máximo posible al costo base se obtiene `h(n)`. El `max(0, ...)`
exterior evita una estimación negativa; el interior evita decir que se pueden
liberar menos de cero celdas.

Por ejemplo, en un tablero de 3×3, si hay `O = 4` celdas ocupadas, quedan
`R = 3` fichas y aparecen `C = 2` colores, el costo base es `3(9 − 1) = 24`.
Como se pueden liberar como máximo `4 + 3 − 2 = 5` celdas, la estimación es
`h(n) = 24 − 5 = 19`. No está adivinando la solución exacta: solo afirma que
ninguna continuación puede costar menos que 19.

La estimación nunca se pasa del costo real que falta, así que si A* alcanza la
meta durante la búsqueda, obtiene el menor número posible de celdas ocupadas.
Al colocar la última ficha de un color, la estimación puede cambiar de golpe;
por eso, si aparece una forma más barata de llegar a un estado ya cerrado, el
agente lo vuelve a abrir. En otras palabras, no descarta definitivamente un
tablero solo porque ya lo hubiera visto: si luego encuentra una forma más
barata de llegar a él, lo revisa de nuevo.

#### Límite de tiempo y completado

El agente tiene un límite de exploración para terminar a tiempo. Con un límite
de 10 segundos revisa como máximo 22000 estados. Si todavía no completó la
partida, toma el mejor tablero encontrado hasta ese momento y termina con una
regla sencilla que busca la mejor fusión inmediata. La solución sigue siendo
válida, pero ya no se puede asegurar que sea la mejor posible. La columna
`search_cutoff` indica cuándo ocurrió esto.

### 1.2 Agente evolutivo

#### Representación y aptitud

El agente evolutivo mantiene varias propuestas de partida y las mejora poco a
poco. Una propuesta indica dónde colocar cada ficha. Las propuestas que colocan
más fichas y dejan menos celdas ocupadas reciben mejor puntuación. Solo entrega
una propuesta que puede jugarse completa y de forma legal.

Cada individuo contiene `M` genes; cada gen es una coordenada propuesta para
la ficha correspondiente. Para evaluarlo se simula la partida. Si una
coordenada ya está ocupada, se cuenta una reparación virtual para poder seguir
evaluando el resto de la propuesta; una propuesta con reparaciones nunca se
entrega como solución.

Su puntuación es:

```text
aptitud = 100 × fichas_colocadas − 10 × celdas_ocupadas − 25 × reparaciones
```

Así, primero le importa colocar fichas; después, dejar pocas celdas ocupadas.
Las reparaciones penalizan propuestas cuya secuencia tuvo que ajustarse para
seguir siendo legal. Los pesos 100/10/25 no se calibraron: replican el orden
del concurso (primero fichas colocadas, luego celdas ocupadas) y las
reparaciones solo sirven para desempatar a favor de planes legales.

#### Selección y cambio

| Componente | Decisión implementada |
|---|---|
| Población inicial | 20 individuos: un plan legal guiado por fusiones y los otros 19 planes legales aleatorios, derivados de la semilla. |
| Selección | Torneo de tres individuos. |
| Cruce y cambio | Cruce de un punto con probabilidad 0.70 y mutación guiada de 0 a 3 genes. |
| Reemplazo | Conserva una propuesta nueva solo si mejora a una de las actuales. |
| Paro | Usa un presupuesto de trabajo que depende del tiempo disponible y de la cantidad de fichas. |

La selección es por torneo de tres. Después se decide de forma independiente si
los dos padres se cruzan: con probabilidad `0.70` se aplica un cruce de un punto
y con probabilidad `0.30` no hay cruce, por lo que el hijo comienza como una
copia del primer padre. Por tanto, no todos los descendientes combinan
información de dos padres.

Luego se decide cuántos genes mutan. La cantidad se escoge uniformemente entre
`0`, `1`, `2` y `3`, respetando que no se pueden mutar más genes que los que
tiene el individuo. En el caso normal de `M >= 3`, cada cantidad tiene
probabilidad `0.25`: hay `0.25` de probabilidad de que el individuo no mute y
`0.75` de probabilidad de que mute al menos un gen. Si `M` es menor que 3,
estas probabilidades se ajustan porque la cantidad se limita a `M`.

La mutación es guiada y no consiste en escoger cualquier coordenada al azar.
Para cada gen seleccionado, el agente considera las celdas legales del estado
actual y prefiere la que produce la mayor componente conexa de fichas del mismo
color, es decir, la fusión inmediata más grande. Si hay empate, prefiere la
celda más cercana a la coordenada original y finalmente resuelve de forma
determinista por fila y columna. Las posiciones mutadas son distintas; si el
padre tenía reparaciones, se prioriza además el primer conflicto. Un hijo solo
reemplaza al peor individuo si realmente lo mejora.

El caso conjunto de ausencia de cruce y cero mutaciones tiene probabilidad
`0.30 × 0.25 = 0.075` (7.5 %) antes de considerar el límite `M`: en ese caso se
reutiliza directamente una copia del primer padre y su aptitud ya calculada.

La población no parte de veinte individuos aleatorios. Primero se construye un
individuo base completamente legal mediante una solución guiada desde el
estado inicial: en cada paso se elige la celda legal que permite la mayor
fusión inmediata; los empates se resuelven por distancia y luego por
coordenadas. Este individuo garantiza que desde el inicio haya una solución
completa y entregable. Después se generan los otros 19 individuos usando
elecciones legales aleatorias derivadas de la semilla. De esta manera, la
población inicial combina una solución de buena calidad conocida con diversidad
para explorar otras secuencias.

#### Población y límite

El límite no se implementa dejando que el reloj decida cuándo terminar. El
agente recibe un límite `T` en segundos, pero lo transforma en un presupuesto
fijo de evaluaciones de aptitud:

```text
presupuesto = max(1, floor(20000 × T / M))
```

`M` es la cantidad de fichas. Una evaluación consiste en simular el cromosoma
completo, es decir, hasta `M` colocaciones, y calcular su aptitud. Por eso se
presupuestan aproximadamente `20000 × T` colocaciones simuladas: cuando hay
más fichas, cada evaluación cuesta más y caben menos evaluaciones dentro del
mismo presupuesto. Por ejemplo, con `T = 10 s`:

| Fichas `M` | Evaluaciones máximas |
|---:|---:|
| 5 | `floor(200000 / 5) = 40000` |
| 8 | `floor(200000 / 8) = 25000` |
| 13 | `floor(200000 / 13) = 15384` |
| 25 | `floor(200000 / 25) = 8000` |

Este contador incluye las evaluaciones de la población inicial y las de los
hijos creados durante la evolución. Primero se evalúa el individuo guiado y se
van generando los demás individuos iniciales mientras quede presupuesto. Luego
se crean hijos y se detiene la evolución exactamente cuando se alcanza el
presupuesto. Si el hijo no tiene cruce ni mutación, se reutiliza la aptitud del
padre y no se cuenta una evaluación nueva, porque no se volvió a simular.

El reloj se usa únicamente como salvaguarda: el agente deja de trabajar al
llegar al `98 %` de `T` si la computadora está tardando más de lo previsto.
Esto permite guardar una solución válida antes de exceder el límite obligatorio,
pero esa interrupción queda marcada como `clock_safeguard = True`. En las
corridas normales el presupuesto termina primero, por lo que la salvaguarda no
decide el resultado.

Así, con la misma instancia, semilla, configuración y `T`, se ejecuta la misma
cantidad de evaluaciones y se obtiene la misma decisión, independientemente de
pequeñas variaciones en la velocidad de la computadora.

#### Calibración de parámetros

**Qué se calibró.** Los tres parámetros del algoritmo evolutivo: tamaño de la
población, tamaño del torneo y probabilidad de cruce. Los pesos de la aptitud
y los presupuestos de trabajo no entran en este barrido: los primeros replican
el orden del concurso y los segundos se fijaron con el procedimiento de la
sección 2.4.

**Procedimiento.** Los valores base (población 20, torneo 3, cruce 0.70) se
habían fijado como decisión de diseño antes de calibrar. El barrido los somete
a prueba: se evalúa la base y seis variantes, y cada variante cambia un solo
parámetro y deja los otros dos en su valor base.

| Parámetro | Valores probados | Base |
|---|---|---|
| Tamaño de población | 10, 20, 40 | 20 |
| Tamaño del torneo | 2, 3, 5 | 3 |
| Probabilidad de cruce | 0.50, 0.70, 0.90 | 0.70 |

La regla de elección se fijó **antes** de ver los resultados: gana la
configuración con menor media de celdas ocupadas; ante empate gana la base, y
entre variantes empatadas, la de menor tiempo medio.

Para no ajustar los parámetros sobre los mismos datos del informe, el barrido
usa tres instancias de calibración cuya configuración (N, K, M) no coincide con
ninguna de las baterías formales: (4, 3, 12), (5, 3, 20) y (6, 4, 30), con
semillas pareadas 101, 102 y 103 y `T = 10 s`. Son 7 configuraciones × 3
instancias × 3 semillas = 63 corridas. Todas pasaron por el validador
independiente (63 de 63 válidas) y ninguna activó la salvaguarda del reloj.

**Resultados.** Los valores son media ± desviación estándar muestral entre las
nueve corridas de cada configuración.

| Configuración | Celdas ocupadas | Mín–máx | Tiempo medio |
|---|---|---|---|
| base (20 / 3 / 0.70) | 3.33 ± 0.50 | 3–4 | 4.16 ± 0.43 s |
| población = 10 | 3.33 ± 0.50 | 3–4 | 4.24 ± 0.49 s |
| población = 40 | 3.33 ± 0.50 | 3–4 | 4.25 ± 0.37 s |
| torneo = 2 | 3.33 ± 0.50 | 3–4 | 4.21 ± 0.44 s |
| torneo = 5 | 3.33 ± 0.50 | 3–4 | 4.15 ± 0.44 s |
| cruce = 0.50 | 3.44 ± 0.73 | 3–5 | 4.21 ± 0.57 s |
| cruce = 0.90 | 3.44 ± 0.73 | 3–5 | 4.12 ± 0.42 s |

Desglose por instancia de calibración (celdas ocupadas):

| Instancia | Todas las configuraciones, salvo |
|---|---|
| (4, 3, 12), semillas 101–103 | Ninguna: todas dejaron 3. |
| (5, 3, 20), semillas 101–103 | Ninguna: todas dejaron 3. |
| (6, 4, 30), semillas 101–103 | Dejaron 4, salvo cruce = 0.50 y cruce = 0.90 en la semilla 103, que dejaron 5. |

**Lectura.** La configuración base resultó ganadora, pero conviene precisar por
qué. Las cinco configuraciones de población y torneo empataron exactamente con
la base, y la regla de desempate favorece a la base. Las dos variantes de cruce
quedaron ligeramente peor en media, y esa diferencia proviene de **dos
corridas** (una por variante, en la misma instancia). Lo que muestra el barrido
es que, en estas instancias, el agente es poco sensible a los tres parámetros;
no demuestra que la base sea óptima. El tiempo medio no distingue
configuraciones: el presupuesto de evaluaciones es el mismo para todas (11110.7
evaluaciones de media) y las diferencias de décimas de segundo están dentro de
la desviación observada. Por eso se conservó la base y no se rehicieron las
baterías formales.

**Limitaciones de la calibración.** El barrido cambia un parámetro a la vez, de
modo que no explora interacciones entre parámetros. Cada configuración se
evaluó con nueve corridas, en instancias donde la mayoría de las
configuraciones empatan, así que su poder para distinguir configuraciones es
limitado. Es un procedimiento explícito y reproducible, no una optimización
exhaustiva. Se reproduce con:

```text
python -m experimentos.calibracion_evolutivo
```

Los resultados están en `resultados/experimentos/calibracion_evolutivo/`
(`crudo.csv`, `resumen.csv` y `metadatos.json`).

#### Exploración previa del presupuesto

Antes de la calibración formal se hicieron pruebas informales, que se conservan
solo como contexto y no forman parte de las baterías formales ni de la
calibración.

En esas instancias exploratorias, las configuraciones finalistas empataron en
los dos criterios de calidad: fichas colocadas y celdas ocupadas. Algunas
mostraron tiempos ligeramente menores, pero la diferencia fue menor que la
variación observada entre corridas; por eso se interpreta como ruido de
medición y no como evidencia de que una configuración sea más rápida.

También se evaluó si el empate podía deberse a que el presupuesto de
evaluaciones fuera demasiado corto. Para el finalista `aleatorio_014` se
repitieron las mismas tres configuraciones y semillas 1--3 con límites de 20 y
40 segundos, frente a la referencia de 10 segundos. Las 18 corridas adicionales
fueron legales, no activaron la salvaguarda del reloj y conservaron la misma
calidad observada a 10 segundos: todas colocaron la secuencia completa y
terminaron con tres celdas ocupadas. El tiempo promedio aumentó a 8.9 s y
17.7 s, respectivamente, sin mejorar esos criterios.

Para ese conjunto acotado, el presupuesto de 10 segundos no parece explicar
el empate: el agente ya encuentra esa calidad antes de agotarlo. En instancias
más difíciles podría ocurrir lo contrario; para afirmarlo harían falta nuevas
pruebas pareadas con presupuestos mayores.

## 2. Metodología

### 2.1 Qué exige el enunciado y qué decidimos nosotros

| Elemento | Origen |
|---|---|
| Ambos agentes sobre el mismo conjunto de instancias | Enunciado |
| Al menos 6 configuraciones de N, K y M, con al menos 3 semillas cada una | Enunciado |
| Fichas colocadas, celdas ocupadas y tiempo | Enunciado |
| Escalabilidad: al menos 3 tamaños de tablero y 3 cantidades de colores | Enunciado |
| Parámetros del evolutivo documentados con el procedimiento por el que se fijaron | Enunciado |
| Límite de tiempo `T = 10 s` común a todas las corridas | Decisión nuestra, tras el piloto |
| Semillas pareadas `s = 1, 2, 3` | Decisión nuestra |
| Cantidad de fichas en cada tamaño de tablero | Decisión nuestra |
| Densidad de fichas `rho = M / N²` en escalabilidad | Decisión nuestra |
| Las seis configuraciones de la comparación | Decisión nuestra, tras el piloto |
| Cantidad de trabajo que usa cada agente | Decisión nuestra (ver 2.4) |
| Parámetros del evolutivo (población, torneo, cruce) | Decisión nuestra, sometidos a barrido (ver 1.2) |
| Instancias y semillas de la calibración | Decisión nuestra, distintas de las baterías formales |

### 2.2 Instancias y semillas

Todas las instancias las produce el generador del proyecto
(`python main.py generar`). Son resolubles por construcción: el generador juega
una partida legal completa mientras inventa la secuencia.

Para cada semilla usamos exactamente la misma instancia con los dos agentes.
Así, cuando los comparamos, la diferencia viene del agente y no de un tablero
distinto.

### 2.3 Métricas

| Columna | Significado |
|---|---|
| `tiles_placed` | Fichas colocadas. Primer criterio del concurso. |
| `occupied_cells` | Celdas ocupadas al terminar. Segundo criterio del concurso. |
| `elapsed_s` | Tiempo de planificación del agente, en segundos. Tercer criterio. |
| `complete` | La solución final consumió la secuencia completa. |
| `search_cutoff` | Solo A*: la búsqueda se detuvo antes de llegar a la meta y luego completó la partida con su regla sencilla. |
| `clock_safeguard` | El reloj de protección detuvo al agente antes de terminar su trabajo previsto. |

Una partida puede aparecer como completa aunque A* haya llegado a su límite,
porque en ese caso coloca las fichas restantes con su regla sencilla.

### 2.4 Cómo respetamos el tiempo

El enunciado pide respetar el tiempo y obtener el mismo resultado cuando la
entrada y la semilla son iguales. Por eso ambos agentes usan una cantidad fija
de trabajo. El reloj solo actúa como protección si la máquina tarda más de lo
esperado.

| Agente | Trabajo máximo con `T = 10 s` | Salvaguarda |
|---|---|---|
| `busqueda_astar` | `min(120000, floor(2200 × T))` opciones; con `T = 10`, son 22000 | 85 % de `T` |
| `evolutivo` | `floor(200000 / M)` propuestas; hay menos cuando hay más fichas | 98 % de `T` |

La salvaguarda no decide cuántas opciones revisa el agente: el presupuesto de
la tabla es el que mantiene el resultado repetible. El reloj solo lo detiene si
la computadora está tardando más de lo esperado, dejando tiempo para guardar
una solución válida. Si ocurre, queda registrado como `clock_safeguard = True`
y esa corrida no se usa para demostrar que el resultado se puede repetir.

### 2.5 Validez de las corridas

Cada corrida pasó por el validador independiente (`main.py validar`). Una
corrida cuenta como válida solo si el validador acepta la solución y además las
fichas colocadas, celdas ocupadas y ficha mayor que informó el agente coinciden
con las que reproduce el validador.

| Experimento | Corridas | Soluciones válidas |
|---|---|---|
| Comparación | 36 | 36 |
| Escalabilidad | 54 | 54 |
| Calibración del evolutivo | 63 | 63 |

Ninguna corrida excedió el tiempo límite ni activó la salvaguarda.

### 2.6 Entorno

Las pruebas se ejecutaron de forma secuencial en una misma computadora. Los
datos técnicos del entorno están en `metadatos.json` de cada experimento.

## 3. Comparación experimental

### 3.1 Configuraciones

Elegimos seis casos de prueba de distintos tamaños y cantidades de fichas. En
algunos A* logra explorar una partida completa; en otros llega a su límite y
termina con su regla sencilla.

| Configuración | Tamaño | Colores | Fichas |
|---|---|---|---|
| n3_k4_m14 | 3×3 | 4 | 14 |
| n4_k4_m8 | 4×4 | 4 | 8 |
| n4_k2_m16 | 4×4 | 2 | 16 |
| n5_k2_m13 | 5×5 | 2 | 13 |
| n5_k4_m25 | 5×5 | 4 | 25 |
| n6_k4_m36 | 6×6 | 4 | 36 |

Son 6 configuraciones × 3 semillas × 2 agentes = 36 corridas.

### 3.2 Resultados

La tabla muestra el resultado de las tres partidas de cada caso. Los dos
agentes colocaron todas las fichas en todos ellos.

| Tamaño | Colores | Fichas | Celdas ocupadas: A* | Celdas ocupadas: evolutivo | Tiempo: A* | Tiempo: evolutivo |
|---|---|---|---|---|---|---|
| 3×3 | 4 | 14 | 3.67 ± 0.58 | 3.67 ± 0.58 | 0.40 ± 0.36 s | 4.20 ± 0.31 s |
| 4×4 | 4 | 8 | 3 ± 0 | 3 ± 0 | 2.12 ± 1.92 s | 5.63 ± 0.18 s |
| 4×4 | 2 | 16 | 4.67 ± 1.53 | 2 ± 0 | 3.07 ± 0.14 s | 4.78 ± 0.27 s |
| 5×5 | 2 | 13 | 5.67 ± 0.58 | 2 ± 0 | 6.19 ± 0.56 s | 5.64 ± 0.30 s |
| 5×5 | 4 | 25 | 16 ± 1 | 4 ± 0 | 2.05 ± 0.31 s | 4.96 ± 0.26 s |
| 6×6 | 4 | 36 | 26.67 ± 2.52 | 4.33 ± 0.58 | 2.31 ± 0.31 s | 5.36 ± 0.31 s |

Los valores son media ± desviación estándar muestral entre las tres semillas;
mínimos y máximos están en `resumen.csv`.

![Calidad y tiempo](resultados/experimentos/comparacion/graficas/comparacion_calidad_y_tiempo.png)

### 3.3 Lo que vimos

- Los dos agentes lograron colocar todas las fichas en las 36 partidas. Por eso,
  en estas pruebas la diferencia importante es cuántas celdas quedaron
  ocupadas al final.
- En 4 de las 6 configuraciones el evolutivo dejó menos celdas ocupadas en
  promedio (4×4 con 2 colores, 5×5 con 2 colores, 5×5 con 4 colores y 6×6). En
  las otras 2 (3×3 con 4 colores y 4×4 con 4 colores) los promedios coinciden.
  En ninguna configuración quedó por detrás.
- En las configuraciones donde A* terminó su búsqueda, o la cortó en muy pocas
  partidas, ambos obtuvieron el mismo resultado. Cuando el tablero fue más
  difícil y A* tuvo que detenerse antes, el evolutivo dejó mejores tableros
  finales.
- A* fue mucho más rápido en los casos pequeños que pudo resolver por completo.
  El evolutivo tardó unos pocos segundos de forma más pareja.

### 3.4 Lectura de la comparación

En estas pruebas no hay un ganador absoluto. A* es una muy buena opción para
tableros pequeños: encuentra una buena respuesta rápidamente. En los tableros
más grandes de la batería, el evolutivo conservó mejor la calidad de la
respuesta, aunque tardó más. Esta conclusión aplica solamente a los tamaños y
tiempos probados aquí.

### 3.5 Variación entre partidas

Cambiar la semilla puede cambiar qué tan difícil resulta una partida concreta,
especialmente para A*: su desviación en celdas ocupadas llega a 2.52 en 6×6,
mientras que la del evolutivo no supera 0.58 en ninguna configuración. Aun así,
la tendencia general se mantuvo: el evolutivo fue igual o mejor en celdas
ocupadas y A* fue más rápido cuando pudo terminar su búsqueda.

## 4. Escalabilidad

### 4.1 Cómo hicimos las pruebas

Probamos tableros de 3×3, 4×4 y 5×5, con 2, 3 y 4 colores. Para cada caso se
usaron tres partidas distintas y se compararon ambos agentes en las mismas
partidas.

Para que la comparación de escalabilidad fuera razonable, no mantuvimos fija
la cantidad de fichas `M` al cambiar el tamaño del tablero. En su lugar,
mantuvimos aproximadamente constante la densidad de fichas:

```text
rho = M / N²
```

Aquí `N²` es la cantidad total de celdas del tablero y `M` es la cantidad de
fichas que deben colocarse. Por ejemplo, `rho = 0.5` significa que la
secuencia tiene aproximadamente media ficha por cada celda disponible. Así,
un tablero grande recibe más fichas que uno pequeño, pero conserva una carga
relativa parecida. Si hubiéramos usado siempre el mismo `M`, el tablero grande
habría quedado artificialmente vacío y la comparación mediría sobre todo esa
diferencia de carga.

Como `M` debe ser un número entero, usamos la fórmula de redondeo al entero más
cercano:

```text
rho = M / N² = 0.5
M = floor(0.5 × N² + 0.5)
```

El `+ 0.5` antes de aplicar `floor` implementa ese redondeo. Por eso:

| Tamaño | Celdas `N²` | Cálculo | Fichas `M` | Densidad real |
|---|---:|---:|---:|---:|
| 3×3 | 9 | `floor(4.5 + 0.5)` | 5 | `5/9 ≈ 0.56` |
| 4×4 | 16 | `floor(8 + 0.5)` | 8 | `8/16 = 0.50` |
| 5×5 | 25 | `floor(12.5 + 0.5)` | 13 | `13/25 = 0.52` |

Las densidades reales quedan cerca de `0.5`, aunque no pueden ser exactamente
iguales en todos los tamaños porque `M` es entero. De esta manera, al aumentar
`N`, aumentan tanto el espacio de búsqueda como la cantidad de fichas, sin que
la instancia grande sea trivial por tener muy pocas fichas.

Además, `rho = 0.5` deja aproximadamente la mitad de las celdas libres antes
de considerar las fusiones. Esa holgura evita que una partida falle únicamente
porque el tablero se llenó; si una corrida termina antes, la causa puede
atribuirse al comportamiento del agente o de la instancia, no a haber elegido
una cantidad de fichas cercana a la capacidad máxima del tablero.

### 4.2 Resultados

Todos los casos se jugaron completos. La tabla conserva los resultados
necesarios para comparar la calidad final, el tiempo y si A* alcanzó a terminar
su búsqueda.

| Tamaño | Colores | Fichas | Ocupadas: A* | Ocupadas: evolutivo | Tiempo: A* | Tiempo: evolutivo | A* terminó su búsqueda |
|---|---|---|---|---|---|---|---|
| 3×3 | 2 | 5 | 2 ± 0 | 2 ± 0 | 0.09 ± 0.14 s | 5.57 ± 0.17 s | 3 de 3 |
| 3×3 | 3 | 5 | 2.67 ± 0.58 | 2.67 ± 0.58 | 0.12 ± 0.18 s | 5.37 ± 0.08 s | 3 de 3 |
| 3×3 | 4 | 5 | 2.67 ± 0.58 | 2.67 ± 0.58 | 0.16 ± 0.11 s | 5.53 ± 0.11 s | 3 de 3 |
| 4×4 | 2 | 8 | 2 ± 0 | 2 ± 0 | 2.07 ± 1.73 s | 5.73 ± 0.20 s | 3 de 3 |
| 4×4 | 3 | 8 | 3 ± 0 | 3 ± 0 | 4.21 ± 0.63 s | 5.59 ± 0.39 s | 1 de 3 |
| 4×4 | 4 | 8 | 3 ± 0 | 3 ± 0 | 2.10 ± 1.87 s | 5.60 ± 0.23 s | 2 de 3 |
| 5×5 | 2 | 13 | 5.67 ± 0.58 | 2 ± 0 | 6.21 ± 0.65 s | 5.58 ± 0.17 s | 0 de 3 |
| 5×5 | 3 | 13 | 6.67 ± 1.15 | 3 ± 0 | 5.71 ± 0.56 s | 6.12 ± 0.55 s | 0 de 3 |
| 5×5 | 4 | 13 | 8.33 ± 0.58 | 3.67 ± 0.58 | 5.16 ± 0.45 s | 5.87 ± 0.21 s | 0 de 3 |

Los valores son media ± desviación estándar muestral entre las tres semillas;
mínimos y máximos están en `resumen.csv`.

![Escalabilidad frente a N](resultados/experimentos/escalabilidad/graficas/escalabilidad_vs_n.png)

### 4.3 Qué pasó al agrandar el tablero

La gráfica resume la tendencia principal. En los tableros de 3×3, A* terminó
su búsqueda en todas las partidas y respondió muy rápido. En 4×4 empezó a
quedarse sin tiempo en algunas partidas. En 5×5 tuvo que detenerse antes en
todas ellas.

Cuando A* se detenía antes, todavía podía dar una jugada válida, pero dejaba
más celdas ocupadas. Por ejemplo, en los casos de 5×5 el evolutivo dejó entre 2
y 4 celdas ocupadas, mientras que A* dejó entre 6 y 8 aproximadamente. El
evolutivo mantuvo resultados similares al crecer el tablero; en la mayoría de
los casos tardó unos segundos más, aunque en n5_k2_m13 fue ligeramente más
rápido que A* (5.58 s frente a 6.21 s de media).

Los tiempos de n5_k2_m13 difieren levemente de los de la sección 3 (6.19 s y
5.64 s allí) porque provienen de corridas separadas sobre las mismas
instancias: las soluciones son idénticas (mismo hash `solution_sha256` para
cada semilla y agente) y solo varía el tiempo de reloj. La gráfica contra N
está arriba; la gráfica contra K aparece en la sección 4.4.

### 4.4 Qué pasó al usar más colores

![Escalabilidad frente a K](resultados/experimentos/escalabilidad/graficas/escalabilidad_vs_k.png)

Con más colores es más difícil juntar fichas iguales, así que quedan igual o
más celdas ocupadas. El efecto es claro en 5×5: de 2 a 4 colores, A* pasa de
5.67 a 8.33 celdas ocupadas y el evolutivo de 2 a 3.67. En 3×3 y 4×4 el efecto
es pequeño porque ambos agentes ya llegan a la misma solución. En el tiempo no
encontramos una regla igual de clara: depende de la partida concreta.

### 4.5 Resumen de escalabilidad

El tamaño del tablero fue el cambio que más afectó a A*. Le fue muy bien en los
tableros pequeños, pero los grandes superaron el tiempo disponible para explorar
todas las opciones. El evolutivo fue más lento en los casos sencillos, pero
conservó mejores tableros finales en los grandes.

No separamos por completo el efecto de tener un tablero más grande del efecto
de usar más fichas, porque ambas cosas crecieron juntas en esta batería. Las
conclusiones se limitan a los tamaños, colores y tiempo probados.

## 5. Reproducibilidad

Una prueba es reproducible si otra persona puede usar los mismos datos y llegar
al mismo resultado. Para lograrlo, cada partida registra su configuración, la
semilla, el agente y el límite de tiempo. La semilla sirve para generar la misma
instancia y, en el agente evolutivo, para repetir las mismas decisiones
aleatorias. Además, los agentes tienen una cantidad fija de trabajo; así, una
computadora que ejecute la misma prueba no cambia el resultado solo por ser un
poco más rápida o más lenta.

Repetimos partidas con la misma semilla y los agentes entregaron la misma
solución. Las filas de cada ejecución están en `crudo.csv`; los promedios de
cada configuración, en `resumen.csv`; y los datos de la computadora usada, en
`metadatos.json`, dentro de las carpetas de comparación, escalabilidad y
calibración del evolutivo. La calibración se reproduce con
`python -m experimentos.calibracion_evolutivo`.

No hace falta volver a correr los agentes para comprobar que las soluciones
guardadas son legales. El validador reproduce las reglas del juego de manera
independiente y revisa la cantidad de fichas y de celdas ocupadas.

Si el reloj de salvaguarda llegara a intervenir, quedaría marcado en los datos.
Esa partida seguiría siendo válida, pero no se usaría como evidencia de que el
resultado se repite exactamente.

## 6. Limitaciones

- **Rango de pruebas pequeño.** En escalabilidad probamos tableros de 3×3 a
  5×5, entre 2 y 4 colores y tres semillas por configuración. La comparación
  incluye además un caso de 6×6. Esto es suficiente para ver una tendencia,
  pero no para asegurar que se mantenga con tableros mucho mayores, más colores
  o muchas más partidas.
- **No evaluamos derrotas.** Las instancias se construyeron para que siempre
  hubiera una forma de colocar toda la secuencia. De hecho, ambos agentes
  colocaron todas las fichas en las pruebas formales. Por eso pudimos comparar
  bien cuántas celdas quedaban ocupadas, pero no sabemos cuál agente manejaría
  mejor partidas que no se pueden completar.
- **El límite de tiempo influye en la comparación.** A* recibe como máximo
  22000 expansiones y, si no termina, completa la partida con una regla simple.
  El evolutivo siempre parte de propuestas completas y las mejora mientras dura
  su presupuesto. Por tanto, los resultados describen a ambos agentes con el
  límite de 10 segundos y estos presupuestos, no una ventaja universal de uno
  sobre el otro.
- **Calibración acotada.** El barrido cambia un parámetro a la vez, sobre tres
  instancias y tres semillas (nueve corridas por configuración). En esas
  instancias la mayoría de las configuraciones empatan, así que el barrido
  muestra que el agente es poco sensible a población, torneo y cruce, no que
  los valores elegidos sean óptimos. No explora interacciones entre parámetros
  ni configuraciones mayores, y los pesos de la aptitud no se calibraron.
- **Una sola computadora.** Los tiempos se midieron en una sola máquina y son
  útiles para comparar estas corridas entre sí. En otra computadora, el tiempo
  en segundos puede cambiar. El presupuesto fijo reduce ese efecto sobre la
  solución elegida, pero no convierte los tiempos medidos en una medida válida
  para cualquier equipo.