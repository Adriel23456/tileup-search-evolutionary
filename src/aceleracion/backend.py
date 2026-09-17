"""
Deteccion del backend de computo disponible.

En esta etapa el sistema corre integramente en CPU con NumPy, porque el motor
del juego trabaja sobre tableros pequenos donde una transferencia a la GPU
costaria mas que el calculo completo.

El modulo existe desde ya para que el agente evolutivo pueda, mas adelante,
evaluar poblaciones completas en lote sobre GPU sin que ningun otro modulo
tenga que cambiar. Ese es el punto de extension previsto.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class InformacionBackend:
    """Describe el backend de computo detectado en la maquina."""

    nombre: str
    soporta_gpu: bool
    detalle: str


class DetectorBackend:
    """
    Averigua que capacidades de computo hay disponibles.

    La deteccion es tolerante a fallos: si una biblioteca opcional no esta
    instalada, simplemente se reporta el backend de CPU.
    """

    def detectar(self) -> InformacionBackend:
        """Devuelve el mejor backend disponible en orden de preferencia."""
        informacion_gpu = self._intentar_detectar_gpu()

        if informacion_gpu is not None:
            return informacion_gpu

        return self._detectar_cpu()

    def _intentar_detectar_gpu(self) -> InformacionBackend:
        """Intenta detectar CuPy y un dispositivo CUDA utilizable."""
        try:
            import cupy
        except ImportError:
            return None

        try:
            cantidad_dispositivos = cupy.cuda.runtime.getDeviceCount()
        except Exception:
            return None

        if cantidad_dispositivos < 1:
            return None

        propiedades = cupy.cuda.runtime.getDeviceProperties(0)
        nombre_dispositivo = propiedades["name"].decode("utf-8")

        return InformacionBackend(
            nombre="cupy",
            soporta_gpu=True,
            detalle="Dispositivo CUDA detectado: " + nombre_dispositivo,
        )

    def _detectar_cpu(self) -> InformacionBackend:
        """Reporta el backend de CPU basado en NumPy."""
        import numpy

        return InformacionBackend(
            nombre="numpy",
            soporta_gpu=False,
            detalle="Computo en CPU con NumPy " + numpy.__version__,
        )