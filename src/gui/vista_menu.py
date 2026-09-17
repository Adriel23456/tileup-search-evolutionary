"""Vista del menu principal de la aplicacion."""

import tkinter
from tkinter import ttk
from typing import Callable

from src.gui import tema
from src.instancias.instancia import Instancia


class VistaMenu(tkinter.Frame):
    """
    Pantalla inicial con las opciones del sistema.

    Muestra la instancia cargada y los botones principales. Los botones de los
    agentes quedan visibles pero deshabilitados hasta que esos modulos existan,
    para que la estructura de la interfaz ya sea la definitiva.
    """

    def __init__(self, contenedor: tkinter.Widget,
                 al_jugar_humano: Callable[[], None],
                 al_ejecutar_busqueda: Callable[[], None],
                 al_ejecutar_evolutivo: Callable[[], None],
                 al_cargar_instancia: Callable[[], None]) -> None:
        """Construye el menu y enlaza las acciones de cada boton."""
        super().__init__(contenedor, background=tema.COLOR_FONDO_VENTANA)

        self._al_jugar_humano = al_jugar_humano
        self._al_ejecutar_busqueda = al_ejecutar_busqueda
        self._al_ejecutar_evolutivo = al_ejecutar_evolutivo
        self._al_cargar_instancia = al_cargar_instancia

        self._etiqueta_instancia = None
        self._etiqueta_backend = None

        self._construir_interfaz()

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------

    def _construir_interfaz(self) -> None:
        """Arma todos los elementos visuales del menu."""
        titulo = tkinter.Label(
            self,
            text="TileUp",
            font=tema.FUENTE_TITULO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_PRIMARIO,
        )
        titulo.pack(pady=(30, 4))

        subtitulo = tkinter.Label(
            self,
            text="Agentes de busqueda y evolutivos",
            font=tema.FUENTE_SUBTITULO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_SECUNDARIO,
        )
        subtitulo.pack(pady=(0, 24))

        panel_botones = tkinter.Frame(
            self, background=tema.COLOR_FONDO_VENTANA
        )
        panel_botones.pack(pady=10)

        self._crear_boton(
            panel_botones,
            "Jugar como humano",
            self._al_jugar_humano,
            habilitado=True,
        )

        self._crear_boton(
            panel_botones,
            "Ejecutar agente de busqueda",
            self._al_ejecutar_busqueda,
            habilitado=False,
        )

        self._crear_boton(
            panel_botones,
            "Ejecutar agente evolutivo",
            self._al_ejecutar_evolutivo,
            habilitado=False,
        )

        self._crear_boton(
            panel_botones,
            "Cargar instancia",
            self._al_cargar_instancia,
            habilitado=True,
        )

        self._etiqueta_instancia = tkinter.Label(
            self,
            text="Instancia: ninguna",
            font=tema.FUENTE_ESTADO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_ACENTO,
        )
        self._etiqueta_instancia.pack(pady=(26, 2))

        self._etiqueta_backend = tkinter.Label(
            self,
            text="Backend: sin detectar",
            font=tema.FUENTE_ESTADO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_SECUNDARIO,
        )
        self._etiqueta_backend.pack(pady=(0, 20))

    def _crear_boton(self, contenedor: tkinter.Widget, texto: str,
                     accion: Callable[[], None], habilitado: bool) -> None:
        """Crea un boton del menu con el estilo comun."""
        if habilitado is True:
            estado_inicial = tkinter.NORMAL
            texto_final = texto
        else:
            estado_inicial = tkinter.DISABLED
            texto_final = texto + "   (pendiente)"

        boton = ttk.Button(
            contenedor,
            text=texto_final,
            command=accion,
            width=34,
        )
        boton.configure(state=estado_inicial)
        boton.pack(pady=6)

    # ------------------------------------------------------------------
    # Actualizacion
    # ------------------------------------------------------------------

    def actualizar_instancia(self, instancia: Instancia) -> None:
        """Refresca la etiqueta que muestra la instancia cargada."""
        if instancia is None:
            self._etiqueta_instancia.configure(text="Instancia: ninguna")
            return

        self._etiqueta_instancia.configure(
            text="Instancia: " + instancia.resumen()
        )

    def actualizar_backend(self, descripcion_backend: str) -> None:
        """Refresca la etiqueta que muestra el backend de computo."""
        self._etiqueta_backend.configure(
            text="Backend: " + descripcion_backend
        )