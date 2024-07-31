import psutil
import argparse
import logging
import time
import threading
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

def parse_arguments():
    parser = argparse.ArgumentParser(description="Windows System Utility")
    parser.add_argument('--cpu', choices=['overall', 'core'], help="Display CPU usage (overall/core)")
    parser.add_argument('--mem', choices=['percentage', 'free'], help="Display memory usage (percentage/free)")
    parser.add_argument('--disk', choices=['percentage', 'free'], help="Display disk space usage (percentage/free)")
    parser.add_argument('--kill', type=int, help="Kill process with given process ID")
    parser.add_argument('--alert', action='store_true', help="Enable alert system for high CPU/memory usage")
    parser.add_argument('--list', action='store_true', help="List running processes")
    return parser.parse_args()

def get_cpu_usage(option):
    if option == 'overall':
        return f"Overall CPU Usage: {psutil.cpu_percent(interval=1)}%"
    elif option == 'core':
        core_usage = psutil.cpu_percent(interval=1, percpu=True)
        return "\n".join([f"Core {i} CPU Usage: {percentage}%" for i, percentage in enumerate(core_usage)])
    else:
        return f"Overall CPU Usage: {psutil.cpu_percent(interval=1)}%"

def get_memory_usage(option):
    mem = psutil.virtual_memory()
    if option == 'percentage':
        return f"Memory Usage: {mem.percent}%"
    elif option == 'free':
        return f"Memory Free: {mem.available / (1024 ** 3):.2f} GB"
    else:
        return f"Memory Usage: {mem.percent}%"

def get_disk_usage(option):
    disk_usage = []
    for partition in psutil.disk_partitions():
        usage = psutil.disk_usage(partition.mountpoint)
        if option == 'percentage':
            disk_usage.append(f"Partition {partition.device} Used: {usage.percent}%")
        elif option == 'free':
            disk_usage.append(f"Partition {partition.device} Free: {usage.free / (1024 ** 3):.2f} GB / {usage.total / (1024 ** 3):.2f} GB")
        else:
            disk_usage.append(f"Partition {partition.device} Used: {usage.percent}%")
    return "\n".join(disk_usage)

def list_processes():
    table = Table(title="Running Processes")
    table.add_column("PID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    for proc in psutil.process_iter(['pid', 'name']):
        table.add_row(str(proc.info['pid']), proc.info['name'])
    console = Console()
    console.print(table)

def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        print(f"Process {pid} terminated.")
    except Exception as e:
        print(f"Failed to terminate process {pid}: {e}")

logging.basicConfig(filename='system.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_event(event):
    logging.info(event)

def alert_system():
    console = Console()
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        if cpu > 80:
            log_event(f"High CPU usage detected: {cpu}%")
            console.print(f"[red]Alert: High CPU usage detected: {cpu}%[/red]")
        if mem > 80:
            log_event(f"High memory usage detected: {mem}%")
            console.print(f"[red]Alert: High memory usage detected: {mem}%[/red]")
        time.sleep(5)

def main():
    args = parse_arguments()
    console = Console()

    if args.kill:
        try:
            kill_process(args.kill)
            log_event(f"Process {args.kill} terminated")
        except Exception as e:
            console.print(f"[red]Error terminating process {args.kill}: {e}[/red]")

    elif args.alert:
        console.print("[yellow]Alert system enabled. Monitoring high CPU and memory usage.[/yellow]")
        alert_thread = threading.Thread(target=alert_system)
        alert_thread.start()

    elif args.list:
        list_processes()

    else:
        # Set default values if no specific flags are provided
        if not any([args.cpu, args.mem, args.disk]):
            args.cpu = 'overall'
            args.mem = 'percentage'
            args.disk = 'percentage'

        with Live(console=console, refresh_per_second=0.5) as live:
            try:
                while True:
                    display_text = "[bold]System Resource Monitor[/bold]\n\n"
                    if args.cpu:
                        display_text += f"{get_cpu_usage(args.cpu)}\n\n"
                    if args.mem:
                        display_text += f"{get_memory_usage(args.mem)}\n\n"
                    if args.disk:
                        display_text += f"{get_disk_usage(args.disk)}\n\n"
                    
                    panel = Panel.fit(display_text, title="System Monitor")
                    live.update(panel)
                    time.sleep(2)
            except KeyboardInterrupt:
                console.print("[yellow]Real-time monitoring stopped.[/yellow]")

if __name__ == "__main__":
    main()
