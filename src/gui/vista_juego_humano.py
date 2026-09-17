"""Vista donde una persona juega TileUp directamente."""

import os
import tkinter
from tkinter import messagebox, ttk
from typing import Callable, List

from src.dominio.estado_partida import EstadoPartida
from src.dominio.motor import EstadoTerminacion
from src.dominio.resultado_colocacion import ResultadoColocacion
from src.gui import tema
from src.instancias.instancia import Instancia
from src.metricas.registro_humano import RegistroHumano
from src.partidas.observador import ObservadorPartida
from src.partidas.sesion_partida import SesionPartida
from src.soluciones.escritor_solucion import EscritorSolucion


# Directorio donde se guardan las soluciones producidas por el jugador humano.
DIRECTORIO_SOLUCIONES_HUMANO = os.path.join("datos", "soluciones", "humano")

# Archivo donde se acumulan los resultados de las partidas humanas.
RUTA_BITACORA_HUMANA = os.path.join(
    "resultados", "humano", "partidas_humanas.csv"
)


class VistaJuegoHumano(tkinter.Frame, ObservadorPartida):
    """
    Tablero interactivo para el jugador humano.

    La vista implementa ObservadorPartida, de modo que se refresca sola cada
    vez que la sesion aplica una colocacion. No conoce las reglas del juego:
    solo dibuja el estado que el motor produjo.
    """

    def __init__(self, contenedor: tkinter.Widget, instancia: Instancia,
                 al_volver_al_menu: Callable[[], None],
                 nombre_jugador: str = "humano") -> None:
        """Construye la vista y arranca una partida nueva."""
        super().__init__(contenedor, background=tema.COLOR_FONDO_VENTANA)

        self._instancia = instancia
        self._al_volver_al_menu = al_volver_al_menu
        self._nombre_jugador = nombre_jugador

        self._sesion = SesionPartida(
            instancia=instancia,
            nombre_agente="humano",
            semilla=0,
        )
        self._sesion.agregar_observador(self)

        self._botones_celda: List[List[tkinter.Button]] = []
        self._partida_terminada = False

        self._etiqueta_ficha_actual = None
        self._etiqueta_metricas = None
        self._barra_progreso = None

        self._construir_interfaz()
        self._sesion.iniciar()
        self._refrescar_todo()

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def _construir_interfaz(self) -> None:
        """Arma el encabezado, el tablero y el pie de la vista."""
        self._construir_encabezado()
        self._construir_tablero()
        self._construir_pie()

    def _construir_encabezado(self) -> None:
        """Crea la zona superior con la ficha pendiente y el progreso."""
        panel_encabezado = tkinter.Frame(
            self, background=tema.COLOR_FONDO_VENTANA
        )
        panel_encabezado.pack(fill=tkinter.X, padx=16, pady=(14, 8))

        etiqueta_instancia = tkinter.Label(
            panel_encabezado,
            text=self._instancia.resumen(),
            font=tema.FUENTE_ESTADO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_SECUNDARIO,
        )
        etiqueta_instancia.pack(anchor="w")

        self._etiqueta_ficha_actual = tkinter.Label(
            panel_encabezado,
            text="",
            font=tema.FUENTE_SUBTITULO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_PRIMARIO,
        )
        self._etiqueta_ficha_actual.pack(anchor="w", pady=(6, 4))

        self._barra_progreso = ttk.Progressbar(
            panel_encabezado,
            orient=tkinter.HORIZONTAL,
            mode="determinate",
            maximum=self._instancia.cantidad_fichas,
        )
        self._barra_progreso.pack(fill=tkinter.X, pady=(2, 0))

    def _construir_tablero(self) -> None:
        """Crea la cuadricula de botones que representa el tablero."""
        panel_tablero = tkinter.Frame(
            self,
            background=tema.COLOR_BORDE,
            padx=2,
            pady=2,
        )
        panel_tablero.pack(padx=16, pady=12)

        dimension = self._instancia.dimension

        for fila in range(dimension):
            botones_de_la_fila: List[tkinter.Button] = []

            for columna in range(dimension):
                boton_celda = tkinter.Button(
                    panel_tablero,
                    text="",
                    width=5,
                    height=2,
                    font=tema.FUENTE_CELDA,
                    relief=tkinter.FLAT,
                    background=tema.COLOR_CELDA_VACIA,
                    foreground=tema.COLOR_TEXTO_PRIMARIO,
                    activebackground=tema.COLOR_ACENTO,
                    command=self._crear_accion_de_celda(fila, columna),
                )
                boton_celda.grid(row=fila, column=columna, padx=1, pady=1)
                botones_de_la_fila.append(boton_celda)

            self._botones_celda.append(botones_de_la_fila)

    def _construir_pie(self) -> None:
        """Crea la zona inferior con metricas y el boton de regreso."""
        panel_pie = tkinter.Frame(self, background=tema.COLOR_FONDO_VENTANA)
        panel_pie.pack(fill=tkinter.X, padx=16, pady=(4, 16))

        self._etiqueta_metricas = tkinter.Label(
            panel_pie,
            text="",
            font=tema.FUENTE_ESTADO,
            background=tema.COLOR_FONDO_VENTANA,
            foreground=tema.COLOR_TEXTO_SECUNDARIO,
            justify=tkinter.LEFT,
        )
        self._etiqueta_metricas.pack(side=tkinter.LEFT)

        boton_volver = ttk.Button(
            panel_pie,
            text="Volver al menu",
            command=self._al_volver_al_menu,
        )
        boton_volver.pack(side=tkinter.RIGHT)

    def _crear_accion_de_celda(self, fila: int, columna: int) -> Callable[[], None]:
        """
        Devuelve la funcion que se ejecuta al hacer clic en una celda.

        Se usa una funcion fabricadora para capturar correctamente los valores
        de fila y columna de cada boton.
        """

        def accion_de_la_celda() -> None:
            """Intenta colocar la ficha pendiente en esta celda."""
            self._intentar_colocar(fila, columna)

        return accion_de_la_celda

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------

    def _intentar_colocar(self, fila: int, columna: int) -> None:
        """Valida y aplica la jugada solicitada por la persona."""
        if self._partida_terminada is True:
            return

        es_legal = self._sesion.motor.es_colocacion_legal(
            self._sesion.estado, fila, columna
        )

        if es_legal is False:
            return

        self._sesion.aplicar_colocacion(fila, columna)

    # ------------------------------------------------------------------
    # Implementacion de ObservadorPartida
    # ------------------------------------------------------------------

    def al_iniciar(self, estado: EstadoPartida) -> None:
        """Refresca la vista al comenzar la partida."""
        self._refrescar_todo()

    def al_colocar(self, estado: EstadoPartida,
                   resultado: ResultadoColocacion) -> None:
        """Refresca la vista tras cada colocacion aplicada."""
        self._refrescar_todo()

    def al_terminar(self, estado: EstadoPartida,
                    terminacion: EstadoTerminacion) -> None:
        """Guarda los resultados y avisa a la persona que la partida acabo."""
        self._partida_terminada = True
        self._refrescar_todo()

        ruta_solucion = self._guardar_resultados()

        if terminacion == EstadoTerminacion.VICTORIA:
            titulo_mensaje = "Victoria"
            cuerpo_mensaje = "Se colocaron todas las fichas de la secuencia."
        else:
            titulo_mensaje = "Derrota"
            cuerpo_mensaje = (
                "El tablero se lleno con fichas pendientes en la secuencia."
            )

        cuerpo_completo = (
            cuerpo_mensaje
            + "\n\nColocadas: " + str(estado.cantidad_colocadas)
            + " de " + str(self._instancia.cantidad_fichas)
            + "\nCeldas ocupadas: " + str(estado.tablero.cantidad_ocupadas)
            + "\nFicha mayor: " + str(estado.tablero.valor_ficha_mayor())
            + "\n\nSolucion guardada en:\n" + ruta_solucion
        )

        messagebox.showinfo(titulo_mensaje, cuerpo_completo)

    # ------------------------------------------------------------------
    # Refresco visual
    # ------------------------------------------------------------------

    def _refrescar_todo(self) -> None:
        """Vuelve a dibujar el tablero, el encabezado y las metricas."""
        self._refrescar_tablero()
        self._refrescar_encabezado()
        self._refrescar_metricas()

    def _refrescar_tablero(self) -> None:
        """Pinta cada celda segun el contenido actual del tablero."""
        tablero = self._sesion.estado.tablero

        for fila in range(tablero.dimension):
            for columna in range(tablero.dimension):
                boton_celda = self._botones_celda[fila][columna]
                ficha_en_celda = tablero.obtener_ficha(fila, columna)

                if ficha_en_celda is None:
                    boton_celda.configure(
                        text="",
                        background=tema.COLOR_CELDA_VACIA,
                    )
                else:
                    boton_celda.configure(
                        text=str(ficha_en_celda.valor),
                        background=tema.color_de_ficha(ficha_en_celda.color),
                    )

                if self._partida_terminada is True:
                    boton_celda.configure(state=tkinter.DISABLED)

    def _refrescar_encabezado(self) -> None:
        """Actualiza la ficha pendiente y la barra de progreso."""
        estado = self._sesion.estado
        ficha_pendiente = estado.ficha_pendiente()

        if ficha_pendiente is None:
            self._etiqueta_ficha_actual.configure(
                text="No quedan fichas pendientes"
            )
        else:
            self._etiqueta_ficha_actual.configure(
                text=(
                    "Ficha " + str(estado.indice_ficha_actual)
                    + " de " + str(self._instancia.cantidad_fichas)
                    + "   |   color " + str(ficha_pendiente.color)
                    + "   valor " + str(ficha_pendiente.valor)
                )
            )

        self._barra_progreso.configure(value=estado.cantidad_colocadas)

    def _refrescar_metricas(self) -> None:
        """Actualiza el texto con las metricas vivas de la partida."""
        estado = self._sesion.estado

        texto_metricas = (
            "Colocadas: " + str(estado.cantidad_colocadas)
            + "   Ocupadas: " + str(estado.tablero.cantidad_ocupadas)
            + " de " + str(estado.tablero.cantidad_celdas)
            + "   Mayor: " + str(estado.tablero.valor_ficha_mayor())
        )

        self._etiqueta_metricas.configure(text=texto_metricas)

    # ------------------------------------------------------------------
    # Persistencia de resultados
    # ------------------------------------------------------------------

    def _guardar_resultados(self) -> str:
        """
        Escribe el archivo de solucion y agrega la fila a la bitacora humana.

        Devuelve la ruta del archivo de solucion generado.
        """
        metricas = self._sesion.construir_metricas()

        nombre_archivo = (
            self._instancia.nombre + "_humano_"
            + str(metricas.fichas_colocadas) + "colocadas.sol"
        )
        ruta_solucion = os.path.join(
            DIRECTORIO_SOLUCIONES_HUMANO, nombre_archivo
        )

        escritor = EscritorSolucion()
        escritor.escribir(ruta_solucion, self._sesion.registro, metricas)

        bitacora = RegistroHumano(RUTA_BITACORA_HUMANA)
        bitacora.registrar(
            metricas=metricas,
            jugador=self._nombre_jugador,
            archivo_solucion=ruta_solucion,
        )

        print(metricas.como_linea_estandar())

        return ruta_solucion