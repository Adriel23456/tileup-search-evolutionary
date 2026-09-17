## Estado actual verificado

| Componente | Peso | Estado |
|---|---|---|
| Motor y validador | 12 | Completo |
| Agente de búsqueda | 16 | Completo |
| Agente evolutivo | 16 | **No iniciado** |
| Comparación experimental | 14 | **No iniciado** |
| Escalabilidad (grupo de 3) | 12 | **No iniciado** |
| README e informe | 12 | README completo; informe no iniciado |
| Reproducibilidad | 8 | Completo |
| Repositorio y autoría | 5 | **Solo un autor con commits** |
| Video y entrega | 5 | **No iniciado** |

Faltan 42 puntos del bloque técnico y 22 del de profesionalidad.

---

## Paso 1 — Generador de instancias

Va antes del evolutivo porque la comparación experimental exige **6+ configuraciones de N, K y M, con 3+ semillas cada una**. Eso son mínimo 18 instancias. Escribirlas a mano no es viable, y el módulo de escalabilidad lo exige explícitamente.

Archivos: `src/generacion/generador_instancias.py`, `src/cli/comandos/comando_generar.py`.

Subcomando nuevo:
```
python main.py generar --n 6 --k 4 --m 24 --semilla 1
python main.py generar --lote --configuraciones datos/configuraciones.txt
```

Salida a `datos/instancias/gen_n6_k4_m24_s1.txt`, patrón ya reservado en la convención de nombrado.

**Detalle que importa:** el generador debe producir instancias *resolubles*. Una secuencia totalmente aleatoria con M cercano a N² puede ser imposible para cualquier agente, y entonces la comparación mide "quién pierde menos" en vez de "quién resuelve mejor". Conviene un parámetro de densidad de colores que controle qué tan fusionable es la secuencia.

---

## Paso 2 — Agente evolutivo

La rúbrica exige documentar seis cosas con procedimiento explícito:

| Elemento | Propuesta |
|---|---|
| Representación | El cromosoma es la secuencia de M colocaciones. Codificar cada gen como *índice dentro de la lista ordenada de celdas vacías*, no como (fila, columna) absoluta, para que toda mutación produzca un individuo legal sin necesidad de reparación. |
| Aptitud | `fichas_colocadas * N² + (N² − celdas_ocupadas)`. Alinea exactamente con el orden del concurso: primero maximizar colocadas, luego minimizar ocupadas. |
| Selección | Torneo de tamaño k. Preserva diversidad frente a elegir siempre al mejor. |
| Variación | Cruce uniforme (cada posición hereda de un padre) más mutación por reemplazo. Son los operadores del PDF de Semana 4 para políticas de tabla, y encajan aquí porque los genes son índices discretos. |
| Reemplazo | Elitismo: los mejores E pasan intactos, el resto se genera por cruce y mutación. |
| Paro | Generaciones agotadas, límite de tiempo alcanzado, o sin mejora del mejor durante G generaciones. |
| Esfuerzo | `evaluaciones_aptitud`, ya contemplado en `MetricasPartida`. |

**Detalle crítico para la rúbrica:** dice "parámetros fijados con un procedimiento explícito". No basta con escribir `POBLACION = 50`. Hay que hacer un barrido (población × tasa de mutación × tamaño de torneo), guardarlo en `resultados/experimentos/calibracion_evolutivo.csv`, y citarlo en el informe. Eso es la diferencia entre Excelente y Bueno en 16 puntos.

**Otro detalle:** el enunciado advierte que un evolutivo que "reimplemente una búsqueda exhaustiva bajo otro nombre" se califica Deficiente. Hay que asegurar que la evaluación de aptitud sea una simulación de partida, no una exploración de sucesores.

**Aquí sí aplica la GPU.** Evaluar 200 individuos por generación es el único punto del sistema donde el lote justifica el backend que dejamos preparado. Opcional, pero es tu requisito original.

---

## Paso 3 — Batería experimental

Directorio `experimentos/` con guiones que llenen los CSV ya creados.

```
python main.py experimento --tipo comparacion
python main.py experimento --tipo escalabilidad
python main.py experimento --tipo calibracion
```

**Detalles que la rúbrica exige y son fáciles de olvidar:**

- "Los resultados se presentan con su dispersión entre semillas, no como un número único." Media **y** desviación estándar o rango. Una tabla con un solo número por celda baja a Bueno.
- Las soluciones producidas deben committearse junto con las instancias, "para que los resultados del informe puedan verificarse con el validador". Eso cambia el `.gitignore` actual, que excluye los `.sol`.
- El validador debe correr sobre todas las soluciones generadas, no solo sobre una. Un guion que valide el lote entero da evidencia directa del criterio "el validador acepta y rechaza correctamente".

Para escalabilidad: 3 valores de N × 3 de K × 3 semillas mínimo, con al menos una gráfica (matplotlib, permitido explícitamente). La lectura pedida es: **qué parámetro domina el costo, en qué punto A\* deja de terminar dentro del límite, y cómo se comporta el evolutivo en ese mismo régimen.** Esa última parte es una frase del enunciado que se responde con datos, no con opinión.

---

## Paso 4 — Informe

`INFORME.md`, en Markdown dentro del repo. No se acepta Word ni PDF.

Buena parte ya está escrita en el README (formulación de A\*, justificación de heurísticas, función de costo). Conviene **mover** eso al informe y dejar en el README solo lo operativo, porque la rúbrica los evalúa como piezas distintas: README = "un tercero lo sigue sin ayuda", informe = "formulación de ambos agentes y comparación experimental".

Recordatorio del Principio de Defensa Técnica: un componente cuya justificación no conste en el informe se evalúa según la evidencia disponible, aunque funcione. Las cuatro variantes de búsqueda que decidiste conservar necesitan estar justificadas ahí, o son cuatro cosas que el evaluador ve sin entender por qué existen.

---

## Paso 5 — Repositorio y autoría

Esto vale 5 puntos y es donde más fácil se pierden.

- **Daniel y Sebastián necesitan commits propios.** El enunciado: "Un integrante sin commits se evalúa individualmente según la autoría que pueda demostrarse." Sugerencia de reparto: uno toma el generador + batería experimental, otro toma el evolutivo o la calibración. Que los commits sean reales y distribuidos en el tiempo, no cinco commits el día de entrega.
- **Ambos deben llenar su sección en `DECLARACION_IA.md`.** Un documento donde solo tú declaras uso de IA, con un repo que muestra tres autores, es exactamente la situación que el enunciado dice que "agrava".
- Verificar que `.venv/` no esté versionado. Son 5 puntos de descuento directo del bloque de profesionalidad.

---

## Paso 6 — Video

Máximo 10 minutos, **sin edición**. Debe mostrar en este orden: clonar el repo, ejecutar ambos agentes sobre una instancia, validar las soluciones producidas, y recorrer el informe.

Tu flujo actual ya cubre casi todo:

```powershell
git clone <url>
cd tileup-search-evolutionary
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest pruebas -q
.venv\Scripts\python.exe main.py resolver --instancia ... --agentes busqueda evolutivo --semilla 7 --limite-tiempo 10
.venv\Scripts\python.exe main.py validar --instancia ... --solucion ...
```

**Detalle:** el enunciado dice "clonación del repositorio". Conviene grabar clonando en una carpeta limpia, no en tu directorio de trabajo, porque eso es justo lo que valida el criterio de aceptación "sobre el repositorio recién clonado".

---

## Pequeños detalles pendientes del código actual

| Detalle | Por qué importa |
|---|---|
| Aplicar las dos correcciones del turno anterior (poda antes de heurística, aviso de planificación) | Ya identificadas, no aplicadas aún. |
| Las 4 variantes de búsqueda escriben al mismo archivo `.sol` | Correr `busqueda` y luego `busqueda_exacta` sobre la misma instancia y semilla sobrescribe el primer resultado. Para la comparación experimental esto sí rompe: perderías datos. Hay que hacer que `nombre` incluya la variante. |
| `.gitignore` excluye los `.sol` | El enunciado exige entregar las soluciones de la comparación experimental. |
| Los archivos de ejemplo `.sol` en `busqueda/` y `evolutivo/` son placeholders inventados | Reemplazarlos por salidas reales antes de entregar. Un archivo que dice "se reemplaza cuando el agente esté implementado" en la entrega final se ve mal. |
| El criterio de aceptación pide "un solo comando" sin instalar dependencias a mano | Vale la pena un `ejecutar.bat` o `setup.ps1` que haga venv + install + pytest en una línea. |
| Falta probar una instancia no publicada | Criterio de aceptación 2: el evaluador corre una instancia que no viste. Genera una con parámetros distintos a los tuyos y pruébala en frío. |

---

## Orden sugerido

1. Correcciones pendientes + nombres de solución por variante (rápido, desbloquea lo demás)
2. Generador de instancias
3. Agente evolutivo
4. Calibración de parámetros del evolutivo
5. Batería experimental + gráficas
6. Informe
7. Declaraciones de IA de los tres + verificación de commits
8. Video