# TileUp - Agentes de busqueda y evolutivos

Implementacion del juego TileUp con interfaz grafica, motor de reglas
independiente y, en etapas posteriores, dos agentes automaticos que resuelven
las instancias de forma autonoma.

Tarea Corta 1 - Inteligencia Artificial - Instituto Tecnologico de Costa Rica.

## Equipo

| Integrante | Carne |
|---|---|
| Adriel S. Chaves Salazar | 2021031465 |
| Daniel Duarte Cordero | 2022012866 |
| Sebastian Hernandez Bonilla | 2022093651 |

## Estado actual

Esta entrega cubre la primera etapa del desarrollo:

- Motor del juego completo (colocacion, fusion, victoria y derrota).
- Lectura del formato de instancia y escritura del formato de solucion.
- Interfaz grafica con menu, carga de instancias y modo de juego humano.
- Bitacora de partidas humanas como linea base de comparacion.
- Pruebas unitarias del motor, del tablero y del lector de instancias.

Pendiente para etapas siguientes: agente de busqueda, agente evolutivo,
validador independiente, generador de instancias y bateria experimental.

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior, con Tkinter incluido (viene con el instalador
  oficial de python.org).
- No se requiere GPU. El sistema detecta CuPy si esta instalado, pero en esta
  etapa todo el computo ocurre en CPU con NumPy.

Verificar la version instalada:

```bat
py --version
```

## Instalacion

Desde la raiz del repositorio, en PowerShell o CMD:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno virtual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Para desactivar el entorno al terminar:

```bat
deactivate
```

## Ejecucion

Abrir la interfaz grafica con la instancia por defecto:

```bat
python main.py
```

Abrir la interfaz con una instancia especifica:

```bat
python main.py --instancia datos\instancias\pequena_5x5.txt
```

Validar el formato de una instancia sin abrir la interfaz:

```bat
python main.py --revisar-instancia datos\instancias\ejemplo_4x4.txt
```

Consultar el backend de computo detectado:

```bat
python main.py --backend
```

Codigos de salida: `0` en caso de exito, `2` cuando una instancia esta mal
formada.

## Pruebas

```bat
python -m pytest pruebas -v
```

## Uso de la interfaz

El menu principal ofrece cuatro opciones:

| Boton | Funcion |
|---|---|
| Jugar como humano | Abre el tablero interactivo. |
| Ejecutar agente de busqueda | Reservado para la siguiente etapa. |
| Ejecutar agente evolutivo | Reservado para la siguiente etapa. |
| Cargar instancia | Reemplaza la instancia activa por otro archivo. |

En el modo humano el encabezado muestra la ficha pendiente (su color y su
valor) y una barra de progreso sobre la secuencia. Un clic sobre una celda
vacia coloca la ficha ahi. Al terminar la partida, el sistema escribe el
archivo de solucion y agrega una fila a la bitacora humana.

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

## Organizacion del repositorio

```text
src/dominio/      Reglas puras del juego: ficha, tablero, estado y motor.
src/instancias/   Lectura y validacion del formato de entrada.
src/soluciones/   Acumulacion y escritura del formato de salida.
src/partidas/     Orquestacion de una partida y observadores.
src/agentes/      Contrato comun de los agentes automaticos.
src/metricas/     Metricas reportables y bitacora de partidas humanas.
src/aceleracion/  Deteccion del backend de computo.
src/gui/          Interfaz grafica en Tkinter.
```

Flujo de datos:

```text
datos/instancias/*.txt        ENTRADA: instancias de los agentes y del humano.
datos/soluciones/humano/      SALIDA: soluciones de partidas humanas.
datos/soluciones/busqueda/    SALIDA: soluciones del agente de busqueda.
datos/soluciones/evolutivo/   SALIDA: soluciones del agente evolutivo.
resultados/humano/            Bitacora acumulada de partidas humanas.
resultados/experimentos/      Tablas y graficas de la comparacion final.
```

## Decisiones de diseno

El sistema aplica los principios SOLID de la siguiente forma.

**Responsabilidad unica.** El tablero conoce la geometria y la conectividad,
pero no las reglas. El motor conoce las reglas, pero no la persistencia ni la
interfaz. El lector y el escritor son los unicos modulos que conocen los
formatos de archivo.

**Abierto/cerrado.** Agregar un agente nuevo no requiere modificar el motor,
la sesion de partida ni la interfaz: basta con implementar la interfaz
`Agente`. Lo mismo aplica a la barra de progreso de los agentes, que sera otra
implementacion de `ObservadorPartida`.

**Sustitucion de Liskov.** Cualquier implementacion de `ObservadorPartida`
puede reemplazar a otra sin que la sesion cambie su comportamiento, incluido
el objeto nulo `ObservadorSilencioso` usado en las pruebas.

**Segregacion de interfaces.** `Agente` expone solo cuatro miembros y
`ObservadorPartida` solo tres. Ninguna clase se ve obligada a implementar
metodos que no usa.

**Inversion de dependencias.** `SesionPartida` depende de la abstraccion
`ObservadorPartida`, no de Tkinter. La capa grafica depende del dominio, nunca
al reves, lo que permite ejecutar todo el motor sin entorno grafico.

**Sobre el uso de GPU.** El motor opera sobre tableros de decenas de celdas,
donde una transferencia de memoria a la GPU costaria mas que el calculo. Por
eso esta etapa corre integramente en CPU con NumPy, que ya provee arreglos
contiguos y operaciones vectorizadas suficientes. El modulo
`src/aceleracion/backend.py` detecta CuPy y un dispositivo CUDA si estan
disponibles, y queda como punto de extension para el agente evolutivo, donde
si tiene sentido evaluar poblaciones completas en lote.

## Declaracion de uso de inteligencia artificial

Pendiente de completar antes de la entrega final, segun lo exigido en la
seccion de evaluacion del enunciado.