import subprocess
import os
import sqlite3
import time
import pytz
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from discord_webhook import DiscordWebhook

console = Console()

def init_databases(output_path):
    recon_db = os.path.join(output_path, "recon.db")
    sent_db = os.path.join(output_path, "sent.db")
    
    conn = sqlite3.connect(recon_db)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS domains (
            domain TEXT PRIMARY KEY,
            status INTEGER,
            title TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect(sent_db)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS sent_domains (domain TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def run_command(command, output_file=None):
    try:
        if output_file:
            with open(output_file, "w") as f:
                subprocess.run(command, shell=True, stdout=f, stderr=subprocess.PIPE, text=True)
        else:
            return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
    except subprocess.SubprocessError as e:
        console.print(f"[red]:exclamation: Command failed: {command} - {e}[/red]")
        return None

def get_current_time_in_iran():
    iran_tz = pytz.timezone('Asia/Tehran')
    return datetime.now(iran_tz).strftime('%Y-%m-%d %H:%M:%S')

def send_discord_message(webhook_url, message):
    retries = 0
    while retries < 5:
        webhook = DiscordWebhook(url=webhook_url, content=message)
        response = webhook.execute()
        if response.status_code == 200:
            return True
        elif response.status_code == 429:
            retry_after = float(response.headers.get('Retry-After', 1))
            console.print(f"[yellow]:warning: Rate limited, retrying in {retry_after} seconds[/yellow]")
            time.sleep(retry_after)
            retries += 1
        else:
            console.print(f"[red]:exclamation: Failed to send message: HTTP {response.status_code}[/red]")
            return False
    return False

def discover_subdomains(config):
    output_path = config["output_path"]
    domains = config["domains"]
    tools = config["tools"]
    limit = config["limit"]
    
    os.makedirs(output_path, exist_ok=True)
    init_databases(output_path)
    all_subdomains = set()
    
    for domain in domains:
        domain_safe = domain.replace(".", "_")
        
        with Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            for tool in tools:
                task = progress.add_task(f":mag: Discovering subdomains with {tool} for {domain}...", total=100)
                
                if tool == "subfinder":
                    subfinder_file = os.path.join(output_path, f"{domain_safe}.subfinder")
                    cmd = f"subfinder -d {domain} -t 50 -all | anew {subfinder_file}"
                    run_command(cmd)
                    progress.update(task, advance=100)
                    if os.path.exists(subfinder_file):
                        with open(subfinder_file, "r") as f:
                            all_subdomains.update(line.strip() for line in f if line.strip())
                
                elif tool == "crtsh":
                    crtsh_file = os.path.join(output_path, f"{domain_safe}.crtsh")
                    query = f"SELECT ci.NAME_VALUE FROM certificate_and_identities ci WHERE plainto_tsquery('certwatch', '{domain}') @@ identities(ci.CERTIFICATE)"
                    cmd = f"echo \"{query}\" | psql -t -h crt.sh -p 5432 -U guest certwatch | sed 's/ //g' | grep -E \".*\\.{domain}\" | sed 's/*\\.//g' | tr '[:upper:]' '[:lower:]' | sort -u | anew {crtsh_file}"
                    run_command(cmd)
                    progress.update(task, advance=100)
                    if os.path.exists(crtsh_file):
                        with open(crtsh_file, "r") as f:
                            all_subdomains.update(line.strip() for line in f if line.strip())
                
                elif tool == "abuseipdb":
                    abuseipdb_file = os.path.join(output_path, f"{domain_safe}.abuseipdb")
                    cmd = f"""curl -s "https://www.abuseipdb.com/whois/{domain}" -H "user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36" | grep -E '<li>\w.*</li>' | sed -E 's/<\\/?li>//g' | sed "s|$|\\.{domain}|" | anew {abuseipdb_file}"""
                    run_command(cmd)
                    progress.update(task, advance=100)
                    if os.path.exists(abuseipdb_file):
                        with open(abuseipdb_file, "r") as f:
                            all_subdomains.update(line.strip() for line in f if line.strip())
                else:
                    console.print(f"[red]:exclamation: Unknown tool: {tool}[/red]")
        
        subs_finally_file = os.path.join(output_path, f"{domain_safe}.subs.finally")
        with open(subs_finally_file, "w") as f:
            for subdomain in all_subdomains:
                f.write(f"{subdomain}\n")
        console.print(f":sparkles: Boom! Found {len(all_subdomains)} subdomains for {domain}, saved to {subs_finally_file}")

        if limit and len(all_subdomains) > limit:
            console.print(f"[yellow]:bulb: Whoa! Found {len(all_subdomains)} subdomains for {domain}[/yellow]")
            choice = input(f"[green]Limit is set to {limit}. Proceed with all (y/n) or apply limit (l)?[/green] ")
            if choice.lower() == "l":
                limited_subdomains = list(all_subdomains)[:limit]
                with open(subs_finally_file, "w") as f:
                    for subdomain in limited_subdomains:
                        f.write(f"{subdomain}\n")
                console.print(f":scissors: Trimmed to {limit} subdomains for {domain}")
                return limited_subdomains
            elif choice.lower() != "y":
                console.print("[yellow]:door: Exiting recon for {domain}[/yellow]")
                return None
    
    return all_subdomains

def process_dnsx(config, subdomains):
    output_path = config["output_path"]
    domains = config["domains"]
    domain_safe = domains[0].replace(".", "_")
    
    subs_finally_file = os.path.join(output_path, f"{domain_safe}.subs.finally")
    dnsx_file = os.path.join(output_path, f"{domain_safe}.live-sub.dnsx")
    
    resolver_path = config.get("resolver_path", os.path.join(os.path.dirname(__file__), "resolvers.txt"))
    cmd = f"dnsx -l {subs_finally_file} -t 10 -r {resolver_path} -silent -a | anew {dnsx_file}"
    
    with Progress(
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(f":zap: Resolving subdomains with dnsx for {domains[0]}...", total=100)
        run_command(cmd)
        progress.update(task, advance=100)
    
    live_subdomains = set()
    if os.path.exists(dnsx_file):
        with open(dnsx_file, "r") as f:
            live_subdomains.update(line.strip() for line in f if line.strip())
    console.print(f":rocket: Sweet! Resolved {len(live_subdomains)} live subdomains, saved to {dnsx_file}")
    return live_subdomains

def process_httpx(config, live_subdomains):
    output_path = config["output_path"]
    domains = config["domains"]
    domain_safe = domains[0].replace(".", "_")
    
    dnsx_file = os.path.join(output_path, f"{domain_safe}.live-sub.dnsx")
    httpx_file = os.path.join(output_path, f"{domain_safe}.httpx")
    recon_db = os.path.join(output_path, "recon.db")
    
    with Progress(
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(f":fire: Probing live subdomains with httpx for {domains[0]}...", total=len(live_subdomains))
        with open(dnsx_file, "r") as infile, open(httpx_file, "w") as outfile:
            for line in infile:
                subdomain = line.strip()
                if subdomain:
                    cmd = f"echo {subdomain} | httpx -silent -follow-host-redirects -title -status-code -cdn -tech-detect -H \"User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0\" -H \"Referer: {subdomain}\""
                    result = run_command(cmd)
                    if result:
                        outfile.write(f"{result}\n")
                    progress.update(task, advance=1)
    
    httpx_results = []
    if os.path.exists(httpx_file):
        with open(httpx_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    domain = parts[0]
                    status = int(parts[1].strip("[]"))
                    title = " ".join(parts[2:]) if len(parts) > 2 else ""
                    httpx_results.append((domain, status, title))
    
    conn = sqlite3.connect(recon_db)
    c = conn.cursor()
    for domain, status, title in httpx_results:
        c.execute("INSERT OR REPLACE INTO domains (domain, status, title) VALUES (?, ?, ?)", (domain, status, title))
    conn.commit()
    conn.close()
    
    console.print(f":tada: Done! Probed {len(httpx_results)} domains with httpx, saved to {httpx_file} and recon.db")
    return httpx_results

def send_to_discord(config, httpx_results):
    webhook_url = config["discord_webhook"]
    if not webhook_url:
        console.print("[yellow]:warning: No Discord webhook provided, skipping[/yellow]")
        return
    
    output_path = config["output_path"]
    domains = config["domains"]
    recon_db = os.path.join(output_path, "recon.db")
    sent_db = os.path.join(output_path, "sent.db")
    
    current_time = get_current_time_in_iran()
    start_message = f":watch: Current time in Iran: {current_time} - Starting recon for {', '.join(domains)}"
    send_discord_message(webhook_url, start_message)
    
    total_urls_sent = 0
    status_counts = {}
    
    for domain in domains:
        domain_safe = domain.replace(".", "_")
        domain_results = [(d, s, t) for d, s, t in httpx_results if d.endswith(domain)]
        
        if domain_results:
            start_domain_message = f":incoming_envelope: Started sending URLs for {domain}"
            send_discord_message(webhook_url, start_domain_message)
            
            conn = sqlite3.connect(sent_db)
            c = conn.cursor()
            for subdomain, status, title in domain_results:
                c.execute("SELECT domain FROM sent_domains WHERE domain = ?", (subdomain,))
                if not c.fetchone():
                    message = f"```URL: {subdomain}\n" \
                              f"Status: {status}\n" \
                              f"Title: {title}\n```" \
                              f":floppy_disk: (Fresh Asset) has been added to recon database"
                    if send_discord_message(webhook_url, message):
                        c.execute("INSERT INTO sent_domains (domain) VALUES (?)", (subdomain,))
                        total_urls_sent += 1
                        status_counts[status] = status_counts.get(status, 0) + 1
                        time.sleep(3)
            conn.commit()
            conn.close()
            
            status_summary = "\n".join([f"Status {code}: {count}" for code, count in status_counts.items()])
            end_domain_message = f":crossed_swords: Finished sending URLs for {domain}\n" \
                                 f"Total URLs sent: {len(domain_results)}\n" \
                                 f"{status_summary}"
            send_discord_message(webhook_url, end_domain_message)
    
    final_message = f"All new URLs have been successfully sent to Discord. Total URLs sent: {total_urls_sent}"
    send_discord_message(webhook_url, final_message)

def run_recon(config):
    subdomains = discover_subdomains(config)
    if subdomains is None:
        return None
    
    live_subdomains = process_dnsx(config, subdomains)
    if not live_subdomains:
        return None
    
    httpx_results = process_httpx(config, live_subdomains)
    if "--send-discord" in sys.argv:
        send_to_discord(config, httpx_results)
    return httpx_results

def show_stats(output_path):
    recon_db = os.path.join(output_path, "recon.db")
    conn = sqlite3.connect(recon_db)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM domains")
    total = c.fetchone()[0]
    c.execute("SELECT status, COUNT(*) FROM domains GROUP BY status")
    stats = c.fetchall()
    conn.close()
    
    console.print(f":bar_chart: Total domains: {total}")
    for status, count in stats:
        console.print(f":bar_chart: Status {status}: {count}")

def show_status(output_path, status_code):
    recon_db = os.path.join(output_path, "recon.db")
    conn = sqlite3.connect(recon_db)
    c = conn.cursor()
    c.execute("SELECT domain, status, title FROM domains WHERE status = ?", (status_code,))
    results = c.fetchall()
    conn.close()
    
    for domain, status, title in results:
        console.print(f":green_circle: {domain} [{status}] {title}")

def reset_sent(output_path):
    sent_db = os.path.join(output_path, "sent.db")
    conn = sqlite3.connect(sent_db)
    c = conn.cursor()
    c.execute("DELETE FROM sent_domains")
    conn.commit()
    conn.close()
    console.print("[green]:broom: Sent domains cleared![/green]")
