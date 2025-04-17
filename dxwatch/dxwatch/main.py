import sys
from dxwatch.display import print_logo, check_update, update_tool
from dxwatch.config import get_config, prompt_config, save_config
from dxwatch.recon import run_recon, show_stats, show_status, reset_sent
from rich.console import Console

console = Console()

def print_help():
    console.print("[bold yellow]:book: dxwatch - Help[/bold yellow]")
    console.print("[cyan]Usage: dxwatch [mode] [options][/cyan]")
    console.print("Modes:")
    console.print("  run          Run in manual mode")
    console.print("  auto         Run in automatic mode")
    console.print("\nOptions:")
    console.print("  -h, --help                Show this help message")
    console.print("  -d, --domains DOMAINS     Set domains (comma-separated)")
    console.print("  -o, --output-dir PATH     Set output directory")
    console.print("  -t, --tools TOOLS         Set subdomain tools (comma-separated)")
    console.print("  -l, --limit NUM           Limit number of subdomains")
    console.print("  -r, --resolver-path PATH  Set custom resolver file path")
    console.print("  --discord-webhook URL     Set Discord webhook URL")
    console.print("  --stats                   Show database stats")
    console.print("  --show-status CODE        Show domains with specific status")
    console.print("  --send-status CODE        Send domains with specific status to Discord")
    console.print("  --send-discord            Send new domains to Discord")
    console.print("  --reset-sent              Reset sent domains database")
    console.print("  --update-config           Update config without running")
    console.print("  --changes                 Show changes since last run")
    console.print("  --update                  Update dxwatch to latest version")
    console.print("\n[green]:bulb: Example: dxwatch run -d example.com -o /path -l 1000[/green]")

def main():
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print_logo()
        print_help()
        sys.exit(0)
    
    print_logo()
    if "--update" in args:
        if check_update()[0]:
            update_tool()
            sys.exit(0)
        else:
            console.print("[green]:check_mark_button: Already up to date[/green]")
            sys.exit(0)
    
    config = get_config(args)
    output_path = config["output_path"]
    
    if "--update-config" in args:
        save_config(config)
        console.print("[green]:floppy_disk: Config updated[/green]")
        sys.exit(0)
    
    if "--stats" in args:
        show_stats(output_path)
        sys.exit(0)
    
    if "--show-status" in args:
        status_code = int(args[args.index("--show-status") + 1])
        show_status(output_path, status_code)
        sys.exit(0)
    
    if "--reset-sent" in args:
        reset_sent(output_path)
        sys.exit(0)
    
    if "run" in args:
        if not config["domains"] or not config["output_path"]:
            if not prompt_config(config):
                save_config(config)
                console.print("[yellow]:door: Config saved, exiting[/yellow]")
                sys.exit(0)
        results = run_recon(config)
        if results is None:
            sys.exit(1)
    save_config(config)

if __name__ == "__main__":
    main()
