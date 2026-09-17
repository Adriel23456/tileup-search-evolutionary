"""Ventana principal y navegacion entre vistas."""

import os
import tkinter
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from src.aceleracion.backend import DetectorBackend
from src.gui import tema
from src.gui.vista_juego_humano import VistaJuegoHumano
from src.gui.vista_menu import VistaMenu
from src.instancias.errores import ErrorFormatoInstancia
from src.instancias.instancia import Instancia
from src.instancias.lector_instancia import LectorInstancia


# Instancia que se carga al abrir la aplicacion si no se indica otra.
RUTA_INSTANCIA_POR_DEFECTO = os.path.join(
    "datos", "instancias", "ejemplo_4x4.txt"
)

# Directorio inicial del dialogo de carga de instancias.
DIRECTORIO_INSTANCIAS = os.path.join("datos", "instancias")


class AplicacionTileUp:
    """
    Controlador de la interfaz grafica.

    Su unica responsabilidad es crear la ventana, mantener la instancia activa
    y decidir que vista se muestra. Toda la logica del juego vive fuera de la
    capa grafica.
    """

    def __init__(self, ruta_instancia_inicial: Optional[str] = None) -> None:
        """Prepara la ventana y carga la instancia inicial."""
        self._ventana = tkinter.Tk()
        self._ventana.title("TileUp - Agentes de busqueda y evolutivos")
        self._ventana.configure(background=tema.COLOR_FONDO_VENTANA)
        self._ventana.minsize(560, 560)

        self._configurar_estilos()

        self._lector_instancia = LectorInstancia()
        self._instancia_activa: Optional[Instancia] = None
        self._vista_actual: Optional[tkinter.Frame] = None

        self._contenedor = tkinter.Frame(
            self._ventana, background=tema.COLOR_FONDO_VENTANA
        )
        self._contenedor.pack(fill=tkinter.BOTH, expand=True)

        self._cargar_instancia_inicial(ruta_instancia_inicial)
        self.mostrar_menu()

    # ------------------------------------------------------------------
    # Configuracion
    # ------------------------------------------------------------------

    def _configurar_estilos(self) -> None:
        """Aplica el estilo comun a los widgets de ttk."""
        estilo = ttk.Style()

        try:
            estilo.theme_use("clam")
        except tkinter.TclError:
            pass

        estilo.configure(
            "TButton",
            font=tema.FUENTE_BOTON,
            padding=8,
        )

        estilo.configure(
            "TProgressbar",
            background=tema.COLOR_ACENTO,
            troughcolor=tema.COLOR_CELDA_VACIA,
        )

    def _cargar_instancia_inicial(self, ruta_indicada: Optional[str]) -> None:
        """Carga la instancia del arranque, con mensaje claro si falla."""
        if ruta_indicada is None:
            ruta_a_cargar = RUTA_INSTANCIA_POR_DEFECTO
        else:
            ruta_a_cargar = ruta_indicada

        try:
            self._instancia_activa = self._lector_instancia.leer_desde_archivo(
                ruta_a_cargar
            )
        except ErrorFormatoInstancia as error_de_formato:
            messagebox.showerror(
                "Error al cargar la instancia",
                "No se pudo cargar la instancia inicial:\n\n"
                + str(error_de_formato),
            )
            self._instancia_activa = None

    # ------------------------------------------------------------------
    # Navegacion
    # ------------------------------------------------------------------

    def _limpiar_vista_actual(self) -> None:
        """Destruye la vista visible para dejar paso a la siguiente."""
        if self._vista_actual is None:
            return

        self._vista_actual.destroy()
        self._vista_actual = None

    def mostrar_menu(self) -> None:
        """Muestra el menu principal."""
        self._limpiar_vista_actual()

        vista = VistaMenu(
            contenedor=self._contenedor,
            al_jugar_humano=self.mostrar_juego_humano,
            al_ejecutar_busqueda=self._avisar_modulo_pendiente,
            al_ejecutar_evolutivo=self._avisar_modulo_pendiente,
            al_cargar_instancia=self.cargar_instancia_desde_dialogo,
        )
        vista.pack(fill=tkinter.BOTH, expand=True)
        vista.actualizar_instancia(self._instancia_activa)

        informacion_backend = DetectorBackend().detectar()
        vista.actualizar_backend(informacion_backend.detalle)

        self._vista_actual = vista

    def mostrar_juego_humano(self) -> None:
        """Muestra la vista de juego para una persona."""
        if self._instancia_activa is None:
            messagebox.showwarning(
                "Sin instancia",
                "Cargue una instancia valida antes de jugar.",
            )
            return

        self._limpiar_vista_actual()

        vista = VistaJuegoHumano(
            contenedor=self._contenedor,
            instancia=self._instancia_activa,
            al_volver_al_menu=self.mostrar_menu,
        )
        vista.pack(fill=tkinter.BOTH, expand=True)

        self._vista_actual = vista

    # ------------------------------------------------------------------
    # Acciones del menu
    # ------------------------------------------------------------------

    def cargar_instancia_desde_dialogo(self) -> None:
        """Permite elegir un archivo de instancia y lo carga."""
        ruta_elegida = filedialog.askopenfilename(
            title="Seleccione una instancia de TileUp",
            initialdir=DIRECTORIO_INSTANCIAS,
            filetypes=[
                ("Instancias de TileUp", "*.txt"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if len(ruta_elegida) == 0:
            return

        try:
            instancia_nueva = self._lector_instancia.leer_desde_archivo(
                ruta_elegida
            )
        except ErrorFormatoInstancia as error_de_formato:
            messagebox.showerror(
                "Instancia invalida",
                "El archivo no cumple el formato esperado:\n\n"
                + str(error_de_formato),
            )
            return

        self._instancia_activa = instancia_nueva
        self.mostrar_menu()

    def _avisar_modulo_pendiente(self) -> None:
        """Informa que el modulo solicitado aun no esta implementado."""
        messagebox.showinfo(
            "Modulo pendiente",
            "Este agente todavia no esta implementado en esta etapa.",
        )

    # ------------------------------------------------------------------
    # Ejecucion
    # ------------------------------------------------------------------

    def ejecutar(self) -> None:
        """Entra en el bucle de eventos de Tkinter."""
        self._ventana.mainloop()