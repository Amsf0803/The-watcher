from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Grid

class SysMonitorApp(App):
    """Una aplicación TUI para monitorear el sistema y bases de datos."""

    # Textual permite usar una sintaxis similar a CSS para el diseño
    CSS = """
    Grid {
        grid-size: 2;
        grid-gutter: 1 2;
    }
    Static {
        background: $panel;
        color: $text;
        height: 100%;
        border: solid $accent;
        padding: 1;
    }
    """

    # Atajos de teclado nativos
    BINDINGS = [("d", "toggle_dark", "Cambiar Tema"), ("q", "quit", "Salir")]

    def compose(self) -> ComposeResult:
        """Aquí definimos los widgets que componen la interfaz."""
        yield Header()
        with Grid():
            # Estos son los 4 paneles principales de nuestro dashboard
            yield Static("Métricas de CPU y RAM aquí", id="sys_metrics")
            yield Static("Estado de MySQL / SQLite aquí", id="db_metrics")
            yield Static("Procesos activos", id="processes")
            yield Static("Logs del sistema", id="logs")
        yield Footer()

if __name__ == "__main__":
    app = SysMonitorApp()
    app.run()