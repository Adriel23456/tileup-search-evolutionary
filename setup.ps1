# Preparacion completa del entorno de TileUp en una sola orden.
#
# Uso desde la raiz del repositorio recien clonado:
#     powershell -ExecutionPolicy Bypass -File setup.ps1
#
# El parametro -ExecutionPolicy Bypass evita el error
# "running scripts is disabled on this system" sin cambiar la configuracion
# de la maquina, de modo que el guion corre tal cual en la maquina del
# evaluador.
#
# El guion crea el entorno virtual, instala las dependencias, ejecuta las
# pruebas, resuelve la instancia de ejemplo con los dos agentes del enunciado
# y valida ambas soluciones.

$ErrorActionPreference = "Stop"

# Ruta del interprete dentro del entorno virtual. Se invoca de forma directa
# para no depender de la activacion del entorno.
$PythonDelEntorno = ".venv\Scripts\python.exe"

# Instancia con la que se demuestra el flujo completo.
$InstanciaDemo = "datos\instancias\ejemplo_n4_k3_m6.txt"

# Soluciones que produce la demostracion, una por agente.
$SolucionBusqueda = "datos\soluciones\busqueda_astar\ejemplo_n4_k3_m6__busqueda_astar__s0.sol"
$SolucionEvolutivo = "datos\soluciones\evolutivo\ejemplo_n4_k3_m6__evolutivo__s0.sol"


function Escribir-Titulo {
    param([string]$Texto)

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host $Texto -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}


Escribir-Titulo "1 de 6. Creando el entorno virtual"

if (Test-Path ".venv") {
    Write-Host "El entorno virtual ya existe, se reutiliza."
} else {
    py -3 -m venv .venv
    Write-Host "Entorno virtual creado en .venv"
}


Escribir-Titulo "2 de 6. Instalando dependencias"

& $PythonDelEntorno -m pip install --upgrade pip --quiet
& $PythonDelEntorno -m pip install -r requirements.txt --quiet
Write-Host "Dependencias instaladas."


Escribir-Titulo "3 de 6. Ejecutando las pruebas automatizadas"

& $PythonDelEntorno -m pytest pruebas -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "Las pruebas fallaron. Se detiene la preparacion." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "4 de 6. Resolviendo la instancia de ejemplo con ambos agentes"

& $PythonDelEntorno main.py resolver --instancia $InstanciaDemo --agentes busqueda_astar evolutivo --semilla 0 --limite-tiempo 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "La resolucion fallo. Se detiene la preparacion." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "5 de 6. Validando la solucion de busqueda_astar"

& $PythonDelEntorno main.py validar --instancia $InstanciaDemo --solucion $SolucionBusqueda --exigir-completa

if ($LASTEXITCODE -ne 0) {
    Write-Host "El validador rechazo la solucion de busqueda_astar." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "6 de 6. Validando la solucion del evolutivo"

& $PythonDelEntorno main.py validar --instancia $InstanciaDemo --solucion $SolucionEvolutivo --exigir-completa

if ($LASTEXITCODE -ne 0) {
    Write-Host "El validador rechazo la solucion del evolutivo." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "Listo"

Write-Host "El sistema esta preparado y verificado con ambos agentes."
Write-Host ""
Write-Host "Para usarlo, invoque el interprete del entorno de forma directa:"
Write-Host "    $PythonDelEntorno main.py --ayuda-completa"
Write-Host ""
Write-Host "O active el entorno y use 'python':"
Write-Host "    .venv\Scripts\Activate.ps1"

exit 0