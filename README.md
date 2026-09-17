# TileUp - Agentes de busqueda y evolutivos

Implementacion del juego TileUp con motor de reglas independiente, agentes
automaticos que lo resuelven, validador de soluciones e interfaz grafica para
jugar.

Tarea Corta 1 - Inteligencia Artificial (IC-6200) - Instituto Tecnologico de
Costa Rica.

## Equipo

| Integrante | Carne |
|---|---|
| Adriel S. Chaves Salazar | 2021031465 |
| Daniel Duarte Cordero | 2022012866 |
| Sebastian Hernandez Bonilla | 2022093651 |

## Estado actual

| Componente | Estado |
|---|---|
| Motor del juego | Completo |
| Lectura de instancias y escritura de soluciones | Completo |
| Interfaz grafica de juego humano | Completo |
| Bitacora de partidas humanas | Completo |
| Validador independiente | Completo |
| Agente de busqueda A* | Completo |
| Agente evolutivo | Pendiente |
| Generador de instancias | Pendiente |
| Comparacion experimental | Pendiente |
| Estudio de escalabilidad | Pendiente |

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior, con Tkinter incluido (viene con el instalador
  oficial de python.org).
- No se requiere GPU. El sistema detecta CuPy si esta instalado, pero todo el
  computo actual ocurre en CPU con NumPy.

```powershell
py --version
```

## Instalacion

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Llamar al ejecutable del entorno de forma directa evita el error
`running scripts is disabled on this system` que PowerShell produce con su
politica de ejecucion por defecto. Si prefiere activar el entorno:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

A partir de aqui, los comandos del documento se escriben como `python`,
asumiendo el entorno activo. Sin activarlo, sustituya `python` por
`.venv\Scripts\python.exe`.

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
| `agentes` | Lista los agentes disponibles. |
| `backend` | Muestra el backend de computo detectado. |

Codigos de salida, comunes a todos los subcomandos:

| Codigo | Significado |
|---|---|
| `0` | La operacion termino correctamente. |
| `1` | Veredicto negativo. Solo lo emite `validar` al rechazar una solucion. |
| `2` | Error de entrada: archivo ausente, formato invalido o argumento fuera de rango. |
| `3` | Se solicito un agente que no esta registrado. |

## Subcomando `resolver`

```powershell
python main.py resolver --instancia datos\instancias\ejemplo_n4_k3_m6.txt --agente busqueda --semilla 42 --limite-tiempo 5
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

Salida estandar:

```text
busqueda     [##############################] 6/6
agente=busqueda instancia=ejemplo_n4_k3_m6 semilla=42 resultado=victoria colocadas=6/6 ocupadas=3 mayor=6 tiempo_s=0.0231 nodos_expandidos=412
solucion=D:\...\datos\soluciones\busqueda\ejemplo_n4_k3_m6__busqueda__s42.sol
```

## Subcomando `validar`

```powershell
python main.py validar --instancia datos\instancias\ejemplo_n4_k3_m6.txt --solucion datos\soluciones\busqueda\ejemplo_n4_k3_m6__busqueda__s42.sol
```

| Argumento | Obligatorio | Descripcion |
|---|---|---|
| `--instancia` | Si | Ruta del archivo de instancia. |
| `--solucion` | Si | Ruta del archivo de solucion a validar. |
| `--exigir-completa` | No | Rechaza la solucion si no consume la secuencia entera. |

## Subcomando `jugar`

```powershell
python main.py jugar --instancia datos\instancias\pequena_n5_k3_m12.txt --jugador adriel --partida 1
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

## Subcomandos `instancia`, `agentes` y `backend`

```powershell
python main.py instancia --instancia datos\instancias\ejemplo_n4_k3_m6.txt
python main.py agentes
python main.py backend
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

## Convencion de nombrado

| Directorio | Patron |
|---|---|
| `datos/instancias/` | `<etiqueta>_n<N>_k<K>_m<M>.txt` |
| `datos/instancias/` generadas | `gen_n<N>_k<K>_m<M>_s<semilla>.txt` |
| `datos/soluciones/<agente>/` | `<instancia>__<agente>__s<semilla>.sol` |
| `resultados/humano/` | `partidas_humanas.csv` |
| `resultados/experimentos/` | `comparacion_agentes.csv`, `escalabilidad_n_k.csv` |

Todo en minusculas, sin espacios ni caracteres especiales del espanol. El
modulo `src/nombrado/nombres_archivos.py` es la unica fuente de estos
patrones.

## Organizacion del repositorio

```text
main.py            Punto de entrada unico, con seis subcomandos.

src/dominio/       Reglas puras del juego: ficha, tablero, estado y motor.
src/instancias/    Lectura y validacion del formato de entrada.
src/soluciones/    Acumulacion y escritura del formato de salida.
src/partidas/      Orquestacion de partidas, observadores y ejecutor.
src/agentes/       Contrato de agente, heuristicas y agentes concretos.
src/validacion/    Reimplementacion independiente de las reglas y arbitraje.
src/metricas/      Metricas reportables y bitacora de partidas humanas.
src/aceleracion/   Deteccion del backend de computo.
src/nombrado/      Convenciones de nombrado de archivos.
src/cli/           Subcomandos y ejecucion por consola.
src/gui/           Ventana de juego humano.

pruebas/           Pruebas unitarias y de integracion.
```

Flujo de datos:

```text
datos/instancias/*.txt        ENTRADA de los agentes y del jugador humano.
datos/soluciones/humano/      SALIDA de las partidas humanas.
datos/soluciones/busqueda/    SALIDA del agente de busqueda.
datos/soluciones/evolutivo/   SALIDA del agente evolutivo.
datos/soluciones/aleatorio/   SALIDA del agente de linea base.
resultados/humano/            Bitacora acumulada de partidas humanas.
resultados/experimentos/      Tablas y graficas de la comparacion final.
```

## Agentes disponibles

| Nombre | Estado | Medida de esfuerzo |
|---|---|---|
| `aleatorio` | Implementado. Linea base inferior. | `colocaciones_evaluadas` |
| `busqueda` | Implementado. A* con poda, configuracion de competencia. | `nodos_expandidos` |
| `busqueda_exacta` | Implementado. A* puro, optimo. | `nodos_expandidos` |
| `busqueda_dijkstra` | Implementado. A* con `h = 0`. | `nodos_expandidos` |
| `busqueda_agresiva` | Implementado. Heuristica no admisible. | `nodos_expandidos` |
| `evolutivo` | Pendiente. | `evaluaciones_aptitud` |

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
| Costo de accion | `(N^2 - 1) - liberadas(a)`, con `liberadas(a) = |G| - 1`. |
| Prueba de meta | `i == M`. |

La funcion de costo se eligio con dos condiciones simultaneas.

**No negatividad.** A* pierde sus garantias con costos negativos. El costo
"natural" seria el cambio en celdas ocupadas, que vale `2 - |G|` y es negativo
en cuanto hay fusion. Restar las liberaciones de una constante lo arregla.

**Exactitud respecto al objetivo.** Todo camino meta tiene exactamente `M`
acciones y `suma(liberadas) = M - ocupadas_finales`, de modo que
`g_total = M(N^2 - 2) + ocupadas_finales`. El termino constante es identico
para todos los caminos meta, asi que **minimizar `g` equivale exactamente a
minimizar las celdas ocupadas al terminar**, que es el segundo criterio de
desempate del concurso.

### Heuristicas

| Nombre | Admisible | Descripcion |
|---|---|---|
| `cero` | Si | `h = 0`. Convierte A* en Dijkstra. Linea base. |
| `cota_liberaciones` | Si | Cota por conservacion de celdas. Opcion por defecto. |
| `compactacion_pK` | **No** | Cota admisible mas una penalizacion por ocupacion. |

**La heuristica admisible, en detalle.** El costo restante es
`restantes * (N^2 - 1) - liberaciones_futuras`. Para acotarlo por debajo hay
que acotar las liberaciones futuras por arriba. Por conservacion de celdas,
`liberaciones_futuras = (ocupadas + restantes) - ocupadas_finales`, de modo
que basta una cota inferior de `ocupadas_finales`. Se usan dos aportes que no
pueden solaparse porque hablan de colores distintos:

1. Cada color distinto que todavia aparece en la secuencia pendiente deja al
   menos una celda al final. Cuando se coloca su ultima ficha, nada posterior
   puede retirarla: solo una ficha del mismo color provocaria la fusion que la
   absorbe, y ya no queda ninguna.
2. Cada componente conexa de un color congelado, es decir presente en el
   tablero pero ausente del resto de la secuencia, permanece intacta.

```text
cota = componentes_congeladas + colores_distintos_restantes
h(n) = max(0, restantes * (N^2 - 1) - max(0, ocupadas + restantes - cota))
```

Ambos aportes se derivan de invariantes del juego y no de las decisiones del
agente, por lo que la cota nunca sobreestima. En los casos triviales es
exacta: en un tablero 2x2 con dos fichas del mismo color da `h = h* = 5`.

**La heuristica no admisible, y que garantia se pierde.** `compactacion_pK`
suma a la cota admisible una penalizacion proporcional a las celdas ocupadas
en el estado actual, lo que empuja la busqueda hacia configuraciones
despejadas antes de que el costo real lo justifique. Al sobreestimar, A* deja
de garantizar que la solucion encontrada sea la optima. Sigue siendo completa
dentro del limite de nodos y sigue produciendo soluciones legales, pero la
cantidad de celdas ocupadas al final puede no ser la minima posible. El peso
`K` se fijo por barrido sobre los valores 1, 2, 4 y 8.

### Comportamiento anytime

El espacio de estados crece como el producto de las celdas vacias a lo largo
de la secuencia: para `N = 6` y `M = 24` el arbol tiene del orden de `36^24`
nodos. A* exacto solo termina en instancias pequenas, de modo que el agente
incorpora tres mecanismos:

1. **Limite de tiempo.** Se comprueba en cada expansion.
2. **Limite de nodos expandidos.** Acota tambien la memoria.
3. **Completado avido.** Si la busqueda se detiene sin alcanzar la meta, se
   toma el mejor nodo visto y se termina la partida con una politica avida
   determinista, de modo que el agente siempre entrega una solucion.

El limite de sucesores por nodo es el cuarto mecanismo y el unico que cambia
la naturaleza del algoritmo: con el activo, A* se convierte en una busqueda en
haz ordenada por `f`. Gana tratabilidad y pierde completitud y optimalidad.
Se desactiva construyendo el agente con `maximo_sucesores = 0`.

### Determinismo

El agente no usa ninguna fuente de azar. Todos los desempates se resuelven por
reglas fijas: en la lista abierta, menor `f`, luego menor `h`, luego orden de
insercion; entre sucesores, menor `f`, luego menos celdas ocupadas, luego
menor fila y columna. Dos ejecuciones sobre la misma instancia producen
siempre la misma solucion, sin importar la semilla.

### Variantes registradas

| Nombre en consola | Heuristica | Poda | Uso previsto |
|---|---|---|---|
| `busqueda` | `cota_liberaciones` | 6 sucesores | Configuracion de competencia. |
| `busqueda_exacta` | `cota_liberaciones` | Ninguna | A* puro, optimo, solo instancias pequenas. |
| `busqueda_dijkstra` | `cero` | Ninguna | Linea base para medir el aporte de la heuristica. |
| `busqueda_agresiva` | `compactacion_p2` | 6 sucesores | Menos nodos, sin garantia de optimalidad. |

Las cuatro variantes comparten el nombre de agente `busqueda`, de modo que sus
soluciones se escriben en `datos/soluciones/busqueda/`.

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
vista de la sesion, que no distingue cual esta observando. Lo mismo ocurre
entre las tres heuristicas del agente de busqueda.

**Segregacion de interfaces.** `Agente` expone cuatro miembros,
`ObservadorPartida` tres, `Comando` cuatro y `Heuristica` tres. Ninguna clase
implementa metodos que no usa.

**Inversion de dependencias.** `SesionPartida` depende de la abstraccion
`ObservadorPartida`, no de Tkinter. `AgenteBusquedaAEstrella` depende de la
abstraccion `Heuristica`, no de una formula concreta. El dominio no depende de
nada por encima de el, por lo que el motor completo se ejecuta y se prueba sin
entorno grafico.

**Sobre el punto de entrada unico.** El sistema tiene un solo ejecutable con
subcomandos, no un ejecutable por tarea. SOLID rige clases y modulos, no la
cantidad de archivos con punto de entrada, y una sola interfaz es mas facil de
aprender y de documentar que tres. La propiedad que si importaba, que ejecutar
agentes no arrastre la capa grafica, se conserva mediante importacion tardia:
`ComandoJugar` importa `VentanaJuego` dentro de su metodo `ejecutar`, de modo
que `resolver` y `validar` nunca cargan Tkinter.

**Sobre el uso de GPU.** El motor opera sobre tableros de decenas de celdas,
donde una transferencia de memoria a la GPU costaria mas que el calculo. Por
eso el sistema corre integramente en CPU con NumPy, que ya provee arreglos
contiguos y operaciones vectorizadas suficientes. El modulo
`src/aceleracion/backend.py` detecta CuPy y un dispositivo CUDA si estan
disponibles, y queda como punto de extension para el agente evolutivo, donde
si tiene sentido evaluar poblaciones completas en lote.

## Declaracion de uso de inteligencia artificial

Pendiente de completar antes de la entrega final, segun lo exigido en la
seccion de evaluacion del enunciado.

## Licencia

MIT. Ver el archivo `LICENSE`.