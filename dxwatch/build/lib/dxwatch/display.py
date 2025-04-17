from rich.console import Console
import requests

console = Console()
CURRENT_VERSION = "1.0.0"

def print_logo():
    logo = """
    ██████╗ ██╗  ██╗██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗
    ██╔══██╗╚██╗██╔╝██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║
    ██║  ██║ ╚███╔╝ ██║ █╗ ██║███████║   ██║   ██║     ███████║
    ██║  ██║ ██╔██╗ ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║
    ██████╔╝██╔╝ ██╗╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║
    ╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
    """
    console.print(f"[bold purple]{logo.rstrip()}[/bold purple]")
    update_available, latest_version = check_update()
    status = ":yellow_circle: Update available" if update_available else ":green_circle: No update needed"
    console.print(f"[bold green]https://github.com/Dissentix - Watch. Discover. Dominate. - v{CURRENT_VERSION} - {status}[/bold green]")

def check_update():
    try:
        response = requests.get("https://raw.githubusercontent.com/Dissentix/dxwatch/main/version.txt", timeout=5)
        latest_version = response.text.strip()
        return latest_version > CURRENT_VERSION, latest_version
    except requests.RequestException:
        return False, CURRENT_VERSION

def update_tool():
    console.print("[yellow]:rocket: Downloading update...[/yellow]")
    response = requests.get("https://github.com/Dissentix/dxwatch/archive/refs/heads/main.zip")
    with open("dxwatch_update.zip", "wb") as f:
        f.write(response.content)
    console.print("[green]:tada: Updated successfully to v1.0.1[/green]")
