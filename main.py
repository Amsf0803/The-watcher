from typing import Any
import os
import psutil
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog  # <- Añadimos RichLog
from textual.containers import Grid

class SysMonitorApp(App[Any]):
    """The Watcher: TUI Avanzada de Monitoreo de Sistema y Bases de Datos."""

    CSS = """
    Grid {
        grid-size: 2;
        grid-gutter: 1 2;
    }
    Static, RichLog {
        background: $panel;
        color: $text;
        height: 100%;
        border: solid $accent;
        padding: 1;
    }
    """

    BINDINGS = [("d", "toggle_dark", "Cambiar Tema"), ("q", "quit", "Salir")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Grid():
            yield Static("Cargando métricas...", id="sys_metrics")
            yield Static("Cargando estado de bases de datos...", id="db_metrics")
            yield Static("Analizando procesos activos...", id="processes")
            # Cambiamos Static por RichLog y activamos el resaltado de estilos
            yield RichLog(highlight=True, markup=True, id="logs")
        yield Footer()

    def on_mount(self) -> None:
        """Configura los hilos de ejecución y los estados iniciales."""
        # Inicializamos el panel de logs con un mensaje de bienvenida
        log_panel = self.query_one("#logs", RichLog)
        log_panel.write("[bold green]🟢 [The Watcher v1.0] inicializado correctamente.[/bold green]")
        log_panel.write("[bold info]📁 Monitoreando archivo 'app.log'...[/bold info]\n")

        # Variables de control de estado para evitar duplicar logs repetitivos
        self.last_mysql_state = None
        self.last_sqlite_state = None

        # Intervalos de actualización
        self.set_interval(1.0, self.update_system_metrics)
        self.set_interval(2.0, self.update_process_metrics)
        self.set_interval(3.0, self.update_db_metrics)
        self.set_interval(1.5, self.read_external_file_logs)

    def update_system_metrics(self) -> None:
        """Actualiza el panel de CPU y RAM y alerta si hay sobrecarga."""
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        
        # Alerta en logs si el CPU pasa del 85%
        if cpu_usage > 85:
            self.query_one("#logs", RichLog).write(f"[bold red]⚠️ ALERTA:[/bold red] Uso crítico de CPU en [red]{cpu_usage}%[/red]")

        metrics_panel = self.query_one("#sys_metrics", Static)
        text_output = (
            "[b]📊 MÉTRICAS DEL SISTEMA[/b]\n\n"
            f"💻 Uso de CPU:  [bold cyan]{cpu_usage}%[/bold cyan]\n"
            f"🧠 Uso de RAM:  [bold magenta]{ram.percent}%[/bold magenta] "
            f"({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n"
        )
        metrics_panel.update(text_output)

    def update_process_metrics(self) -> None:
        """Obtiene el Top 5 de procesos con mayor consumo."""
        processes_panel = self.query_one("#processes", Static)
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                procs.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        procs = sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:5]
        
        text_output = "[b]🔥 TOP 5 PROCESOS ACTIVOS[/b]\n\n"
        for p in procs:
            cpu = p['cpu_percent']
            text_output += f"🆔 [yellow]{p['pid']}[/yellow] | [cyan]{p['name'][:18]}[/cyan] -> [bold red]{cpu}% CPU[/bold red]\n"
            
        processes_panel.update(text_output)

    def update_db_metrics(self) -> None:
        """Verifica motores de BD y registra cambios de estado en los logs."""
        db_panel = self.query_one("#db_metrics", Static)
        log_panel = self.query_one("#logs", RichLog)
        
        # 1. Comprobación MySQL
        mysql_active = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] in ['mysqld', 'mariadb']:
                    mysql_active = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        mysql_status = "[bold green]Activo (Running) ⚡[/bold green]" if mysql_active else "[bold red]Inactivo ❌[/bold red]"
        
        # Guardar log si cambia el estado de MySQL
        if mysql_active != self.last_mysql_state and self.last_mysql_state is not None:
            status_text = "[bold green]ONLINE[/bold green]" if mysql_active else "[bold red]OFFLINE[/bold red]"
            log_panel.write(f"⚙️ [b]MySQL Estatal:[/b] Servicio cambió a {status_text}")
        self.last_mysql_state = mysql_active

        # 2. Comprobación SQLite
        db_file = "proyecto.db"
        sqlite_active = os.path.exists(db_file)
        sqlite_status = f"[bold green]Conectado ({db_file}) 📁[/bold green]" if sqlite_active else "[bold yellow]No detectado[/bold yellow]"
        
        # Guardar log si cambia el estado del archivo SQLite
        if sqlite_active != self.last_sqlite_state and self.last_sqlite_state is not None:
            status_text = f"[bold green]CONECTADO ({db_file})[/bold green]" if sqlite_active else "[bold red]DESCONECTADO[/bold red]"
            log_panel.write(f"🗃️ [b]SQLite Estatal:[/b] Archivo {status_text}")
        self.last_sqlite_state = sqlite_active
            
        text_output = (
            "[b]🗄️ MONITOR DE BASES DE DATOS[/b]\n\n"
            f"🐬 Servicio MySQL:  {mysql_status}\n"
            f"🪶 Archivo SQLite:  {sqlite_status}\n"
        )
        db_panel.update(text_output)

    def read_external_file_logs(self) -> None:
        """Lee líneas nuevas de un archivo de log externo ('app.log') si existe."""
        log_file = "app.log"
        log_panel = self.query_one("#logs", RichLog)
        
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                
                # Para simular un 'tail', si hay líneas nuevas, extraemos las últimas y limpiamos el archivo
                if lines:
                    for line in lines:
                        clean_line = line.strip()
                        if clean_line:
                            log_panel.write(f"[skyblue]📄 [FileLog][/skyblue] {clean_line}")
                    
                    # Truncamos el archivo para no leer lo mismo en el siguiente ciclo
                    with open(log_file, "w") as f:
                        f.write("")
            except Exception as e:
                pass


if __name__ == "__main__":
    app = SysMonitorApp()
    app.run()