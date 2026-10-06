# TileUp - Agentes de busqueda y evolutivos

Motor del juego TileUp, agentes automaticos que lo resuelven, validador
independiente de soluciones e interfaz grafica para jugar una partida.

Tarea Corta 1 - Inteligencia Artificial (IC-6200) - Instituto Tecnologico de
Costa Rica.

## Equipo

| Integrante | Carne |
|---|---|
| Adriel S. Chaves Salazar | 2021031465 |
| Daniel Duarte Cordero | 2022012866 |
| Sebastian Hernandez Bonilla | 2022093651 |

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior, con Tkinter incluido (viene con el instalador
  oficial de python.org).

```powershell
py --version
```

## Instalacion

Una sola orden crea el entorno virtual, instala las dependencias, corre las
pruebas, resuelve la instancia de ejemplo con los dos agentes y valida ambas
soluciones:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

El parametro `-ExecutionPolicy Bypass` evita el error
`running scripts is disabled on this system` sin cambiar la configuracion de la
maquina. Si se prefiere hacerlo paso a paso:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para activar el entorno:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

A partir de aqui los comandos se escriben como `python`, asumiendo el entorno
activo. Sin activarlo, sustituya `python` por `.venv\Scripts\python.exe`.

## Un punto de entrada, seis subcomandos

Todo el sistema se opera desde `main.py`.

```powershell
python main.py --ayuda-completa
```

| Subcomando | Proposito |
|---|---|
| `resolver` | Resuelve una instancia con uno o varios agentes. |
| `validar` | Valida un archivo de solucion contra su instancia. |
| `jugar` | Abre la ventana de juego para jugar una partida. |
| `instancia` | Revisa el formato de un archivo de instancia. |
| `generar` | Genera un archivo de instancia resoluble. |
| `agentes` | Lista los agentes disponibles. |

Codigos de salida, comunes a todos los subcomandos:

| Codigo | Significado |
|---|---|
| `0` | La operacion termino correctamente. |
| `1` | Veredicto negativo. Solo lo emite `validar` al rechazar una solucion. |
| `2` | Error de entrada: archivo ausente, formato invalido o argumento fuera de rango. |
| `3` | Se solicito un agente que no esta registrado. |

## Subcomando `resolver`

```powershell
python main.py resolver --instancia datos\instancias\ejemplo_n4_k3_m6.txt --agente busqueda_astar --semilla 0 --limite-tiempo 10
```

| Argumento | Obligatorio | Descripcion |
|---|---|---|
| `--instancia` | Si | Ruta del archivo de instancia. |
| `--agente` | Uno de los dos | Un agente. Ver `python main.py agentes`. |
| `--agentes` | Uno de los dos | Varios agentes sobre la misma instancia y semilla. |
| `--semilla` | No (`0`) | Fija toda fuente de azar del agente. |
| `--limite-tiempo` | No (`10`) | Limite de planificacion, en segundos. |
| `--salida` | No | Ruta del archivo de solucion. Solo con `--agente`. |
| `--silencioso` | No | Omite la barra de progreso. |
| `--bitacora` | No | CSV al que se agrega una fila con las metricas. Sin esta opcion no se escribe ningun CSV. |

Salida estandar:

```text
Planificando con 'busqueda_astar' sobre ejemplo_n4_k3_m6  (N=4, K=3, M=6). Limite de tiempo: 10.0 s.
busqueda_astar [##############################] 6/6
agente=busqueda_astar instancia=ejemplo_n4_k3_m6 semilla=0 resultado=victoria colocadas=6/6 ocupadas=3 mayor=6 tiempo_s=0.0625 nodos_expandidos=502
solucion=D:\...\datos\soluciones\busqueda_astar\ejemplo_n4_k3_m6__busqueda_astar__s0.sol
```

Cuando la busqueda agota su presupuesto sin alcanzar la meta, el agente entrega
la mejor solucion encontrada y lo advierte por salida estandar:

```text
Nota: la busqueda se corto antes de alcanzar la meta; la solucion se completo con la politica avida.
```

Si el reloj de salvaguarda detiene a cualquier agente antes de que agote su
presupuesto (ver *Criterio de paro y determinismo*), tambien se advierte:

```text
Advertencia: el reloj de salvaguarda detuvo al agente antes de agotar su presupuesto; la solucion puede depender de la velocidad de la maquina.
```

Cada ejecucion escribe su archivo de solucion e informa sus metricas por salida
estandar. No escribe ningun CSV salvo que se indique `--bitacora RUTA`; en ese
caso agrega a ese archivo una fila con las mismas metricas que imprime, de modo
que la bitacora y la salida estandar nunca difieren.

## Subcomando `validar`

```powershell
python main.py validar --instancia datos\instancias\ejemplo_n4_k3_m6.txt --solucion datos\soluciones\busqueda_astar\ejemplo_n4_k3_m6__busqueda_astar__s0.sol
```

| Argumento | Obligatorio | Descripcion |
|---|---|---|
| `--instancia` | Si | Ruta del archivo de instancia. |
| `--solucion` | Si | Ruta del archivo de solucion a validar. |
| `--exigir-completa` | No | Rechaza la solucion si no consume la secuencia entera. |

Salida estandar:

```text
instancia=ejemplo_n4_k3_m6  (N=4, K=3, M=6)
solucion=ejemplo_n4_k3_m6__busqueda_astar__s0
veredicto=ACEPTADA
colocadas=6/6 ocupadas=3 mayor=6 suma=12
completitud=secuencia_consumida
```

## Subcomando `jugar`

```powershell
python main.py jugar --instancia datos\instancias\ejemplo_n5_k3_m12.txt --jugador adriel --partida 1
```

| Argumento | Obligatorio | Descripcion |
|---|---|---|
| `--instancia` | No | Instancia que se va a jugar. Por defecto `ejemplo_n4_k3_m6.txt`. |
| `--jugador` | No (`humano`) | Nombre que se registra en la bitacora. |
| `--partida` | No (`0`) | Numero de partida, para distinguir intentos repetidos. |

La ventana muestra la ficha pendiente, una barra de progreso y el tablero. Un
clic sobre una celda vacia coloca la ficha ahi. Al terminar, el sistema
escribe el archivo de solucion y agrega una fila a
`resultados/humano/partidas_humanas.csv`.

La interfaz sirve unicamente para jugar: no ofrece forma de ejecutar agentes.

## Subcomando `generar`

Produce un archivo de instancia nuevo a partir de `N`, `K`, `M` y una semilla.
Existe porque la comparacion experimental necesita decenas de instancias y a
mano no es viable.

```powershell
python main.py generar --n 4 --k 3 --m 20 --semilla 1
```

| Argumento | Obligatorio | Descripcion |
|---|---|---|
| `--n` | Si | Lado del tablero. Mayor o igual a 1. |
| `--k` | Si | Cantidad de colores. Mayor o igual a 1. |
| `--m` | Si | Cantidad de fichas de la secuencia. No negativa. |
| `--semilla` | No (`0`) | Fija toda fuente de azar del generador. |
| `--etiqueta` | No (`gen`) | Familia a la que pertenece la instancia. Es el prefijo del nombre. |
| `--salida` | No | Ruta exacta del archivo. Anula la convencion de nombrado. |

Salida estandar:

```text
instancia=gen_s1_n4_k3_m20  (N=4, K=3, M=20)
semilla=1
archivo=datos\instancias\gen_s1_n4_k3_m20.txt
colocaciones_testigo=20 (la instancia se construyo jugando una partida legal completa)
```

Sin `--salida`, el archivo se escribe en `datos/instancias/` con el patron
`<etiqueta>_s<semilla>_n<N>_k<K>_m<M>.txt`. La semilla forma parte del nombre,
de modo que varias semillas de una misma configuracion conviven sin
sobreescribirse:

```powershell
python main.py generar --n 5 --k 3 --m 30 --semilla 1   # gen_s1_n5_k3_m30.txt
python main.py generar --n 5 --k 3 --m 30 --semilla 2   # gen_s2_n5_k3_m30.txt
python main.py generar --n 5 --k 3 --m 30 --semilla 3   # gen_s3_n5_k3_m30.txt
```

La etiqueta sirve para distinguir familias de instancias, igual que `ejemplo` o
`ciega` en las que ya estan versionadas. `--salida` ignora la convencion y
escribe en la ruta exacta que se le indique.

### Papel de la semilla

Todo el azar del generador proviene de un unico generador sembrado con
`--semilla`. Lo que se garantiza es una sola direccion, que es la que el
enunciado exige: **los mismos `N`, `K`, `M` y semilla producen siempre el mismo
archivo, byte a byte**. La direccion contraria no se promete, porque dos
semillas distintas pueden coincidir por azar, sobre todo con `M` pequeno.

El determinismo se sostiene en que el orden de recorrido es fijo, el salto de
linea se escribe como `\n` en cualquier sistema y el archivo no lleva marcas de
tiempo. Los parametros quedan anotados en un comentario de la cabecera, de modo
que cualquier instancia del repositorio se puede regenerar leyendo su primera
linea.

```powershell
python main.py generar --n 4 --k 3 --m 20 --semilla 1 --salida a.txt
python main.py generar --n 4 --k 3 --m 20 --semilla 1 --salida b.txt
fc a.txt b.txt
```

### Como se garantiza que la instancia sea resoluble

Una secuencia enteramente aleatoria con `M` mayor que `N^2` puede ser imposible
para cualquier agente, y entonces la comparacion mediria quien pierde menos en
lugar de quien resuelve mejor. El generador lo evita por construccion: **no
inventa la secuencia y despues comprueba si se puede ganar, sino que juega una
partida legal completa e inventa cada ficha en el momento de colocarla**. La
lista de colocaciones que resulta es un testigo de que la instancia tiene al
menos una solucion.

Que la partida nunca se atasque descansa en una observacion: colocar una ficha
ocupa a lo sumo una celda neta, porque sin fusion ocupa una y con una fusion de
tamano `|G|` se retiran `|G|` celdas y queda una, es decir se liberan `|G| - 1`.
Basta entonces mantener el invariante de que al empezar cada paso quede al menos
una celda vacia, y para eso el generador aplica una sola regla especial:

- Con dos o mas celdas vacias, la eleccion es libre: celda al azar y color
  uniforme en `1..K`.
- Con **una sola celda vacia y fichas todavia pendientes**, colocar sin fusion
  llenaria el tablero y perderia la partida. El generador copia entonces el
  color de un vecino de esa celda. Como es la unica vacia, todos sus vecinos
  estan ocupados, de modo que `|G| >= 2`, la fusion libera `|G| - 1 >= 1` celdas
  y el invariante se restablece.
- Con una sola celda vacia y siendo esa la ultima ficha, se coloca y se gana.

La regla de fusion no se reescribe en el generador: la aplica `MotorTileUp`, el
mismo motor que usan el jugador humano y los agentes. El unico caso que el
generador rechaza es `N = 1` con `M > 1`, porque una celda sin vecinos nunca
puede fusionar.

Los valores de las fichas son enteros uniformes en `1..9`. El enunciado solo
exige que sean positivos; un solo digito mantiene el archivo legible y la fusion
ya se encarga de que aparezcan valores grandes durante la partida.

## Subcomandos `instancia` y `agentes`

```powershell
python main.py instancia --instancia datos\instancias\ejemplo_n4_k3_m6.txt
python main.py agentes
```

## Pruebas

```powershell
python -m pytest pruebas -v
```

Las pruebas unitarias verifican el motor de forma aislada, con los casos que
el enunciado exige: fusion de dos fichas, fusion de una componente de tres o
mas, colocacion sin fusion y deteccion de derrota. Las pruebas de integracion
resuelven una instancia pequena de principio a fin, comprueban el determinismo
de la semilla y verifican con el validador que la solucion producida es legal.

## Experimentacion

Dos baterias formales y una calibracion, descritas en archivos de configuracion
o guiones versionados. Todas las corridas de las baterias pasan por la linea de
comandos real (`generar`, `resolver`, `validar`); los guiones de `experimentos/`
no reimplementan nada del juego. Los resultados y su interpretacion estan en
`INFORME.md`.

| Bateria | Objetivo | Configuraciones | Corridas |
|---|---|---|---|
| `comparacion` | Comparar ambos agentes sobre las mismas instancias, como exige el enunciado. | (N, K, M) = (3,4,14), (4,4,8), (4,2,16), (5,2,13), (5,4,25), (6,4,36) | 6 × 3 semillas × 2 agentes = 36 |
| `escalabilidad` | Estudiar como crece el costo con N y con K. | N ∈ {3,4,5} × K ∈ {2,3,4}, con M = floor(0.5·N² + 0.5) | 9 × 3 semillas × 2 agentes = 54 |

- **Agentes:** `busqueda_astar` y `evolutivo`.
- **Limite de tiempo:** `T = 10 s`, el mismo para todas las corridas.
- **Semillas pareadas `s = 1, 2, 3`:** la semilla `s` genera la instancia y esa
  misma `s` se entrega al agente. Ambos agentes corren sobre el mismo archivo.
- **`rho = M / N^2`:** es una decision metodologica del grupo, no un requisito
  del enunciado.
- **Validez:** una corrida solo es valida si termina `ok`, el validador la
  acepta, sus metricas coinciden con las del validador y `clock_safeguard` es
  `False` (ver *Criterio de paro y determinismo*).

Comandos, desde la raiz y en este orden:

```powershell
python -m experimentos.bateria experimentos/configuracion/comparacion.json
python -m experimentos.bateria experimentos/configuracion/escalabilidad.json
python -m experimentos.revalidar comparacion
python -m experimentos.revalidar escalabilidad
python -m experimentos.resumen comparacion
python -m experimentos.resumen escalabilidad
python -m experimentos.graficas comparacion
python -m experimentos.graficas escalabilidad
python -m experimentos.calibracion_evolutivo
```

`bateria` y `calibracion_evolutivo` no sobrescriben un `crudo.csv` existente
salvo que se agregue `--sobrescribir`; hacerlo reemplaza resultados
versionados, asi que solo debe hacerse a proposito. `revalidar`, `resumen` y
`graficas` solo leen el CSV crudo: no vuelven a ejecutar los agentes.

### Calibracion del evolutivo

Los parametros del agente evolutivo (tamano de poblacion, tamano de torneo y
probabilidad de cruce) se someten a un barrido de un parametro a la vez.

Procedimiento, fijado antes de ver los resultados:

1. Se parte de la configuracion base: poblacion 20, torneo 3, cruce 0.70. Estos
   valores se habian fijado como decision de diseno antes de calibrar.
2. Se evalua la base y seis variantes. Cada variante cambia un solo parametro:
   poblacion 10 o 40, torneo 2 o 5, cruce 0.50 o 0.90.
3. Todas se corren sobre tres instancias de calibracion, con configuraciones
   (N, K, M) = (4,3,12), (5,3,20) y (6,4,30), que no coinciden con ninguna de
   las baterias formales. Semillas pareadas 101, 102 y 103 y `T = 10 s`.
   Son 7 × 3 × 3 = 63 corridas.
4. Gana la configuracion con menor media de celdas ocupadas. Ante empate gana la
   base y, entre variantes empatadas, la de menor tiempo medio.

Los pesos de la aptitud (100/10/25) no se barren: replican el orden del
concurso, primero fichas colocadas y luego celdas ocupadas.

Resultado: las 63 corridas fueron validas por el validador independiente y
ninguna activo la salvaguarda del reloj.

| Configuracion | Celdas ocupadas (media ± desv.) | Min-max | Tiempo medio |
|---|---|---|---|
| base (20 / 3 / 0.70) | 3.33 ± 0.50 | 3-4 | 4.16 s |
| poblacion = 10 | 3.33 ± 0.50 | 3-4 | 4.24 s |
| poblacion = 40 | 3.33 ± 0.50 | 3-4 | 4.25 s |
| torneo = 2 | 3.33 ± 0.50 | 3-4 | 4.21 s |
| torneo = 5 | 3.33 ± 0.50 | 3-4 | 4.15 s |
| cruce = 0.50 | 3.44 ± 0.73 | 3-5 | 4.21 s |
| cruce = 0.90 | 3.44 ± 0.73 | 3-5 | 4.12 s |

La configuracion base resulto ganadora y se conservo. Las cinco configuraciones
de poblacion y torneo empataron con ella, y la diferencia de las de cruce
proviene de dos corridas. El barrido muestra que, en estas instancias, el agente
es poco sensible a los tres parametros; no demuestra que la base sea optima. No
explora interacciones entre parametros y cada configuracion se evaluo con nueve
corridas. Al conservarse los valores, no fue necesario rehacer las baterias
formales.

### Donde quedan los resultados

| Ruta | Contenido |
|---|---|
| `experimentos/configuracion/*.json` | Configuracion de cada bateria: configuraciones, semillas, agentes y limite. |
| `datos/instancias/<bateria>_s<s>_n<N>_k<K>_m<M>.txt` | Instancias generadas. |
| `datos/instancias/calibracion_s<s>_n<N>_k<K>_m<M>.txt` | Instancias de la calibracion del evolutivo. |
| `datos/soluciones/<agente>/<instancia>__<agente>__s<s>.sol` | Soluciones producidas. |
| `resultados/experimentos/<bateria>/crudo.csv` | Una fila por corrida. **Es la fuente primaria de verdad.** |
| `resultados/experimentos/<bateria>/resumen.csv` | Por configuracion y agente: media, desviacion estandar, minimo y maximo entre semillas. |
| `resultados/experimentos/<bateria>/registros.jsonl` | Comandos, stdout y stderr completos de cada corrida. |
| `resultados/experimentos/<bateria>/metadatos.json` | Commit, maquina, Python y huellas de la configuracion y de los guiones. |
| `resultados/experimentos/<bateria>/graficas/*.png` | Graficas generadas desde el CSV crudo. |
| `resultados/experimentos/calibracion_evolutivo/` | `crudo.csv` (una fila por corrida), `resumen.csv` (por configuracion) y `metadatos.json` de la calibracion. |

Columnas principales de `crudo.csv` de las baterias:

| Columna | Significado |
|---|---|
| `instance_seed`, `agent_seed` | Semilla de la instancia y del agente. Coinciden por diseno, pero cumplen funciones distintas. |
| `status` | `ok`, `rejected`, `mismatch`, `agent_error`, `killed` o `validator_error`. |
| `validated` | El validador independiente acepto la solucion. |
| `tiles_placed`, `occupied_cells`, `largest_tile` | Metricas que informa el agente. |
| `validator_tiles`, `validator_occupied`, `validator_largest` | Las mismas metricas, reproducidas por el validador. |
| `elapsed_s` | Tiempo de planificacion del agente, en segundos. |
| `effort`, `effort_type` | `expanded_nodes` (A*) o `fitness_evaluations` (evolutivo). Unidades distintas, no comparables entre si. |
| `complete` | La solucion consumio toda la secuencia. |
| `search_cutoff` | Solo A*: la busqueda termino sin alcanzar la meta y la partida se completo de forma avida. |
| `clock_safeguard` | El reloj de salvaguarda actuo antes que el presupuesto; la corrida no seria reproducible. |
| `solution_path`, `solution_sha256` | Solucion producida y su huella, para comprobar reproducibilidad. |

La carpeta `resultados/experimentos/` conserva ademas evidencia historica que
**no** forma parte de los resultados formales:

- el piloto con el que se eligieron las configuraciones (`piloto/`);
- las pruebas de determinismo con el criterio de paro anterior (`determinismo/`,
  `determinismo_diagnostico/`) y con el actual (`determinismo_presupuesto_*`);
- la comprobacion del evolutivo con presupuesto (`comprobacion_evolutivo/`);
- las baterias interrumpidas al detectar el problema de determinismo
  (`*_criterio_reloj/`).

## Reglas del juego

- El tablero es una cuadricula de `N x N` celdas, inicialmente vacia.
- Una ficha es un par `<color, valor>`, con el color en el rango `1..K`.
- En cada paso se toma la primera ficha pendiente y se coloca en cualquier
  celda vacia. No hay gravedad ni restriccion de columna, por lo que el factor
  de ramificacion de un estado con `e` celdas vacias es exactamente `e`.
- Tras colocar la ficha en la celda `p`, se calcula `G`, la componente conexa
  maximal del mismo color que contiene a `p` por vecindad ortogonal. Si
  `|G| >= 2`, todas las fichas de `G` se retiran y en `p` queda una unica ficha
  del mismo color cuyo valor es la suma de los valores de `G`.
- La fusion no encadena: como `G` es maximal, la ficha resultante no puede
  quedar adyacente a otra del mismo color.
- La partida se gana al colocar las `M` fichas de la secuencia. Se pierde
  cuando queda al menos una ficha pendiente y el tablero esta lleno.

## Formato de entrada

Archivo de texto plano. Las lineas en blanco se ignoran y todo lo que sigue a
un caracter `#` se descarta hasta el fin de linea. El orden de lectura es:
una linea con `N` y `K`, una linea con `M`, y luego `M` lineas con el color y
el valor de cada ficha.

```text
# TileUp -- instancia de ejemplo
4 3        # tablero 4x4, 3 colores
6          # 6 fichas en la secuencia
1 2
2 1
1 3
3 1
1 1
2 4
```

Un archivo mal formado produce un mensaje de error legible con el numero de
linea afectado y un codigo de salida distinto de cero, nunca una traza de
excepcion sin controlar.

## Formato de salida

Una linea por colocacion, en el orden de la secuencia, con el indice de la
ficha (desde cero), la fila y la columna (ambas desde cero). La ultima linea
comienza con `#` y resume el resultado.

```text
0 0 0
1 1 1
2 0 1
3 2 2
4 0 2
5 1 2
# colocadas=6 ocupadas=3 mayor=6
```

El archivo se escribe siempre, aun cuando la partida termine en derrota, con
las colocaciones que el agente alcanzo a realizar.

## Convencion de nombrado

| Directorio | Patron |
|---|---|
| `datos/instancias/` (generadas) | `<etiqueta>_s<semilla>_n<N>_k<K>_m<M>.txt` |
| `datos/instancias/` (escritas a mano) | `<etiqueta>_n<N>_k<K>_m<M>.txt` |
| `datos/soluciones/<agente>/` | `<instancia>__<agente>__s<semilla>.sol` |
| `resultados/humano/` | `partidas_humanas.csv` |
| `resultados/experimentos/` | `comparacion_agentes.csv` (registro historico de corridas sueltas) |

Todo en minusculas, sin espacios ni caracteres especiales del espanol. El
modulo `src/nombrado/nombres_archivos.py` es la unica fuente de estos
patrones.

El nombre de una instancia generada lleva su semilla, para que la bateria
experimental pueda correr varias semillas por configuracion sin que una
sobreescriba a la anterior. Las instancias escritas a mano no tienen semilla
y por eso omiten ese campo.

Los agentes de busqueda son todos el mismo algoritmo A*; lo unico que cambia
entre ellos es la heuristica. Por eso su nombre sigue el patron
`busqueda_<heuristica>`, de modo que el nombre del agente, el directorio de
soluciones y el nombre de la heuristica digan siempre lo mismo.

## Organizacion del repositorio

```text
main.py            Punto de entrada unico, con seis subcomandos.
setup.ps1          Preparacion y verificacion del entorno en una sola orden.

src/dominio/       Reglas puras del juego: ficha, tablero, estado y motor.
src/instancias/    Lectura, escritura y generacion del formato de entrada.
src/soluciones/    Acumulacion y escritura del formato de salida.
src/partidas/      Orquestacion de partidas, observadores y ejecutor.
src/agentes/       Contrato de agente, heuristicas y agentes concretos.
src/validacion/    Reimplementacion independiente de las reglas y arbitraje.
src/metricas/      Metricas reportables y bitacoras de resultados.
src/nombrado/      Convenciones de nombrado de archivos.
src/cli/           Subcomandos y ejecucion por consola.
src/gui/           Ventana de juego humano.

pruebas/           Pruebas unitarias y de integracion.

experimentos/      Guiones de las baterias, la calibracion y sus configuraciones.
INFORME.md         Formulacion de los agentes, calibracion y resultados.
```

Flujo de datos:

```text
datos/instancias/*.txt               ENTRADA de los agentes y del jugador.
datos/soluciones/humano/             SALIDA de las partidas humanas.
datos/soluciones/aleatorio/          SALIDA del agente de linea base.
datos/soluciones/busqueda_astar/     SALIDA de A* con heuristica admisible.
datos/soluciones/busqueda_dijkstra/  SALIDA de A* con h = 0.
datos/soluciones/evolutivo/          SALIDA del agente evolutivo.
resultados/humano/                   Bitacora de partidas humanas.
resultados/experimentos/<bateria>/   Resultados de cada bateria experimental.
resultados/experimentos/calibracion_evolutivo/
                                     Resultados de la calibracion del evolutivo.
resultados/experimentos/comparacion_agentes.csv
                                     Registro historico de corridas sueltas.
```

## Agentes disponibles

| Nombre | Algoritmo | Medida de esfuerzo |
|---|---|---|
| `aleatorio` | Coloca cada ficha en una celda vacia al azar. Linea base inferior. | `colocaciones_evaluadas` |
| `busqueda_astar` | A* con la heuristica admisible de colores pendientes. Es el agente de busqueda del enunciado. | `nodos_expandidos` |
| `busqueda_dijkstra` | A* con `h = 0`, es decir Dijkstra. Linea base para medir el aporte de la heuristica. | `nodos_expandidos` |
| `evolutivo` | Algoritmo genetico de estado estacionario con mutacion guiada. | `evaluaciones_aptitud` |

Agregar un agente consiste en implementar la interfaz `Agente` e inscribirlo
en `RegistroAgentes`. Ningun otro archivo del sistema cambia.

## Validador independiente

El validador reimplementa las reglas por su cuenta en
`src/validacion/verificador_reglas.py`, con listas de Python y un recorrido en
profundidad con pila explicita, en lugar de reusar el motor de
`src/dominio/motor.py`, que usa NumPy y un recorrido en anchura. No hereda por
tanto los posibles errores del motor y sirve de contraste real. Tampoco
comparte codigo de decision con ningun agente: no elige donde colocar nada.

Comprueba cinco cosas:

1. Los indices de ficha son consecutivos desde cero y en orden.
2. Cada colocacion cae dentro del tablero y sobre una celda vacia.
3. La partida no continua despues de haberse perdido.
4. La suma de valores del tablero coincide con la suma de las fichas
   colocadas. Este invariante se cumple siempre porque la fusion conserva la
   suma, y es una prueba barata de que la reproduccion fue fiel.
5. El resumen declarado en el archivo coincide con lo verificado.

Una solucion incompleta no es ilegal: el enunciado obliga a escribir la
solucion aun cuando la partida termine en derrota. El dictamen distingue
legalidad de completitud.

## Agente de busqueda: A*

### Formulacion del problema

| Elemento | Definicion |
|---|---|
| Estado | Par `<tablero, i>`: configuracion de N x N celdas e indice de la proxima ficha. |
| Estado inicial | Tablero vacio, `i = 0`. |
| Operador de sucesion | Colocar la ficha `i` en cualquier celda vacia, aplicando la fusion. |
| Factor de ramificacion | Exactamente la cantidad de celdas vacias. |
| Costo de accion | `(N^2 - 1) - liberadas(a)`, con `liberadas(a) = \|G\| - 1`. |
| Prueba de meta | `i == M`. |

La funcion de costo se eligio con dos condiciones simultaneas.

**No negatividad.** A* pierde sus garantias con costos negativos. El costo
"natural" seria el cambio en celdas ocupadas, que vale `1 - |G|` y es negativo
en cuanto hay fusion. Restar las liberaciones de una constante lo arregla.

**Exactitud respecto al objetivo.** Todo camino meta tiene exactamente `M`
acciones y `suma(liberadas) = M - ocupadas_finales`, de modo que
`g_total = M(N^2 - 2) + ocupadas_finales`. El termino constante es identico
para todos los caminos meta, asi que **minimizar `g` equivale exactamente a
minimizar las celdas ocupadas al terminar**, que es el segundo criterio de
desempate del concurso.

### Estructuras del algoritmo

La implementacion sigue el pseudocodigo de A* sobre grafos:

| Estructura | Rol |
|---|---|
| Lista abierta | Cola de prioridad ordenada por `f = g + h`. Es lo que separa A* de BFS: BFS extrae por orden de llegada, A* por el menor total estimado. |
| Lista cerrada | Estados ya expandidos, para no reprocesarlos. |
| `g` | Costo real de llegar a cada estado. |
| `padre` | Puntero al estado del que se llego. Permite reconstruir el camino al alcanzar la meta; sin el, la busqueda conoceria el costo pero no el camino. |

### Heuristicas

| Nombre | Admisible | Descripcion |
|---|---|---|
| `cero` | Si | `h = 0`. Convierte A* en Dijkstra. Linea base. |
| `colores_pendientes` | Si | Cota por conservacion de celdas. Es la del agente `busqueda_astar`. |

**El argumento de admisibilidad, en tres pasos.**

El costo que falta es `R * (N^2 - 1) - liberaciones_futuras`, donde `R` son
las fichas que quedan por colocar. Por conservacion de celdas, cada ficha
ocupa una celda y cada fusion libera `|G| - 1`, de modo que

```text
liberaciones_futuras = ocupadas_ahora + R - ocupadas_finales
```

Acotar el costo por debajo equivale entonces a acotar `ocupadas_finales` por
debajo. Y cada color distinto que todavia aparece en la secuencia pendiente
deja al menos una celda ocupada al terminar: cuando se coloca su ultima ficha,
nada posterior puede retirarla, porque solo una ficha del mismo color
provocaria la fusion que la absorbe y ya no queda ninguna. Por tanto

```text
h(n) = R * (N^2 - 1) - (ocupadas + R - colores_distintos_pendientes)
```

Ambos terminos se recortan a cero para que la estimacion nunca sea negativa;
recortar solo puede hacerla mas optimista, y una heuristica mas optimista
sigue siendo admisible.

La cota es exacta en los casos simples. En un tablero 2x2 con dos fichas del
mismo color da `h = h* = 5`, y en la instancia de ejemplo del enunciado da
`ocupadas_finales >= 3`, que es justo el optimo que el agente alcanza.

**Sobre la consistencia.** La heuristica es admisible pero no es consistente:
al colocar la ultima ficha de un color, el conjunto de colores pendientes se
reduce y `h` cae mas de lo que cuesta esa accion. Por eso el agente reabre los
nodos cerrados cuando descubre un camino mas barato hacia ellos. Sin esa
reapertura, A* con lista cerrada podria fijar un costo subotimo y no
corregirlo.

### Respeto del limite de tiempo

El espacio de estados crece como el producto de las celdas vacias a lo largo
de la secuencia: para `N = 6` y `M = 24` el arbol tiene del orden de `36^24`
nodos, de modo que A* solo alcanza la meta en instancias pequenas. El agente
aplica tres mecanismos:

1. **Presupuesto determinista de nodos.** La busqueda se detiene al expandir
   `min(120000, floor(2200 * T))` nodos, con `T` el limite de tiempo recibido:
   22000 nodos para `T = 10 s`. El tope de 120000 solo acota la memoria.
2. **Reloj de salvaguarda.** Se comprueba en cada expansion, al 85 % de `T`,
   reservando el resto para el completado avido. No decide cuando parar: solo
   protege el limite obligatorio si el presupuesto no alcanzara a agotarse.
3. **Completado avido.** Si la busqueda se detiene sin alcanzar la meta, se
   toma el mejor estado visto y se termina la partida colocando cada ficha
   restante en la celda de menor costo inmediato. Asi el agente siempre
   entrega una solucion, y lo advierte por salida estandar.

### Determinismo

El agente no usa ninguna fuente de azar. Todos los desempates se resuelven por
reglas fijas: en la lista abierta, menor `f`, luego menor `h`, luego orden de
insercion; en el completado avido, menor costo, luego menor fila y columna.
Como la busqueda se detiene por un presupuesto que depende solo de la entrada,
dos ejecuciones con la misma instancia y el mismo limite expanden los mismos
nodos y producen la misma solucion, sin importar la semilla, siempre que el
reloj de salvaguarda no intervenga. Ver *Criterio de paro y determinismo*.

## Agente evolutivo

El agente `evolutivo` usa un algoritmo genetico de estado estacionario. Cada
individuo contiene `M` genes y cada gen es la coordenada `(fila, columna)`
propuesta para la ficha de esa posicion.

### Aptitud y factibilidad

Un individuo se simula con el motor sobre una copia del estado inicial. Cuando
un gen apunta a una celda ocupada, se suma una reparacion y se usa una
colocacion virtual para poder evaluar los genes posteriores. La colocacion
virtual se elige con una heuristica determinista: mayor fusion inmediata,
menor distancia Manhattan al gen original y, finalmente, menor fila y
columna. La reparacion no modifica el cromosoma ni puede aparecer en la
solucion entregada.

La aptitud es:

```text
100 * fichas_colocadas - 10 * celdas_ocupadas - 25 * reparaciones
```

Las fusiones se registran para analizar el comportamiento y guiar la mutacion,
pero no se suman otra vez a la aptitud: para una misma cantidad de fichas,
dejar menos celdas ocupadas ya expresa el espacio liberado por las fusiones.
El agente mantiene aparte el mejor individuo con cero reparaciones y solo ese
tipo de individuo puede convertirse en solucion.

### Seleccion y variacion

La seleccion es por torneo de tres individuos. Con probabilidad `0.70` se
aplica cruce de un punto; en el caso contrario el hijo parte como copia de un
padre. Despues se elige uniformemente mutar 0, 1, 2 o 3 genes. Las posiciones
son distintas y una mutacion guiada prefiere la celda que produzca la mayor
fusion inmediata, con desempates deterministas.

El caso sin cruce y con cero mutaciones conserva una copia del padre y reutiliza
su aptitud, ya que volver a simular el mismo cromosoma no aporta informacion.
El reemplazo es elitista de estado estacionario: un hijo sustituye al peor
individuo solo cuando lo supera.

### Poblacion, paro y esfuerzo

La poblacion inicial tiene 20 individuos. Primero se construye un plan legal
guiado por fusiones para disponer inmediatamente de una solucion entregable;
los restantes se construyen con elecciones legales aleatorias derivadas de la
semilla.

El agente crea y evalua hijos hasta agotar un presupuesto determinista de
`floor(20000 * T / M)` evaluaciones de aptitud, con `T` el limite de tiempo y
`M` la cantidad de fichas (con `T = 10 s`: 40000 para `M = 5`, 25000 para
`M = 8`, 8000 para `M = 25`). El presupuesto se aplica tanto en la
inicializacion como en el bucle evolutivo. El reloj, al 98 % de `T`, queda solo
como salvaguarda del limite obligatorio. La medida de esfuerzo es
`evaluaciones_aptitud`: una clonacion que reutiliza una aptitud no incrementa
este contador.

### Parametros y procedimiento con el que se fijaron

| Parametro | Valor | Como se fijo |
|---|---|---|
| Tamano de poblacion | 20 | Barrido de calibracion (ver *Calibracion del evolutivo*). |
| Tamano de torneo | 3 | Barrido de calibracion. |
| Probabilidad de cruce | 0.70 | Barrido de calibracion. |
| Pesos de la aptitud | 100 / 10 / 25 | Por diseno: replican el orden del concurso. No se calibran. |
| Presupuesto de evaluaciones | `floor(20000 * T / M)` | Criterio de paro y determinismo. |

El barrido, su regla de eleccion y sus resultados estan en la seccion
*Calibracion del evolutivo*, y se reproducen con
`python -m experimentos.calibracion_evolutivo`.

## Criterio de paro y determinismo

El enunciado exige a la vez que el agente respete el limite de tiempo y que la
misma instancia, el mismo agente y la misma semilla produzcan la misma
solucion. Si el reloj decide cuando parar, la cantidad de trabajo depende de la
velocidad de la maquina en ese momento, y con ella la solucion. Esto se observo
en la practica: A* sobre la misma instancia, con la misma semilla y
`T = 10 s`, expandio 37176 nodos en una sesion y 55791 en otra, y entrego
soluciones distintas (5 y 3 celdas ocupadas). La evidencia quedo en
`resultados/experimentos/piloto/` y `resultados/experimentos/comparacion_criterio_reloj/`.

Por eso ambos agentes se detienen por un **presupuesto de trabajo** que depende
solo de su entrada, y el reloj queda **solo como salvaguarda** del limite
obligatorio:

| Agente | Presupuesto | Salvaguarda |
|---|---|---|
| `busqueda_astar` | `min(120000, floor(2200 * T))` nodos expandidos | 85 % de `T` |
| `evolutivo` | `floor(20000 * T / M)` evaluaciones de aptitud | 98 % de `T` |

Mientras la salvaguarda no actua, la misma entrada ejecuta exactamente el mismo
trabajo y produce la misma solucion. Si llegara a actuar, por ejemplo en una
maquina mucho mas lenta que aquella donde se midieron las corridas, el agente lo
avisa por salida estandar y la bateria experimental lo registra en la columna
`clock_safeguard`. No se afirma un determinismo valido para cualquier maquina
imaginable: lo que se demuestra es que, con estos presupuestos, las corridas
evaluadas completan su trabajo antes de que la salvaguarda intervenga.

**Como se fijaron las constantes.** Con las 186 corridas registradas con el
criterio anterior, en la misma maquina y sin reajustarlas despues:

- *A\*, 2200 nodos por segundo de `T`.* Debia cumplir dos condiciones. No
  cortar ninguna meta observada con `T = 10 s`: la mas costosa necesito 19912
  nodos, lo que exige al menos 1991. Y agotarse antes que el reloj con margen
  1.5 en el caso mas lento observado, 4181 nodos por segundo durante el 85 % de
  `T`, lo que permite a lo sumo 2369. Se eligio 2200, dentro de ese intervalo.
- *Evolutivo, 20000 colocaciones simuladas por segundo de `T`.* Una evaluacion
  simula `M` colocaciones, por eso el presupuesto se divide por `M`: medidas en
  evaluaciones por segundo, las corridas variaron once veces entre instancias;
  medidas en colocaciones simuladas por segundo, solo 2.3 veces. El caso mas
  lento simulo 39042 colocaciones por segundo durante el 98 % de `T`; con
  margen 2 quedan unas 19100, redondeadas a 20000.

**Verificacion.** Con los presupuestos, la prueba de determinismo (4
instancias, 2 agentes, 5 repeticiones, en dos sesiones separadas) dio en cada
grupo un solo hash de solucion, el mismo esfuerzo, ninguna intervencion de la
salvaguarda y ninguna discrepancia con el validador:

```powershell
python -m experimentos.determinismo --experimento determinismo_presupuesto_sesion1
python -m experimentos.determinismo --experimento determinismo_presupuesto_sesion2
```

## Decisiones de diseno

**Responsabilidad unica.** El tablero conoce la geometria y la conectividad,
pero no las reglas. El motor conoce las reglas, pero no la persistencia ni la
presentacion. El lector y el escritor son los unicos modulos que conocen los
formatos de archivo. Cada subcomando resuelve una tarea y solo una.

**Abierto/cerrado.** Agregar un agente consiste en implementar `Agente` e
inscribirlo en `RegistroAgentes`. Agregar un subcomando consiste en
implementar `Comando` e inscribirlo en `RegistroComandos`. En ninguno de los
dos casos cambia `main.py`, ni el motor, ni la sesion, ni la ventana de juego.

**Sustitucion de Liskov.** `ObservadorConsola` y `VentanaJuego` implementan la
misma interfaz `ObservadorPartida` y son intercambiables desde el punto de
vista de la sesion, que no distingue cual la esta observando. Lo mismo ocurre
entre las heuristicas del agente de busqueda.

**Segregacion de interfaces.** `Agente` expone cuatro miembros,
`ObservadorPartida` tres, `Comando` cuatro y `Heuristica` tres. Ninguna clase
implementa metodos que no usa.

**Inversion de dependencias.** `SesionPartida` depende de la abstraccion
`ObservadorPartida`, no de Tkinter. `AgenteBusquedaAEstrella` depende de la
abstraccion `Heuristica`, no de una formula concreta. El dominio no depende de
nada por encima de el, por lo que el motor completo se ejecuta y se prueba sin
entorno grafico.

**Sobre el punto de entrada unico.** El sistema tiene un solo ejecutable con
subcomandos, no un ejecutable por tarea. La propiedad que importa, que
ejecutar agentes no arrastre la capa grafica, se conserva mediante importacion
tardia: `ComandoJugar` importa `VentanaJuego` dentro de su metodo `ejecutar`,
de modo que `resolver` y `validar` nunca cargan Tkinter.

## Bibliotecas externas

| Biblioteca | Uso |
|---|---|
| NumPy | Matrices contiguas para el tablero. |
| pytest | Marco de pruebas. |
| matplotlib | Graficas de la experimentacion. No lo usa ningun agente. |

La cola de prioridad de A* es `heapq` de la biblioteca estandar. El motor, la
busqueda y la heuristica estan escritos integramente en este repositorio: no
se usa ninguna biblioteca de busqueda en grafos o en espacios de estados, ni
marcos de computacion evolutiva, ni resolvedores de restricciones. El programa
no invoca ningun modelo de lenguaje en tiempo de ejecucion ni realiza ninguna
llamada de red.

## Licencia

MIT. Ver el archivo `LICENSE`.