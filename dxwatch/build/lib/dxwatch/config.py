import yaml
import os
from rich.console import Console

console = Console()
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.dxwatch/dxwatch_config.yaml")

def load_config():
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        return {"domains": [], "output_path": "./output", "tools": ["subfinder", "crtsh", "abuseipdb"], "limit": None, "discord_webhook": ""}
    with open(DEFAULT_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(config):
    os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
    with open(DEFAULT_CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f)

def get_config(args):
    config = load_config()
    if "--domains" in args or "-d" in args:
        config["domains"] = args[args.index("--domains") + 1] if "--domains" in args else args[args.index("-d") + 1]
        config["domains"] = config["domains"].split(",")
    if "--output-dir" in args or "-o" in args:
        config["output_path"] = args[args.index("--output-dir") + 1] if "--output-dir" in args else args[args.index("-o") + 1]
    if "--tools" in args or "-t" in args:
        config["tools"] = args[args.index("--tools") + 1] if "--tools" in args else args[args.index("-t") + 1]
        config["tools"] = config["tools"].split(",")
    if "--limit" in args or "-l" in args:
        config["limit"] = int(args[args.index("--limit") + 1] if "--limit" in args else args[args.index("-l") + 1])
    if "--discord-webhook" in args:
        config["discord_webhook"] = args[args.index("--discord-webhook") + 1]
    if "--resolver-path" in args or "-r" in args:
        config["resolver_path"] = args[args.index("--resolver-path") + 1] if "--resolver-path" in args else args[args.index("-r") + 1]
    return config

def prompt_config(config):
    if not config["domains"]:
        config["domains"] = input("[bold green]:globe_with_meridians: Enter domains (required, comma-separated):[/bold green] ").split(",")
    if not config["output_path"]:
        config["output_path"] = input("[bold green]:file_folder: Enter output directory (required):[/bold green] ")
    config["tools"] = input(f"[bold green]:hammer: Enter tools (optional, default: {','.join(config['tools'])}):[/bold green] ") or config["tools"]
    if isinstance(config["tools"], str):
        config["tools"] = config["tools"].split(",")
    limit = input("[bold green]:scissors: Enter limit (optional):[/bold green] ")
    config["limit"] = int(limit) if limit else None
    config["discord_webhook"] = input("[bold green]:speech_balloon: Enter Discord webhook (optional):[/bold green] ") or config["discord_webhook"]
    resolver_path = input("[bold green]:gear: Enter resolver path (optional, default: bundled resolvers.txt):[/bold green] ")
    config["resolver_path"] = resolver_path if resolver_path else config.get("resolver_path")
    console.print("\n[blue]:eyes: Current settings:[/blue]")
    console.print(f"Domains: {', '.join(config['domains'])}")
    console.print(f"Output Directory: {config['output_path']}")
    console.print(f"Tools: {', '.join(config['tools'])}")
    console.print(f"Limit: {config['limit'] if config['limit'] else 'None'}")
    console.print(f"Resolver Path: {config.get('resolver_path', 'bundled resolvers.txt')}")
    console.print(f"Discord Webhook: {config['discord_webhook'] if config['discord_webhook'] else 'None'}")
    return input("[blue]:question: Proceed? (y/n):[/blue] ").lower() == "y"
