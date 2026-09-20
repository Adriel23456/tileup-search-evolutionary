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
# pruebas y resuelve la instancia de ejemplo para demostrar que el sistema
# funciona de principio a fin.

$ErrorActionPreference = "Stop"

# Ruta del interprete dentro del entorno virtual. Se invoca de forma directa
# para no depender de la activacion del entorno.
$PythonDelEntorno = ".venv\Scripts\python.exe"

# Instancia con la que se demuestra el flujo completo.
$InstanciaDemo = "datos\instancias\ejemplo_n4_k3_m6.txt"

# Solucion que produce la demostracion.
$SolucionDemo = "datos\soluciones\busqueda_astar\ejemplo_n4_k3_m6__busqueda_astar__s0.sol"


function Escribir-Titulo {
    param([string]$Texto)

    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host $Texto -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}


Escribir-Titulo "1 de 5. Creando el entorno virtual"

if (Test-Path ".venv") {
    Write-Host "El entorno virtual ya existe, se reutiliza."
} else {
    py -3 -m venv .venv
    Write-Host "Entorno virtual creado en .venv"
}


Escribir-Titulo "2 de 5. Instalando dependencias"

& $PythonDelEntorno -m pip install --upgrade pip --quiet
& $PythonDelEntorno -m pip install -r requirements.txt --quiet
Write-Host "Dependencias instaladas."


Escribir-Titulo "3 de 5. Ejecutando las pruebas automatizadas"

& $PythonDelEntorno -m pytest pruebas -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "Las pruebas fallaron. Se detiene la preparacion." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "4 de 5. Resolviendo la instancia de ejemplo"

& $PythonDelEntorno main.py resolver --instancia $InstanciaDemo --agente busqueda_astar --semilla 0 --limite-tiempo 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "La resolucion fallo. Se detiene la preparacion." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "5 de 5. Validando la solucion producida"

& $PythonDelEntorno main.py validar --instancia $InstanciaDemo --solucion $SolucionDemo --exigir-completa

if ($LASTEXITCODE -ne 0) {
    Write-Host "El validador rechazo la solucion." -ForegroundColor Red
    exit 1
}


Escribir-Titulo "Listo"

Write-Host "El sistema esta preparado y verificado."
Write-Host ""
Write-Host "Para usarlo, invoque el interprete del entorno de forma directa:"
Write-Host "    $PythonDelEntorno main.py --ayuda-completa"
Write-Host ""
Write-Host "O active el entorno y use 'python':"
Write-Host "    .venv\Scripts\Activate.ps1"

exit 0